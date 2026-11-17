"""인스타그램 공식 API(Graph API) 연결.

여기서 쓰는 것은 Business Discovery 하나다. 계정명을 주면 그 계정의
소개글, 웹사이트 링크, 팔로워 수를 돌려준다. 상대가 프로페셔널
(비즈니스·크리에이터) 계정일 때만 조회된다.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HOST = "https://graph.facebook.com"
DEFAULT_VERSION = "v27.0"
USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")
PROFILE_FIELDS = "username,biography,website,followers_count,media_count"


class GraphError(Exception):
    """API가 돌려준 오류."""

    def __init__(self, message, code=None, subcode=None, transient=False, http_status=None):
        super().__init__(message)
        self.message = str(message)
        self.code = code
        self.subcode = subcode
        self.transient = transient
        self.http_status = http_status

    @property
    def kind(self) -> str:
        """오류 종류. 종류에 따라 건너뛸지, 기다릴지, 멈출지가 달라진다."""
        code = self.code
        if code == 110 or self.subcode == 2207013 or "cannot be found" in self.message:
            return "not_found"      # 없는 계정이거나 개인 계정 → 이 계정만 건너뜀
        if code == 190:
            return "auth"           # 토큰 만료·오류 → 멈춤
        if code in (4, 17, 32, 613) or (isinstance(code, int) and 80000 <= code < 80100):
            return "rate_limit"     # 호출 한도 → 기다렸다 다시
        if code in (10, 200) or (isinstance(code, int) and 200 < code < 300):
            return "permission"     # 권한 부족 → 멈춤
        if self.transient or code in (1, 2) or (self.http_status or 0) >= 500:
            return "transient"      # 일시 오류 → 잠깐 기다렸다 다시
        return "other"


def http_transport(url: str, timeout: float = 20.0) -> dict:
    """실제 인터넷으로 API를 호출한다."""
    request = urllib.request.Request(url, headers={"User-Agent": "seeding-automation"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            err = json.loads(body).get("error") or {}
        except ValueError:
            err = {}
        raise GraphError(
            err.get("error_user_msg") or err.get("message") or f"HTTP {e.code}",
            code=err.get("code"),
            subcode=err.get("error_subcode"),
            transient=bool(err.get("is_transient")),
            http_status=e.code,
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise GraphError(f"네트워크 오류: {getattr(e, 'reason', e)}", transient=True) from None


class SampleTransport:
    """실제 API 대신 sample/mock_profiles.json의 가상 계정을 돌려준다.

    토큰 없이 전체 흐름을 돌려 볼 때 쓴다. 요청 주소를 실제와 똑같이 해석하므로
    주소를 만드는 코드도 함께 검증된다.
    """

    def __init__(self, path: Path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.profiles = {k.lower(): v for k, v in data["profiles"].items()}

    def __call__(self, url: str, timeout: float = 20.0) -> dict:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        fields = query.get("fields", [""])[0]
        m = re.search(r"business_discovery\.username\(([^)]+)\)", fields)
        if not m:
            raise GraphError("샘플 모드는 business_discovery 조회만 지원합니다.")
        profile = self.profiles.get(m.group(1).lower())
        if profile is None or profile.get("_not_found"):
            raise GraphError("Invalid user id", code=110, subcode=2207013, http_status=400)
        payload = {k: v for k, v in profile.items() if not k.startswith("_")}
        return {"business_discovery": payload, "id": "0"}


class InstagramAPI:
    def __init__(
        self,
        access_token: str,
        ig_user_id: str = "",
        *,
        version: str = DEFAULT_VERSION,
        transport=http_transport,
        min_interval: float = 1.0,
        max_retries: int = 3,
        sleep=time.sleep,
        on_wait=None,
    ):
        self.access_token = access_token
        self.ig_user_id = ig_user_id
        self.version = version or DEFAULT_VERSION
        self.transport = transport
        self.min_interval = min_interval
        self.max_retries = max_retries
        self.sleep = sleep
        self.on_wait = on_wait
        self._last_call = None

    def _throttle(self) -> None:
        """호출 사이에 간격을 둔다."""
        if self._last_call is not None and self.min_interval > 0:
            remaining = self.min_interval - (time.monotonic() - self._last_call)
            if remaining > 0:
                self.sleep(remaining)
        self._last_call = time.monotonic()

    def _get(self, path: str, params: dict) -> dict:
        query = urllib.parse.urlencode({**params, "access_token": self.access_token})
        url = f"{HOST}/{self.version}/{path}?{query}"
        attempt = 0
        while True:
            self._throttle()
            try:
                return self.transport(url)
            except GraphError as e:
                if e.kind not in ("rate_limit", "transient") or attempt >= self.max_retries:
                    raise
                wait = (60 if e.kind == "rate_limit" else 2) * (2 ** attempt)
                if self.on_wait:
                    self.on_wait(e.kind, wait)
                self.sleep(wait)
                attempt += 1

    def business_discovery(self, username: str) -> dict:
        """계정명으로 프로필 정보를 가져온다."""
        if not USERNAME_RE.match(username):
            raise ValueError(f"계정명 형식이 아닙니다: {username!r}")
        if not self.ig_user_id:
            raise ValueError("IG_USER_ID가 없습니다. check_setup.py를 먼저 실행하세요.")
        fields = f"business_discovery.username({username}){{{PROFILE_FIELDS}}}"
        data = self._get(self.ig_user_id, {"fields": fields})
        return data.get("business_discovery") or {}

    def my_instagram_accounts(self) -> list[dict]:
        """이 토큰으로 접근할 수 있는 인스타그램 프로페셔널 계정 목록."""
        data = self._get(
            "me/accounts",
            {"fields": "name,instagram_business_account{id,username}", "limit": 100},
        )
        accounts = []
        for page in data.get("data", []):
            ig = page.get("instagram_business_account")
            if ig:
                accounts.append(
                    {
                        "page": page.get("name", ""),
                        "ig_user_id": ig.get("id", ""),
                        "username": ig.get("username", ""),
                    }
                )
        return accounts
