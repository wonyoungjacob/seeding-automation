# 부록: 인스타그램 API 조사

2026-11-17에 Meta 공식 개발자 문서를 직접 열어 확인한 내용입니다. 문서로만 확인했고 실제 계정으로 아직 돌려 보지 않은 항목은 **검증 필요**로 표시했습니다. 본문은 [README](../README.md)에 있습니다.

## 되는 것과 안 되는 것

| 하고 싶은 일 | 판정 | 공식 방법 | 조건과 한계 |
|---|---|---|---|
| 계정명으로 소개글, 웹사이트 링크, 팔로워 수, 최근 게시물의 좋아요·댓글 수 가져오기 | ✅ 가능 | Business Discovery | 상대가 비즈니스·크리에이터 계정일 때만. 연령 제한을 건 계정은 조회되지 않음. 저장 수, 공유 수, 스토리는 볼 수 없음 |
| 프로필 "이메일" 버튼의 주소 가져오기 | ❌ 불가 | — | 해당 항목이 API에 없음 |
| 크리에이터의 메일 주소 가져오기 | 🟡 조건부 | Creator Discovery API의 `email` | "있는 경우" 제공. 앱 검수(고급 액세스)와 브랜드의 마켓플레이스 자격 필요. 표준 액세스는 테스트 데이터만 반환 |
| 조건(국가, 팔로워, 관심사)으로 크리에이터 검색 | 🟡 조건부 | Creator Discovery API | 위와 같음. `has_public_contact_email`, `exclude_messaged_creators` 필터 있음. 계정명으로 조회하면 마켓플레이스 가입 여부와 무관하게 자격 있는 프로페셔널 계정이 반환됨 |
| 처음 연락하는 사람에게 DM 자동 발송 | ❌ 불가 | Messaging API | 공식 문서: "대화는 인스타그램 사용자가 먼저 메시지를 보낼 때만 시작된다" |
| 크리에이터에게 협업 제안 메시지 보내기 | ✅ 가능, **검증 필요** | 크리에이터 마켓플레이스 (Meta 비즈니스 스위트, 카페24 연동) | 제안은 크리에이터 DM의 별도 폴더로 감. 메시지 발송 API는 공개 문서에 없음. 자격과 한도는 확인 필요 |
| 우리 게시물에 댓글 단 사람에게 자동 DM | ✅ 가능 | Private Replies | 댓글 후 7일 이내, 1회만. 상대가 답하면 24시간 안에 후속 메시지 가능 |
| 받은 DM 읽기 (회신 확인) | ✅ 가능, **검증 필요** | Conversations API | 대화마다 최근 메시지 20개까지 상세 조회. 요청함에서 30일 넘게 조용한 대화는 나오지 않음 |
| DM 창을 바로 여는 링크 | ✅ 가능 | ig.me 링크 | 모바일 앱에서만 동작. PC 웹은 지원하지 않음 |
| 우리 계정을 태그한 게시물과 올린 사람 확인 | ✅ 가능 | IG User Tags | 비공개 계정의 게시물은 제외 |
| 해시태그로 게시물 찾기 | 🟡 조건부 | Hashtag Search | 앱 검수 필요. 계정당 7일에 해시태그 30개. 결과에 작성자 계정명이 없음 |
| 게시물 링크만으로 작성자 알아내기 | ❌ 불가 | (oEmbed) | 2025년 11월부터 작성자 정보 제공이 중단됨 |
| 프로그램으로 화면 긁어 오기, 자동 DM 프로그램 | ❌ 약관 위반 | — | 이용약관이 허가 없는 자동 수집을 금지. 계정 제한 위험 |

## 약관과 법에서 지켜야 할 선

- **인스타그램 이용약관**: 허가 없이 자동화된 방식으로 계정을 만들거나 정보를 수집하는 것을 금지합니다.
- **Meta 플랫폼 약관 3.a(금지 행위)**: API로 받은 데이터를 판매·제공하거나, 문서에 설명된 목적 밖으로 쓰거나, 동의 없이 개인 프로필을 만드는 데 쓰는 것을 금지합니다.
- **정보통신망법 제50조의2**: 홈페이지 운영자의 사전 동의 없이 프로그램으로 메일 주소를 자동 수집하는 것, 그렇게 모은 주소를 유통하거나 발송에 쓰는 것을 금지합니다.

## 크리에이터 마켓플레이스

- 2022년 미국에서 시작했고 2024년 5월 한국에 도입됐습니다. 도입 당시에는 일부 브랜드와 크리에이터를 대상으로 운영했습니다.
- 브랜드는 Meta 비즈니스 스위트에서, 크리에이터는 프로페셔널 대시보드에서 접속합니다.
- 브랜드는 조건으로 크리에이터를 검색하고, DM을 보내고, 여러 크리에이터에게 협업을 제안할 수 있습니다. 제안은 크리에이터 DM 안의 별도 폴더에 들어갑니다.
- 카페24가 2026년 10월 29일에 크리에이터 마켓플레이스 API 연동을 발표했습니다. 카페24 안에서 크리에이터를 찾고 파트너십 메시지를 보낼 수 있고, 크리에이터의 메일 주소 없이도 제안할 수 있다고 보도됐습니다. 요금, 계정 조건, 일괄 발송 가능 여부는 기사에 없습니다.

<details>
<summary>개발자용 메모</summary>

- 문서 예시 기준 Graph API 버전: v27.0
- Business Discovery 권한: `instagram_basic`, `instagram_manage_insights`, `pages_read_engagement` (페이스북 로그인 방식)
- Business Discovery로 조회되는 계정 항목: `biography`, `website`, `username`, `followers_count`, `media_count`
- Private Replies: `POST /<IG_ID>/messages`, `recipient.comment_id` 지정. 권한은 로그인 방식에 따라 `instagram_manage_comments` 계열과 `instagram_manage_messages`
- Messaging, Conversations (인스타그램 로그인 방식): `instagram_business_basic`, `instagram_business_manage_messages`. 자사 계정은 표준 액세스, 남의 계정을 다루면 고급 액세스
- Creator Discovery: `instagram_creator_marketplace_discovery`, `instagram_basic`, `pages_manage_metadata`, `pages_show_list`, `business_management`. 엔드포인트 `/<IG_USER_ID>/creator_marketplace_creators`
- Hashtag Search: `Instagram Public Content Access` 기능과 `instagram_basic`, 앱 검수 필수

</details>

## 출처

- [Business Discovery](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/business-discovery)
- [Creator Discovery API](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-facebook-login/creator-marketplace)
- [Messaging API](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api)
- [Private Replies](https://developers.facebook.com/docs/instagram-platform/private-replies/)
- [Conversations API](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/conversations-api)
- [ig.me 링크](https://developers.facebook.com/docs/messenger-platform/instagram/features/ig-me-links)
- [IG User Tags](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/tags)
- [Hashtag Search](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/hashtag-search)
- [oEmbed 변경 공지 (2025-04-08)](https://developers.facebook.com/blog/post/2025/04/08/oembed-updates/)
- [Instagram Platform 변경 내역](https://developers.facebook.com/docs/instagram-platform/changelog)
- [인스타그램 이용약관](https://help.instagram.com/581066165581870)
- [Meta 플랫폼 약관](https://developers.facebook.com/terms/)
- [정보통신망법 제50조의2 (서울대학교 안내 페이지의 조문)](https://www.snu.ac.kr/prohibition_of_unauthorized_email_collection)
- [인스타그램, '크리에이터 마켓플레이스' 국내 도입 (브랜드브리프, 2024-05-13)](https://www.brandbrief.co.kr/news/articleView.html?idxno=6913)
- [카페24, '인스타 데이터' 연동 (지디넷코리아, 2026-10-29)](https://zdnet.co.kr/view/?no=20261029105313)
