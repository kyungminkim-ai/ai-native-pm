# /weekly — Weekly 공유사항 업데이터

## 사용법

```
/weekly [Confluence 회의록 URL]
```

## 역할

Confluence 회의록을 분석하여 관련 Jira Initiative 티켓별로 Weekly 공유사항을 정리하고,
사용자 승인 후 각 티켓에 코멘트로 게시한다.

---

## 전체 워크플로우

```
Confluence URL 입력
      │
      ▼
[Step 1] 회의록 페이지 로드
  fetch_page.py로 마크다운 변환
      │
      ▼
[Step 2] Initiative별 내용 파싱 (AI 분석)
  - TM-XXXX 티켓 키 추출
  - "지난주 진행상황" / "Action Item (이번주)" 항목 분류
      │
      ▼
[Step 3] 마크다운 미리보기 출력 + 사용자 승인 대기
      │
      ▼ (승인 시)
[Step 4] weekly_draft.json 생성
      │
      ▼
[Step 5] post_weekly_comment.py 실행 → Jira 코멘트 게시
      │
      ▼
[Step 6] 결과 보고 (코멘트 URL 목록)
```

---

## Step 1: 회의록 로드

URL에서 페이지 ID 추출 후 fetch_page.py 호출:

```bash
cd /Users/musinsa/Documents/agent_project/pm-studio && \
python3 .claude/skills/confluence-tool/scripts/fetch_page.py \
  --page-id {페이지_ID} \
  --format markdown
```

URL 패턴:
- `https://*.atlassian.net/wiki/spaces/*/pages/{PAGE_ID}/...` → PAGE_ID 추출
- `https://*.atlassian.net/wiki/spaces/*/pages/{PAGE_ID}` → PAGE_ID 추출

---

## Step 2: Initiative별 파싱 (AI 분석 규칙)

회의록 전문을 분석하여 각 Jira Initiative(TM-XXXX)별로 논의된 내용을 추출한다.

### 2-1. Initiative 식별 방법
- 회의록에 명시된 `TM-XXXX` 티켓 키 직접 추출
- 이니셔티브명이 언급된 경우 `input/initiatives/index.md`에서 매핑

### 2-2. 섹션 분류 기준

| 항목 | 분류 기준 |
|------|----------|
| 지난주 진행상황 | 완료된 작업, 진행된 미팅, 결정된 사항, 배포/릴리스 내용 |
| Action Item (이번주) | 다음 액션, ETA가 있는 작업, 담당자가 배정된 태스크, 후속 논의 필요 사항 |

### 2-3. 항목 작성 규칙
- 각 항목은 간결하게 1줄 요약 (50자 이내 권장)
- ETA가 있으면 포함: `기능 X 개발 완료 (ETA: 3/15)`
- 담당자가 명시된 경우 포함: `API 설계 문서 작성 (담당: 홍길동)`
- Jira 티켓이 언급된 경우 sub 항목으로 포함:
  ```json
  {
    "text": "추천 알고리즘 개선 완료",
    "sub": ["PSN-704: 스케줄링 시스템 고도화"]
  }
  ```

### 2-4. 주차 계산
- 오늘 날짜 기준 ISO 주차 사용: `datetime.now().isocalendar()[1]`
- 연초 기준: 1월 첫 주 = 1주차

---

## Step 3: 마크다운 미리보기

분석 결과를 아래 형식으로 출력하고 **반드시 사용자 승인을 받는다**:

```
[Weekly 업데이터] 회의록 분석 완료 — N주차

---

### TM-XXXX — {이니셔티브명}

**지난주 진행상황**
- 항목1
  - 하위 항목 (예: PSN-xxx)
- 항목2

**Action Item (이번주)**
- 항목1 (ETA: MM/DD)
- 항목2

---

### TM-YYYY — {이니셔티브명}
...

---

총 {N}개 Initiative, {M}개 항목 추출.
위 내용으로 Jira Weekly 코멘트를 게시할까요?
수정이 필요하면 수정 내용을 말씀해주세요.
```

---

## Step 4: weekly_draft.json 생성

승인 후 아래 형식의 JSON 파일을 생성한다:

```json
{
  "week": 10,
  "source_url": "https://musinsa-oneteam.atlassian.net/wiki/...",
  "generated_at": "2026-03-09",
  "updates": [
    {
      "ticket": "TM-2055",
      "initiative_name": "MATCH Phase2 - Foundation",
      "prev_week": [
        "항목 텍스트",
        {
          "text": "항목 텍스트",
          "sub": ["하위 항목1", "하위 항목2"]
        }
      ],
      "action_items": [
        "항목 텍스트 (ETA: MM/DD)",
        {
          "text": "항목 텍스트",
          "sub": ["하위 항목1"]
        }
      ]
    }
  ]
}
```

저장 위치: `output/weekly_draft_{YYYYMMDD}.json`

---

## Step 5: Jira 코멘트 게시

```bash
cd /Users/musinsa/Documents/agent_project/pm-studio && \
python3 .claude/skills/weekly-updater/scripts/post_weekly_comment.py \
  --input output/weekly_draft_{YYYYMMDD}.json
```

---

## Step 6: 결과 보고

```
[Weekly 업데이터] 게시 완료!

✅ TM-2055 — MATCH Phase2 - Foundation
   → https://musinsa-oneteam.atlassian.net/browse/TM-2055?focusedCommentId=XXXXX

✅ TM-2061 — Campaign Meta Engine
   → https://musinsa-oneteam.atlassian.net/browse/TM-2061?focusedCommentId=XXXXX

📁 결과: output/weekly_result_{YYYYMMDD}.json
```

---

## 에러 처리

| 오류 | 처리 방법 |
|------|----------|
| 페이지 접근 불가 (403/404) | 페이지 ID 또는 권한 확인 요청 |
| Initiative 키 없음 | 회의록에서 TM-XXXX를 찾지 못한 경우 사용자에게 직접 입력 요청 |
| Jira API 401 | "CONFLUENCE_API_TOKEN 환경변수를 확인하세요" 후 중단 |
| 특정 티켓 게시 실패 | 해당 티켓 skip + 결과에 오류 표시, 나머지 계속 진행 |
| 항목이 너무 많음 (10개+) | "항목이 많습니다. 핵심 항목만 포함할까요?" 확인 |

---

## 주의사항

- **게시는 되돌리기 어렵다** — 반드시 Step 3 미리보기 승인 후 게시
- 기존 Weekly 코멘트는 수정하지 않고, **새 코멘트로 추가**한다
- 회의록 1개에 여러 Initiative가 포함될 수 있다 — 모두 처리
- Initiative가 명시되지 않은 논의 내용은 건너뛴다
