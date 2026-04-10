---
description: 회의 내용을 바탕으로 회의록을 작성하고 Confluence 업로드 및 Google Calendar 일정 등록을 수행하는 미팅 에이전트
---

# /meeting — Meeting Agent

## 모델

`claude-haiku-4-5-20251001`

## 사용법

```
/meeting [옵션]
```

## 옵션

| 옵션 | 설명 |
|------|------|
| `--input {파일경로}` | 회의 노트 텍스트 파일 |
| `--confluence {URL}` | Confluence 페이지 참조 (컨텍스트 보완) |
| `--initiative {TM-XXXX}` | Jira Initiative 배경 자동 로드 |
| `--title {제목}` | 회의 제목 (없으면 AI가 컨텍스트에서 추론) |
| `--date {YYYY-MM-DD}` | 회의 날짜 (기본: 오늘) |
| `--attendees {이름1,이름2}` | 참석자 목록 |
| `--calendar` | 회의록 완성 후 Google Calendar 이벤트에 요약 등록 |
| `--calendar-event-id {ID}` | 업데이트할 캘린더 이벤트 ID (없으면 날짜+제목 검색) |
| `--calendar-only` | 캘린더 등록만 실행 (회의록이 이미 완성된 경우) |

## 빠른 실행 예시

```bash
# 노트 파일로 회의록 작성
/meeting --input input/meetings/notes_{YYYYMMDD}.txt --title "Auxia 정기 미팅"

# Initiative 배경 포함 회의록
/meeting --input input/meetings/notes.txt --initiative TM-2055

# 회의록 + 캘린더 등록 한 번에
/meeting --input input/meetings/notes.txt --title "Auxia 정기 미팅" --calendar

# 기존 회의록을 캘린더에만 등록
/meeting --calendar-only --date 2026-03-09 --title "Auxia 정기 미팅"

# 텍스트 직접 붙여넣기 (args 없이 실행 → 회의 내용 입력 요청)
/meeting
```

## 실행 워크플로우

### 모드 결정
- `--calendar-only` → calendar-only 모드 (Step 4만)
- `--calendar` → write + calendar 모드 (Step 1~4)
- 나머지 → write 모드 (Step 1~3)
- args 없음 → 회의 내용 또는 파일 경로 입력 요청

---

### Step 1: 컨텍스트 수집

**입력 소스 우선순위**:
1. `--input {파일경로}` → 파일 읽기
2. `--confluence {URL}` → `confluence-tool/scripts/fetch_page.py`로 페이지 내용 가져오기
3. 둘 다 없음 → 회의 내용 직접 붙여넣기 요청

**Initiative 컨텍스트 로드** (`--initiative TM-XXXX` 있을 때):
- `input/initiatives/index.md`에서 이니셔티브 확인
- 해당 폴더의 `context.md`·`meta.json`·`decisions.md` 로드
- `meta.json`의 `confluence.primary_space`를 Space 기본값으로 사용

---

### Step 2: 회의록 초안 작성

아래 구조로 Markdown 회의록 작성:

```markdown
# {YYYY년 MM월 DD일} {회의 제목}

**일시**: {날짜}
**참석자**: {참석자 목록}
**작성자**: PM Studio (AI)

---

## 아젠다

1. ...

## 주요 논의 내용

### {아젠다 항목}
- ...

## 결정 사항

- [ ] ...

## Action Item

| 항목 | 담당 | 기한 |
|------|------|------|
| ... | ... | ... |

## 다음 미팅 예정

{날짜 또는 "미정"}
```

---

### Step 3: Confluence 업로드

**미리보기 제시 후 사용자 승인 필수** (되돌리기 어려움):
```
[회의팀] 업로드 준비 완료

제목: {YYYY년 MM월 DD일} {회의 제목}
Space: {space_key}
상위 페이지: [MATCH 미팅 회의록]

업로드할까요?
```

승인 후:
```bash
python3 .claude/skills/confluence-tool/scripts/upload.py \
  --title "{YYYY년 MM월 DD일} {제목}" \
  --space {space_key} \
  --parent-id {meeting_parent_id} \
  --content {draft_file}
```

- Space/parent_id: `config/spaces.json`의 `core_customer` 섹션
- 로컬 초안: `output/meetings/meeting_draft_{YYYYMMDD}_{slug}.md`

---

### Step 4: Google Calendar 등록 (`--calendar` / `--calendar-only`)

Google Calendar API로 이벤트 탐색 후 description 업데이트:

```
[회의 요약 — PM Studio]
📋 목적: {회의 목적}
✅ 결정 사항: {주요 결정}
📌 Action Item: {핵심 액션}
🔗 Confluence: {업로드된 페이지 URL}
```

- 환경변수: `GOOGLE_CLIENT_SECRETS_PATH`, `GOOGLE_CALENDAR_ID`
- 미설정 시: STUB 모드 (요약 텍스트만 출력)

---

## Confluence 업로드 대상

- **Space**: Core Customer (`config/spaces.json`의 `core_customer.space_key`)
- **상위 페이지**: [MATCH 미팅 회의록] (`config/spaces.json`의 `core_customer.meeting_parent_id`)
- **페이지 제목 형식**: `{YYYY년 MM월 DD일} {회의 제목}`

## 산출물

- `output/meetings/meeting_draft_{YYYYMMDD}_{slug}.md` — 로컬 회의록 초안
- Confluence 페이지 URL
- (옵션) Google Calendar 이벤트 업데이트

## PGM 연동

회의록 업로드 후 Jira Initiative 코멘트 반영이 필요하면:
```
/pgm --weekly {Confluence URL}
```
