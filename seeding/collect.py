"""A. 메일 수집기 — 계정 목록을 받아 계정마다 메일 주소를 찾는다."""
from __future__ import annotations

import csv
import os
import re
from datetime import datetime
from pathlib import Path

from .email_extract import extract_emails, is_link_hub, prefers_dm
from .ig_api import USERNAME_RE, GraphError

COLUMNS = [
    "계정", "프로필 링크", "조회 결과", "메일", "메일 출처", "확인 필요",
    "다음 행동", "비고", "팔로워", "게시물 수", "소개글", "웹사이트", "조회 시각",
]
MAIL_COLUMNS = ["계정", "메일", "확인 필요", "팔로워", "프로필 링크"]

DONE = ("조회됨", "조회 불가")  # 다시 실행해도 건너뛰는 상태. "오류"는 다시 시도한다.
STOP_KINDS = ("auth", "permission", "rate_limit")

_HEADER_NAMES = ("계정", "username", "account", "아이디", "인스타", "instagram", "id")
_RESERVED = {"p", "reel", "reels", "explore", "stories", "tv", "accounts", "direct"}


class Stopped(Exception):
    """더 진행할 수 없어 멈춘 경우. 그때까지의 결과는 저장되어 있다."""


def normalize_username(raw: str) -> str | None:
    """"@abc", "https://www.instagram.com/abc/" 같은 입력을 계정명 "abc"로 바꾼다."""
    s = (raw or "").strip()
    if not s:
        return None
    m = re.search(r"instagram\.com/([A-Za-z0-9._]+)", s)
    if m:
        s = m.group(1)
    s = s.lstrip("@").strip().strip("/").lower()
    if s in _RESERVED or not USERNAME_RE.match(s):
        return None
    return s


def read_text(path: Path) -> str:
    """엑셀에서 저장한 CSV(cp949)와 UTF-8을 모두 읽는다."""
    data = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def read_usernames(path: Path) -> tuple[list[str], list[str]]:
    """계정 목록 파일을 읽는다. (계정명 목록, 알아볼 수 없어 건너뛴 값 목록)을 돌려준다.

    CSV의 "계정" 또는 "username" 열을 쓰고, 그런 열이 없으면 첫 번째 열을 쓴다.
    한 줄에 하나씩 적은 텍스트 파일도 된다.
    """
    rows = [r for r in csv.reader(read_text(path).splitlines()) if r]
    column, start = 0, 0
    if rows:
        header = [c.strip().lower() for c in rows[0]]
        for name in _HEADER_NAMES:
            if name in header:
                column, start = header.index(name), 1
                break
    names: list[str] = []
    skipped: list[str] = []
    seen: set[str] = set()
    for row in rows[start:]:
        raw = row[column].strip() if len(row) > column else ""
        if not raw:
            continue
        username = normalize_username(raw)
        if username is None:
            skipped.append(raw)
        elif username not in seen:
            seen.add(username)
            names.append(username)
    return names, skipped


def lookup(api, username: str) -> dict:
    """계정 하나를 조회해 결과 한 줄을 만든다."""
    row = {c: "" for c in COLUMNS}
    row["계정"] = username
    row["프로필 링크"] = f"https://www.instagram.com/{username}/"
    row["조회 시각"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        profile = api.business_discovery(username)
    except GraphError as e:
        if e.kind in STOP_KINDS:
            raise
        if e.kind == "not_found":
            row["조회 결과"] = "조회 불가"
            row["비고"] = "개인 계정이거나 없는 계정 (API는 프로페셔널 계정만 조회됨)"
        else:
            row["조회 결과"] = "오류"
            row["비고"] = f"다시 실행하면 재시도합니다: {e.message}"
        row["다음 행동"] = "수동 확인"
        return row

    bio = profile.get("biography") or ""
    site = profile.get("website") or ""
    found = extract_emails(bio)
    source = "소개글"
    if not found and site.lower().startswith("mailto:"):
        found = extract_emails(site)
        source = "웹사이트 칸"

    notes = []
    row["조회 결과"] = "조회됨"
    row["팔로워"] = profile.get("followers_count", "")
    row["게시물 수"] = profile.get("media_count", "")
    row["소개글"] = " / ".join(line.strip() for line in bio.splitlines() if line.strip())
    row["웹사이트"] = site

    if found:
        row["메일"] = "; ".join(f.email for f in found)
        row["메일 출처"] = source + (" (변형 표기)" if found[0].how != "표준" else "")
        row["다음 행동"] = "메일 발송"
        if not found[0].sure:
            row["확인 필요"] = "예"
            notes.append("주소가 맞는지 소개글과 한 번 비교해 주세요")
        if len(found) > 1:
            notes.append(f"메일 {len(found)}개")
    else:
        row["다음 행동"] = "DM"
        if is_link_hub(site):
            notes.append("링크 모음 페이지 있음: 눌러 보면 메일이 있을 수 있음")
        if prefers_dm(bio):
            notes.append("소개글에 DM 문의 표시")
    row["비고"] = ", ".join(notes)
    return row


def load_results(path: Path) -> dict[str, dict]:
    """이전에 저장한 결과 파일을 읽는다. 없으면 빈 값."""
    path = Path(path)
    if not path.exists():
        return {}
    rows = csv.DictReader(read_text(path).splitlines())
    return {r["계정"]: {c: r.get(c, "") for c in COLUMNS} for r in rows if r.get("계정")}


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    """엑셀에서 한글이 깨지지 않는 형식으로 저장한다."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    try:
        os.replace(tmp, path)
    except PermissionError:
        tmp.unlink(missing_ok=True)
        raise Stopped(f"{path.name} 파일이 엑셀에 열려 있어 저장할 수 없습니다. 엑셀을 닫고 다시 실행해 주세요.")


def mail_targets_path(out_path: Path) -> Path:
    out_path = Path(out_path)
    return out_path.with_name(out_path.stem + "_mail" + out_path.suffix)


def summarize(rows: list[dict]) -> dict:
    total = len(rows)
    found = sum(1 for r in rows if r["조회 결과"] == "조회됨")
    mail = sum(1 for r in rows if r["다음 행동"] == "메일 발송")
    return {
        "전체": total,
        "조회됨": found,
        "메일 확보": mail,
        "DM 대상": sum(1 for r in rows if r["다음 행동"] == "DM"),
        "수동 확인": sum(1 for r in rows if r["다음 행동"] == "수동 확인"),
        "메일 확보율(조회된 계정 중)": f"{mail / found * 100:.0f}%" if found else "-",
    }


def run(usernames: list[str], api, out_path: Path, *, refresh: bool = False, log=print) -> dict:
    """계정 목록을 차례로 조회해 결과 파일을 만든다.

    중간에 멈춰도 그때까지의 결과는 저장되어 있고, 같은 명령을 다시 실행하면
    이미 조회한 계정은 건너뛰고 이어서 한다.
    """
    out_path = Path(out_path)
    results = {} if refresh else load_results(out_path)
    todo = [u for u in usernames if results.get(u, {}).get("조회 결과") not in DONE]
    if len(todo) < len(usernames):
        log(f"이미 조회한 {len(usernames) - len(todo)}개는 건너뜁니다.")

    def save() -> list[dict]:
        ordered = [results[u] for u in usernames if u in results]
        write_csv(out_path, COLUMNS, ordered)
        write_csv(
            mail_targets_path(out_path),
            MAIL_COLUMNS,
            [r for r in ordered if r["다음 행동"] == "메일 발송"],
        )
        return ordered

    stopped = None
    for i, username in enumerate(todo, 1):
        try:
            row = lookup(api, username)
        except GraphError as e:
            stopped = e
            break
        results[username] = row
        log(f"[{i}/{len(todo)}] {username}: {row['메일'] or row['다음 행동']}")
        if i % 10 == 0:
            save()

    rows = save()
    summary = summarize(rows)
    if stopped is not None:
        reasons = {
            "auth": "액세스 토큰이 만료됐거나 잘못됐습니다. 토큰을 새로 발급해 .env에 넣어 주세요.",
            "permission": "토큰에 필요한 권한이 없습니다. README의 권한 목록을 확인해 주세요.",
            "rate_limit": "API 호출 한도에 걸렸습니다. 한 시간쯤 뒤에 같은 명령을 다시 실행하면 이어서 합니다.",
        }
        raise Stopped(f"{reasons[stopped.kind]} (API 응답: {stopped.message})")
    return summary
