"""소개글 같은 짧은 글에서 메일 주소를 찾는다.

AI를 쓰지 않고 규칙만으로 찾는다. 외부 라이브러리가 필요 없다.

- 표준 표기:  abc@naver.com
- 변형 표기:  abc 골뱅이 naver 닷컴 / abc(at)gmail.com / abc @ naver . com
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlparse

# "abc at gmail.com"처럼 괄호 없이 at을 쓴 경우, 뒤에 이 도메인이 올 때만 메일로 본다.
# (영어 문장의 "at"과 구분하기 위해서)
MAIL_DOMAINS = (
    "gmail", "naver", "daum", "hanmail", "kakao", "nate",
    "outlook", "hotmail", "icloud", "yahoo",
)

COMMON_TLDS = {
    "com", "net", "org", "kr", "io", "me", "co", "ai", "biz", "info", "jp", "cn",
    "us", "uk", "de", "fr", "ca", "au", "eu", "asia", "shop", "store", "xyz", "app",
    "dev", "tv", "cc", "studio", "design", "media", "agency", "company", "world",
    "life", "live", "page", "site", "online",
}

# "name@2x.png" 같은 파일 이름은 메일이 아니다.
NOT_TLDS = {"png", "jpg", "jpeg", "gif", "webp", "svg", "heic", "mp4", "mov"}

# 소개글의 링크가 "링크 모음 페이지"인지 알아보기 위한 목록
LINK_HUB_HOSTS = (
    "linktr.ee", "litt.ly", "inpock.co.kr", "inpk.link", "instabio.cc", "beacons.ai",
    "lnk.bio", "linkin.bio", "bio.site", "taplink.cc", "msha.ke", "campsite.bio",
    "carrd.co", "linkr.bio",
)

_EMAIL = re.compile(
    r"(?<![A-Za-z0-9._%+\-])"
    r"([A-Za-z0-9][A-Za-z0-9._%+\-]{0,63})"
    r"@"
    r"((?:[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,24})"
)

_MAIL_DOMAIN_ALT = "|".join(MAIL_DOMAINS)
_OPEN = r"[\(\[\{<]"
_CLOSE = r"[\)\]\}>]"


@dataclass(frozen=True)
class FoundEmail:
    email: str
    how: str   # "표준" 또는 "변형 표기"
    sure: bool  # False면 사람이 한 번 봐야 한다 (변형 표기이거나 낯선 도메인 끝자리)


def _fix_tld(domain: str) -> tuple[str, bool]:
    """도메인 끝에 붙은 군더더기를 떼고, 끝자리가 흔한 것인지 알려 준다.

    "naver.comDM" → "naver.com" (소문자에서 대문자로 바뀌는 곳에서 자른다)
    """
    labels = domain.split(".")
    tld = labels[-1]
    m = re.match(r"^([a-z]{2,})(?=[A-Z])", tld)
    if m and m.group(1) in COMMON_TLDS:
        tld = m.group(1)
    labels[-1] = tld
    return ".".join(labels).lower(), tld.lower() in COMMON_TLDS


def _find_standard(text: str) -> list[tuple[str, bool, tuple[int, int]]]:
    out = []
    for m in _EMAIL.finditer(text):
        domain, known_tld = _fix_tld(m.group(2))
        if domain.rsplit(".", 1)[-1] in NOT_TLDS:
            continue
        out.append((f"{m.group(1).lower()}@{domain}", known_tld, m.span()))
    return out


def _deobfuscate(t: str) -> str:
    """변형 표기를 표준 표기로 바꾼다. 계정 멘션(@handle)을 메일로 오인하지 않도록 조건을 좁혔다."""
    I = re.IGNORECASE
    # (at) [at] {골뱅이} → @
    t = re.sub(rf"\s*{_OPEN}\s*(?:at|골뱅이|앳|엣)\s*{_CLOSE}\s*", "@", t, flags=I)
    # 골뱅이 → @
    t = re.sub(r"\s*골뱅이\s*", "@", t)
    # "abc at gmail" → 뒤가 메일 도메인일 때만
    t = re.sub(rf"(?<=[A-Za-z0-9])\s+at\s+(?=(?:{_MAIL_DOMAIN_ALT})\b)", "@", t, flags=I)
    # (dot) [닷] (점) → .
    t = re.sub(rf"\s*{_OPEN}\s*(?:dot|닷|점)\s*{_CLOSE}\s*", ".", t, flags=I)
    # "abc @ naver.com", "abc@ naver.com"  (멘션은 @ 뒤에 공백이 없으므로 구분된다)
    t = re.sub(r"(?<=[A-Za-z0-9])\s*@\s+(?=[A-Za-z0-9])", "@", t)
    # "abc @naver.com" → 뒤가 메일 도메인일 때만 (멘션과 구분)
    t = re.sub(rf"(?<=[A-Za-z0-9])\s+@(?=(?:{_MAIL_DOMAIN_ALT})\b)", "@", t, flags=I)
    # "@naver 닷컴", "@naver 닷넷"
    t = re.sub(r"(@[A-Za-z0-9\-]+)\s*닷\s*컴", r"\1.com", t)
    t = re.sub(r"(@[A-Za-z0-9\-]+)\s*닷\s*넷", r"\1.net", t)
    # "@naver dot com", "@naver 닷 com", "@naver 점 com"
    t = re.sub(r"(@[A-Za-z0-9\-]+)\s+dot\s+(?=[A-Za-z]{2,})", r"\1.", t, flags=I)
    t = re.sub(r"(@[A-Za-z0-9\-]+)\s*[닷점]\s*(?=[A-Za-z]{2,})", r"\1.", t)
    # "@naver . com", "@naver. com", "@naver .com"
    t = re.sub(r"(@[A-Za-z0-9\-]+)\s+\.\s*(?=[A-Za-z]{2,})", r"\1.", t)
    t = re.sub(r"(@[A-Za-z0-9\-]+)\.\s+(?=[A-Za-z]{2,})", r"\1.", t)
    return t


def extract_emails(text: str | None) -> list[FoundEmail]:
    """글에서 메일 주소를 모두 찾아 돌려준다. 표준 표기가 먼저 온다."""
    if not text:
        return []
    text = unicodedata.normalize("NFKC", text)  # 전각 문자(＠ 등)를 보통 문자로

    found: list[FoundEmail] = []
    seen: set[str] = set()

    standard = _find_standard(text)
    for email, known_tld, _ in standard:
        if email not in seen:
            seen.add(email)
            found.append(FoundEmail(email, "표준", known_tld))

    # 이미 찾은 부분은 가리고, 남은 글에서 변형 표기를 찾는다.
    masked = list(text)
    for _, _, (start, end) in standard:
        masked[start:end] = " " * (end - start)
    for email, _, _ in _find_standard(_deobfuscate("".join(masked))):
        if email not in seen:
            seen.add(email)
            found.append(FoundEmail(email, "변형 표기", False))

    return found


def prefers_dm(text: str | None) -> bool:
    """소개글에 "문의는 DM" 같은 말이 있는지."""
    if not text:
        return False
    return bool(re.search(r"\bDM\b|디엠|다이렉트", text, flags=re.IGNORECASE))


def is_link_hub(url: str | None) -> bool:
    """링크트리 같은 "링크 모음 페이지"인지. 여기에 메일이 적혀 있는 경우가 있다."""
    if not url:
        return False
    host = (urlparse(url if "//" in url else "https://" + url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in LINK_HUB_HOSTS)
