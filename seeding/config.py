"""설정(.env) 읽기와 화면 출력 준비."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
SAMPLE_PROFILES = ROOT / "sample" / "mock_profiles.json"
SAMPLE_ACCOUNTS = ROOT / "sample" / "accounts.csv"

ENV_KEYS = ("IG_ACCESS_TOKEN", "IG_USER_ID", "GRAPH_API_VERSION")


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    """.env 파일을 읽는다. 같은 이름의 환경 변수가 있으면 그쪽이 우선한다."""
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    for key in ENV_KEYS:
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def save_env_value(key: str, value: str, path: Path = ENV_PATH) -> None:
    """.env 파일의 한 줄을 바꾸거나 추가한다."""
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []
    for i, line in enumerate(lines):
        if line.strip().startswith(key + "="):
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def setup_console() -> None:
    """윈도우 명령창에서 이모지 같은 글자 때문에 프로그램이 멈추지 않게 한다."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
