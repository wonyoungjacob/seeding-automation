"""실제 계정 연결 확인.

.env 에 넣은 토큰으로 인스타그램 계정을 찾고, 조회가 되는지 한 번 시험한다.

    python check_setup.py
"""
import sys

from seeding import config
from seeding.ig_api import GraphError, InstagramAPI


def main() -> int:
    config.setup_console()
    env = config.load_env()
    token = env.get("IG_ACCESS_TOKEN", "")
    if not token:
        print(".env 파일에 IG_ACCESS_TOKEN이 없습니다.")
        print(".env.example 을 .env 로 복사한 뒤 토큰을 붙여넣으세요. 발급 방법은 README에 있습니다.")
        return 1

    api = InstagramAPI(token, env.get("IG_USER_ID", ""), version=env.get("GRAPH_API_VERSION", ""), min_interval=0)

    print("1) 토큰으로 접근할 수 있는 인스타그램 계정을 찾습니다.")
    try:
        accounts = api.my_instagram_accounts()
    except GraphError as e:
        print(f"   실패: {e.message} (코드 {e.code})")
        if e.kind == "auth":
            print("   토큰이 만료됐거나 잘못 복사됐습니다. 새로 발급해 주세요.")
        elif e.kind == "permission":
            print("   권한이 부족합니다. pages_show_list, instagram_basic 이 선택됐는지 확인하세요.")
        return 1
    if not accounts:
        print("   찾지 못했습니다. 다음을 확인하세요.")
        print("   - 인스타그램 계정이 프로페셔널(비즈니스·크리에이터) 계정인지")
        print("   - 그 계정이 페이스북 페이지와 연결되어 있는지")
        print("   - 토큰을 만들 때 그 페이지를 선택했는지")
        return 1
    for a in accounts:
        print(f"   - @{a['username']}  (페이지: {a['page']}, ID: {a['ig_user_id']})")

    ig_user_id = env.get("IG_USER_ID", "")
    known = {a["ig_user_id"]: a for a in accounts}
    if ig_user_id not in known:
        if len(accounts) > 1 and not ig_user_id:
            print("   계정이 여러 개입니다. 쓸 계정의 ID를 .env 의 IG_USER_ID 에 적고 다시 실행하세요.")
            return 1
        ig_user_id = accounts[0]["ig_user_id"]
        config.save_env_value("IG_USER_ID", ig_user_id)
        print(f"   .env 에 IG_USER_ID={ig_user_id} 를 저장했습니다.")
    me = known.get(ig_user_id, accounts[0])

    print("2) 계정 조회(Business Discovery)를 시험합니다.")
    api.ig_user_id = ig_user_id
    try:
        profile = api.business_discovery(me["username"])
    except GraphError as e:
        print(f"   실패: {e.message} (코드 {e.code})")
        if e.kind == "permission":
            print("   instagram_basic, instagram_manage_insights, pages_read_engagement 권한을 확인하세요.")
        return 1
    print(f"   성공: @{profile.get('username')} 팔로워 {profile.get('followers_count')}명")
    print("\n준비됐습니다. 이제 실행하세요:  python collect_emails.py 계정목록.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
