"""A. 메일 수집기 실행 파일.

    python collect_emails.py --sample              샘플 데이터로 돌려 보기 (토큰 필요 없음)
    python collect_emails.py 계정목록.csv           실제 계정 조회
"""
import argparse
import sys
from pathlib import Path

from seeding import collect, config
from seeding.ig_api import InstagramAPI, SampleTransport


def main() -> int:
    config.setup_console()
    parser = argparse.ArgumentParser(description="계정 목록에서 메일 주소를 찾아 CSV로 저장합니다.")
    parser.add_argument("accounts", nargs="?", help="계정 목록 파일 (CSV 또는 한 줄에 하나씩 적은 텍스트)")
    parser.add_argument("--out", default="output/emails.csv", help="결과 파일 (기본: output/emails.csv)")
    parser.add_argument("--sample", action="store_true", help="실제 API 대신 가상의 샘플 데이터로 실행")
    parser.add_argument("--refresh", action="store_true", help="이미 조회한 계정도 다시 조회")
    parser.add_argument("--interval", type=float, default=1.0, help="조회 사이 간격(초). 기본 1초")
    args = parser.parse_args()

    if args.sample:
        accounts = Path(args.accounts) if args.accounts else config.SAMPLE_ACCOUNTS
        out = Path(args.out if args.out != "output/emails.csv" else "output/sample_emails.csv")
        api = InstagramAPI("sample", "0", transport=SampleTransport(config.SAMPLE_PROFILES), min_interval=0)
        print("샘플 모드: 가상의 계정 데이터로 실행합니다. 실제 인스타그램에는 접속하지 않습니다.\n")
    else:
        if not args.accounts:
            parser.error("계정 목록 파일을 지정하세요. 먼저 돌려 보려면 --sample 을 붙이세요.")
        accounts, out = Path(args.accounts), Path(args.out)
        env = config.load_env()
        if not env.get("IG_ACCESS_TOKEN") or not env.get("IG_USER_ID"):
            print(".env 파일에 IG_ACCESS_TOKEN과 IG_USER_ID가 필요합니다. python check_setup.py 를 먼저 실행하세요.")
            return 1

        def on_wait(kind, seconds):
            reason = "호출 한도" if kind == "rate_limit" else "일시 오류"
            print(f"  ({reason}: {seconds}초 기다렸다가 다시 시도합니다)")

        api = InstagramAPI(
            env["IG_ACCESS_TOKEN"],
            env["IG_USER_ID"],
            version=env.get("GRAPH_API_VERSION", ""),
            min_interval=args.interval,
            on_wait=on_wait,
        )

    if not accounts.exists():
        print(f"파일을 찾을 수 없습니다: {accounts}")
        return 1
    usernames, skipped = collect.read_usernames(accounts)
    if skipped:
        print(f"계정명으로 볼 수 없어 건너뛴 값 {len(skipped)}개: {', '.join(skipped[:5])}")
    if not usernames:
        print("조회할 계정이 없습니다.")
        return 1
    print(f"계정 {len(usernames)}개를 조회합니다.\n")

    try:
        summary = collect.run(usernames, api, out, refresh=args.refresh)
    except collect.Stopped as e:
        print(f"\n멈췄습니다: {e}")
        print(f"그때까지의 결과는 {out} 에 저장되어 있습니다.")
        return 2

    print("\n결과")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print(f"\n전체 결과: {out}")
    print(f"메일 발송 대상만: {collect.mail_targets_path(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
