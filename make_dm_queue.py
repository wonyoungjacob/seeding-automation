"""B. DM 전송 큐 실행 파일.

    python make_dm_queue.py --sample                        샘플 결과로 큐 만들어 보기
    python make_dm_queue.py                                 output/emails.csv 에서 큐 만들기
    python make_dm_queue.py --import-sent sent_2026-11-18.csv   보낸 목록을 연락 기록에 합치기
"""
import argparse
import sys
from pathlib import Path

from seeding import config, dm_queue
from seeding.collect import Stopped


def main() -> int:
    config.setup_console()
    parser = argparse.ArgumentParser(description="메일이 없는 계정의 DM 전송 큐를 만듭니다.")
    parser.add_argument("results", nargs="?", default="output/emails.csv", help="메일 수집 결과 파일")
    parser.add_argument("--template", default="templates/dm_template.txt", help="DM 문안 파일")
    parser.add_argument("--log", default="output/contact_log.csv", help="연락 기록 파일")
    parser.add_argument("--out", default="output/dm_queue.html", help="큐 페이지 파일")
    parser.add_argument("--limit", type=int, default=20, help="하루에 보낼 수. 기본 20")
    parser.add_argument("--sample", action="store_true", help="샘플 결과(output/sample_emails.csv)로 실행")
    parser.add_argument("--import-sent", metavar="FILE", help="큐 페이지에서 내려받은 보낸 목록을 연락 기록에 합침")
    args = parser.parse_args()

    try:
        if args.import_sent:
            added = dm_queue.import_sent(Path(args.import_sent), Path(args.log))
            print(f"연락 기록에 {added}개를 추가했습니다: {args.log}")
            return 0

        results = Path("output/sample_emails.csv" if args.sample else args.results)
        out = Path("output/sample_dm_queue.html" if args.sample and args.out == "output/dm_queue.html" else args.out)
        if not results.exists():
            hint = "python collect_emails.py --sample" if args.sample else "python collect_emails.py 계정목록.csv"
            print(f"메일 수집 결과가 없습니다: {results}\n먼저 실행하세요: {hint}")
            return 1
        summary = dm_queue.build(results, Path(args.template), Path(args.log), out, limit=args.limit)
    except Stopped as e:
        print(f"멈췄습니다: {e}")
        return 2

    for key, value in summary.items():
        print(f"  {key}: {value}")
    print(f"\n큐 페이지: {out}  (브라우저로 여세요)")
    print(f"같은 내용의 표: {out.with_suffix('.csv')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
