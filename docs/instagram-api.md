# 인스타그램 API로 되는 것과 안 되는 것

2026-11-17에 Meta 공식 개발자 문서를 직접 열어 확인한 내용입니다. 문서로만 확인했고 실제 계정으로 아직 돌려 보지 않은 항목은 **검증 필요**로 표시했습니다.

## 메일 수집 (A)

| 하고 싶은 일 | 판정 | 공식 방법 | 조건과 한계 |
|---|---|---|---|
| 계정명으로 소개글, 웹사이트 링크, 팔로워 수 가져오기 | ✅ 가능 | Business Discovery | 상대가 비즈니스·크리에이터 계정일 때만. 연령 제한을 건 계정은 조회되지 않음 |
| 프로필 "이메일" 버튼의 주소 가져오기 | ❌ 불가 | — | 해당 항목이 API에 없음 |
| 개인 계정의 소개글 가져오기 | ❌ 불가 | — | Business Discovery는 프로페셔널 계정만 지원 |

Meta 검수 없이 자기 계정용 앱으로 Business Discovery를 쓸 수 있는지는 문서에 명시되어 있지 않습니다. **검증 필요**입니다.

## DM 발송 (B)

| 하고 싶은 일 | 판정 | 공식 방법 | 조건과 한계 |
|---|---|---|---|
| 처음 연락하는 사람에게 DM 자동 발송 | ❌ 불가 | Messaging API | 공식 문서: "대화는 인스타그램 사용자가 먼저 메시지를 보낼 때만 시작된다" |
| DM 창을 바로 여는 링크 | ✅ 가능 | ig.me 링크 (`https://ig.me/m/계정명`) | 모바일 앱에서만 동작. PC 웹은 지원하지 않음 |
| 상대가 답한 뒤 답장 보내기 | ✅ 가능 | Messaging API | 상대의 마지막 메시지로부터 24시간 이내 |
| 우리 게시물에 댓글 단 사람에게 자동 DM | ✅ 가능 | Private Replies | 댓글 후 7일 이내, 1회만 |
| 받은 DM 읽기 (회신 확인) | ✅ 가능, **검증 필요** | Conversations API | 대화마다 최근 메시지 20개까지 상세 조회. 요청함에서 30일 넘게 조용한 대화는 나오지 않음 |
| 프로그램으로 화면을 조작해 DM 발송, 화면 긁어 오기 | ❌ 약관 위반 | — | 이용약관이 허가 없는 자동화된 접근과 수집을 금지. 계정 제한 위험 |

## 이 도구가 쓰는 요청

```
GET https://graph.facebook.com/v27.0/{내 인스타그램 계정 ID}
    ?fields=business_discovery.username({조회할 계정명}){username,biography,website,followers_count,media_count}
    &access_token={토큰}
```

- 필요한 권한: `instagram_basic`, `instagram_manage_insights`, `pages_read_engagement`. 계정 ID를 찾는 데 `pages_show_list`
- 페이스북 로그인 방식의 토큰을 씁니다.

## 출처

- [Business Discovery](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/business-discovery)
- [Messaging API](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api)
- [ig.me 링크](https://developers.facebook.com/docs/messenger-platform/instagram/features/ig-me-links)
- [Private Replies](https://developers.facebook.com/docs/instagram-platform/private-replies/)
- [Conversations API](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/conversations-api)
- [인스타그램 이용약관](https://help.instagram.com/581066165581870)
