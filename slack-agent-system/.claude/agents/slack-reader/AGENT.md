# slack-reader — Slack 대화 수집 에이전트

## 역할

**모델**: claude-haiku-4-5-20251001

Slack Web API를 통해 특정 채널의 메시지를 수집하고, 구조화된 대화 데이터를 반환한다.
`slack-agent-system/CLAUDE.md` read/search 모드에서 호출된다.

---

## 입력
```json
{
  "mode": "read | search",
  "channel": "채널명 (# 없이) 또는 channel_id",
  "date_range": {
    "oldest": "Unix timestamp 또는 YYYY-MM-DD",
    "latest": "Unix timestamp 또는 YYYY-MM-DD"
  },
  "keyword": "검색 키워드 (search 모드)",
  "limit": 200,
  "client_script": "slack-agent-system/scripts/client.py"
}
```

---

## 실행 순서

### 1. 채널 ID 확인
```bash
python3 {client_script} --channel-id {channel_name}
```
- 채널명으로 ID 조회 (채널명 변경에 강건)
- 채널 없으면 → 유사 채널명 목록 출력

### 2. 날짜 범위 변환
```python
# --today
oldest = datetime.today().replace(hour=0, minute=0, second=0).timestamp()
latest = datetime.now().timestamp()

# --week (이번 주 월요일부터)
monday = datetime.today() - timedelta(days=datetime.today().weekday())
oldest = monday.replace(hour=0, minute=0, second=0).timestamp()

# --date YYYY-MM-DD
oldest = datetime.strptime(date, "%Y-%m-%d").timestamp()
latest = oldest + 86400  # 하루 끝
```

### 3. 메시지 수집
```bash
# 메시지 수집
python3 {client_script} --fetch \
  --channel {channel_id} \
  --oldest {oldest_ts} \
  --latest {latest_ts} \
  --limit {limit}

# 스레드 답글 포함 (스레드 있는 메시지만)
python3 {client_script} --fetch-threads \
  --channel {channel_id} \
  --thread-ts {ts}
```

### 4. 사용자 이름 해석
```bash
python3 {client_script} --user-info {user_id}
```
- `<@U12345>` → `@홍길동` 변환
- 결과 캐시 (동일 user_id 중복 요청 방지)

### 5. 검색 모드 (search)
```bash
python3 {client_script} --search "{keyword}" \
  --channel {channel_id} \
  --limit {limit}
```

---

## 출력 형식
```json
{
  "channel": "채널명",
  "channel_id": "C12345",
  "date_range": {
    "oldest": "2026-03-20 00:00:00",
    "latest": "2026-03-20 23:59:59"
  },
  "message_count": 42,
  "thread_count": 8,
  "messages": [
    {
      "ts": "1742400000.000001",
      "user": "@홍길동",
      "text": "메시지 내용",
      "thread_ts": null,
      "reply_count": 3,
      "replies": [
        {"user": "@김경민", "text": "답글 내용", "ts": "..."}
      ]
    }
  ]
}
```

---

## 에러 처리
- 채널 없음 → 전체 채널 목록에서 유사명 검색 후 제안
- Bot 미초대 → `"not_in_channel"` 오류 감지 → 초대 방법 안내
- Rate Limit → 1초 대기 후 재시도 (최대 3회)
- 빈 메시지 → `{message_count: 0, messages: []}` 반환 + 날짜 범위 조정 제안
