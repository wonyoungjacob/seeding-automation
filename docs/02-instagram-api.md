# 2. 인스타그램에서 되는 것과 안 되는 것

2026-11-17에 Meta 공식 개발자 문서를 직접 열어 확인한 내용입니다. 문서로만 확인했고 실제 계정으로 아직 돌려 보지 않은 항목은 **검증 필요**로 표시했습니다.

## 한눈에 보기

| 하고 싶은 일 | 판정 | 공식 방법 | 조건과 한계 |
|---|---|---|---|
| 계정명으로 팔로워 수, 게시물 수, 소개글, 최근 게시물의 좋아요·댓글 수 가져오기 | ✅ 가능 | Business Discovery | 상대가 비즈니스·크리에이터 계정일 때만. 연령 제한을 건 계정은 조회되지 않음. 좋아요 수를 숨긴 게시물은 좋아요 수가 빠짐. 저장 수, 공유 수, 스토리는 볼 수 없음 |
| 우리 계정을 태그한 게시물과 올린 사람 확인 | ✅ 가능 | IG User Tags | 비공개 계정의 게시물은 제외 |
| 우리 게시물에 댓글을 단 계정 확인 | ✅ 가능 | IG Media Comments | — |
| 캡션에서 우리 계정을 @멘션한 게시물 확인 | 🟡 조건부 | Mentioned Media + 웹훅 | 알림을 받을 서버(웹훅)가 있어야 함. 스토리 멘션은 지원하지 않음 |
| 해시태그로 게시물 찾기 | 🟡 조건부 | Hashtag Search | Meta 앱 검수를 통과해야 함. 계정당 7일에 해시태그 30개까지. 결과에 **작성자 계정명이 없고** 게시물 링크만 나옴. "최근 게시물"은 24시간 이내 것만. 스토리 미지원 |
| 조건(국가, 팔로워, 관심사)으로 크리에이터 검색 | 🟡 조건부 | Creator Discovery API (크리에이터 마켓플레이스) | 앱 검수와 브랜드 계정의 마켓플레이스 자격이 필요. 한국 계정 지원 여부는 문서에 없음. **검증 필요** |
| 게시물 링크만으로 작성자 알아내기 | ❌ 불가 | (oEmbed) | 2025년 11월부터 작성자 정보 제공이 중단됨 |
| 처음 연락하는 사람에게 DM 자동 발송 | ❌ 불가 | Messaging API | 공식 문서: "대화는 인스타그램 사용자가 먼저 메시지를 보낼 때만 시작된다" |
| 받은 DM 읽기 (회신 확인) | ✅ 가능, **검증 필요** | Conversations API | 대화마다 최근 메시지 20개까지 상세 조회. 요청함에서 30일 넘게 조용한 대화는 나오지 않음 |
| 상대가 답한 뒤 답장 보내기 | ✅ 가능 | Messaging API | 상대의 마지막 메시지로부터 24시간 이내 |
| DM 창을 바로 여는 링크 | ✅ 가능 | ig.me 링크 | 모바일 앱에서만 동작. PC 웹은 지원하지 않음 |
| 프로그램으로 화면 긁어 오기(크롤링), 자동 DM 프로그램 | ❌ 약관 위반 | — | 이용약관이 허가 없는 자동 수집을 금지. 계정 제한 위험 |

## 정리하면

1. **선별과 게시 확인은 지금 바로 자동화할 수 있습니다.** 계정명만 있으면 수치를 가져올 수 있고, 우리를 태그한 게시물은 올린 사람까지 나옵니다. Meta 검수가 필요 없습니다.
2. **발굴은 "이미 접점이 있는 계정"에서 출발하는 것이 현실적입니다.** 해시태그 검색은 검수가 필요하고, 통과해도 작성자 계정명을 주지 않습니다. 반면 우리를 태그하거나 댓글을 단 계정은 계정명까지 바로 얻을 수 있습니다.
3. **연락은 전송 한 번만 사람 손이 필요합니다.** 첫 DM은 자동으로 보낼 수 없지만, 상대가 답한 뒤의 대화는 API로 읽을 수 있습니다. 그래서 "회신 왔는지 확인"은 자동화 대상입니다.

## 약관에서 지켜야 할 선

- **인스타그램 이용약관**: 허가 없이 자동화된 방식으로 계정을 만들거나 정보를 수집하는 것을 금지합니다. 그래서 이 제안은 공식 API와 사람이 직접 하는 조작만 씁니다.
- **Meta 플랫폼 약관 3.a(금지 행위)**: API로 받은 데이터를 판매·제공하거나, 문서에 설명된 목적 밖으로 쓰거나, 동의 없이 개인 프로필을 만드는 데 쓰는 것을 금지합니다. 그래서 다음 원칙을 둡니다.
  - 선별에 필요한 공개 수치만 저장한다
  - 선정하지 않은 후보의 데이터는 일정 기간 뒤 지운다
  - 외부에 넘기지 않는다

## 검증이 필요한 항목

회사 계정을 연결한 첫날에 확인할 목록입니다.

| 항목 | 왜 확인이 필요한가 |
|---|---|
| Meta 검수 없이 Business Discovery, Tags, Comments를 쓸 수 있는지 | 문서에 필요한 권한은 나와 있지만 검수 필요 여부는 명시되어 있지 않음. 자사 계정용 앱은 통상 검수 없이 동작 |
| Conversations API로 인플루언서의 답장이 읽히는지 | 문서상 자사 계정은 표준 액세스로 가능하지만 "일부 기능은 고급 액세스 전까지 제대로 동작하지 않을 수 있다"는 단서가 있음 |
| 크리에이터 마켓플레이스가 회사 계정에서 열리는지 | 지원 국가 목록이 문서에 없음 |
| 스토리에서 우리 계정을 멘션했을 때 감지되는지 | Mentioned Media는 스토리를 지원하지 않음. DM 알림 경로로 잡히는지 확인 필요 |

<details>
<summary>개발자용 메모</summary>

- 문서 예시 기준 Graph API 버전: v27.0
- Business Discovery 권한: `instagram_basic`, `instagram_manage_insights`, `pages_read_engagement` (페이스북 로그인 방식)
- Tags, Mentioned Media 권한: `instagram_basic`, `instagram_manage_comments`, `pages_read_engagement`
- Hashtag Search: `Instagram Public Content Access` 기능 + `instagram_basic`, 앱 검수 필수
- Messaging, Conversations (인스타그램 로그인 방식): `instagram_business_basic`, `instagram_business_manage_messages`
- Creator Discovery: `instagram_creator_marketplace_discovery` (고급 액세스 필요, 표준 액세스는 테스트 데이터만 반환)
- Business Discovery로 조회할 수 있는 게시물 필드: `caption`, `like_count`, `comments_count`, `timestamp`, `permalink`, `media_type`, `media_product_type`, `view_count`(릴스)
- 2026-07-30 변경: 저작권 음원을 쓴 릴스는 `media_url`이 빠짐. `permalink`로 대체
- 2026-04-22 추가: Collaborative Media API. 크리에이터가 우리 계정을 공동 작업자로 초대한 게시물 목록을 조회할 수 있어 게시 확인에 추가로 쓸 수 있음

</details>

## 출처

- [Business Discovery](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/business-discovery)
- [IG User Tags](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/tags)
- [Mentioned Media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/mentioned_media)
- [Hashtag Search](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/hashtag-search)
- [Creator Discovery API](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-facebook-login/creator-marketplace)
- [oEmbed 변경 공지 (2025-04-08)](https://developers.facebook.com/blog/post/2025/04/08/oembed-updates/)
- [Messaging API](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api)
- [Conversations API](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/conversations-api)
- [ig.me 링크](https://developers.facebook.com/docs/messenger-platform/instagram/features/ig-me-links)
- [Instagram Platform 변경 내역](https://developers.facebook.com/docs/instagram-platform/changelog)
- [인스타그램 이용약관](https://help.instagram.com/581066165581870)
- [Meta 플랫폼 약관](https://developers.facebook.com/terms/)
