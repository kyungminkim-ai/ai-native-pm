# PGM Command Center — 오케스트레이터

## 역할

PM의 주간 업무 전반을 처리하는 통합 허브.
Jira 성과 분석, 회의록 처리, Jira 코멘트 게시, 보고서 배포를 단일 파이프라인으로 연결한다.

> 공통 규약: `../CONVENTIONS.md`

---

## 실행 모드

| 모드 | 커맨드 | 용도 |
|------|--------|------|
| **flash** | `/pgm [JIRA_KEY] [메모]` | Weekly Flash Report만 생성 (Jira 데이터 기반) |
| **weekly** | `/pgm --weekly [CONFLUENCE_URL]` | 회의록 → Jira Initiative 코멘트 게시만 |
| **full** | `/pgm --full [JIRA_KEY] [CONFLUENCE_URL] [메모]` | Flash + 회의록 + Jira 코멘트 전부 |
| **initiative-weekly** | `/pgm --initiative-weekly [JIRA_KEY] [WEEKLY_DOC_URL] --notes [MEETING_NOTES_URL]` | 이니셔티브 위클리 문서 업데이트 + Jira 'Weekly 공유사항' 섹션 수정 |

모드 미지정 시 → `flash` 모드로 동작.

---

## 전체 데이터 플로우

```
/pgm --full MATCH https://confluence-url "선택 메모"
    │
    ▼
[Step 0: 체크포인트 확인]
  .pipeline_state.json 존재 시 → 완료 단계 스킵, 실패 단계부터 재개
    │
    ▼
[Step 1: 데이터 수집] ← 병렬 실행 (Agent Teams 패턴)
  ├── jira-parser 스킬 → output/jira_raw_{YYYYMMDD}.json
  └── fetch_page.py → output/confluence_{YYYYMMDD}.md  (weekly/full 모드만)
    │
    ▼ (Step 1 완료 후 아래 2-A, 2-B를 동시 실행)
    ┌─────────────────────────────────────────────────┐
    │ [Step 2-A: Flash 분석] ← 병렬                  │
    │   입력: jira_raw + 메모 + 이전 주 데이터         │
    │   에이전트: .claude/agents/analyst/AGENT.md     │
    │   출력: output/flash_analysed_{YYYYMMDD}.json   │
    │   (WoW 트렌드 포함 시 prev 참조)                │
    │                                                 │
    │ [Step 2-B: 회의록 분석] ← 병렬                  │
    │   입력: confluence_{YYYYMMDD}.md               │
    │   에이전트: .claude/agents/analyst/AGENT.md     │
    │   출력: output/minutes_analysed_{YYYYMMDD}.json │
    │   (Initiative별 항목 + 회의 요약 동시 추출)      │
    └─────────────────────────────────────────────────┘
    │ (2-A, 2-B 모두 완료 후)
    ▼
[Step 3: publisher + minutes-generator] ← 병렬 실행  (flash/full 모드)
  publisher (2-A 출력 기반):
    ├── output/flash_{YYYYMMDD}.md
    ├── Google Docs 초안 URL
    └── Gmail Draft ID
  minutes-generator (2-B 출력 기반):
    ├── output/meeting_minutes_{YYYYMMDD}.md
    ├── Google Docs 회의록 URL
    └── output/slack_summary_{YYYYMMDD}.txt
    │
    ▼
[Step 4: weekly-poster]  (weekly/full 모드)
  minutes_analysed_{YYYYMMDD}.json에서 Initiative별 항목 재사용 (재파싱 불필요)
  → 마크다운 미리보기 → 사용자 승인
  → output/weekly_draft_{YYYYMMDD}.json 생성
  → post_weekly_comment.py 실행 → Jira 코멘트 게시
  → output/weekly_result_{YYYYMMDD}.json
    │
    ▼
[Step 5: Self-Validation + Artifacts 갱신]
  _artifacts.json 업데이트
  레지스트리 등록: python3 scripts/registry.py register --type flash --path pgm-agent-system/output/flash_{YYYYMMDD}.md
  12개 체크리스트 검증
```

> **병렬화 포인트**: Step 2-A(Flash 분석)와 Step 2-B(회의록 분석)는 서로 다른 입력을 사용하므로
> 동시 실행 가능. `full` 모드에서 Step 3까지의 전체 소요 시간이 단축된다.

---

## Step 0: 체크포인트 확인

실행 시작 시 `output/.pipeline_state.json`을 확인한다.

- 파일이 없거나 `date` 필드가 오늘과 다르면 → **새 실행** (모든 단계 pending으로 초기화)
- `date`가 오늘과 같으면 → **재실행** 모드:
  - `"done"` 단계: 스킵 (기존 산출물 재사용)
  - `"failed"` / `"pending"` 단계: 해당 단계부터 실행
  - 사용자에게 알림: "이전 실행 감지. [완료 단계] 스킵, [미완료 단계]부터 재개합니다."

파이프라인 상태 파일 형식: `CONVENTIONS.md §6` 참조.

---

## Step 1: 데이터 수집

### 1-A: Jira 데이터 (flash/full 모드)

```bash
cd /Users/musinsa/Documents/agent_project/pm-studio && \
python3 pgm-agent-system/.claude/skills/jira-parser/scripts/parse_jira.py \
  --project {JIRA_KEY} \
  --week-offset 0 \
  --output pgm-agent-system/output/jira_raw_{YYYYMMDD}.json
```

### 1-B: Confluence 회의록 (weekly/full 모드)

URL 패턴에서 PAGE_ID 추출:
- `https://*.atlassian.net/wiki/spaces/*/pages/{PAGE_ID}/...` → PAGE_ID 추출

```bash
cd /Users/musinsa/Documents/agent_project/pm-studio && \
python3 .claude/skills/confluence-tool/scripts/fetch_page.py \
  --page-id {PAGE_ID} \
  --format markdown \
  --output pgm-agent-system/output/confluence_{YYYYMMDD}.md
```

**입력 미제공 시**:
> "어떤 Jira 프로젝트를 대상으로 할까요? (예: MATCH, CME)
> 이번 주 회의록 Confluence URL도 있으면 함께 주세요."

---

## Step 2: analyst 서브에이전트 병렬 호출

`full` 모드: 2-A와 2-B를 **동시에** 실행한다. `flash` 모드: 2-A만 실행.

### Step 2-A: Flash 분석 (flash/full 모드)

```
Task: 아래 Jira 데이터를 분석하여 Weekly Flash 항목을 분류하고 우선순위를 판단해줘.
      이전 주 분석 결과가 있으면 WoW 트렌드를 함께 생성해줘.
에이전트 스펙: .claude/agents/analyst/AGENT.md

입력:
  - Jira 원시 데이터: pgm-agent-system/output/jira_raw_{YYYYMMDD}.json
  - 사용자 메모: input/notes/memo_{YYYYMMDD}.txt (있으면)
  - 이전 주 데이터: pgm-agent-system/output/analysed_report_prev.json (있으면)

출력: pgm-agent-system/output/flash_analysed_{YYYYMMDD}.json
```

### Step 2-B: 회의록 분석 (weekly/full 모드) ← 2-A와 동시 실행

```
Task: 아래 Confluence 회의록을 분석하여 Initiative별 항목과 회의 요약을 추출해줘.
에이전트 스펙: .claude/agents/analyst/AGENT.md

입력:
  - Confluence 회의록: pgm-agent-system/output/confluence_{YYYYMMDD}.md

출력: pgm-agent-system/output/minutes_analysed_{YYYYMMDD}.json
  - initiatives: Initiative별 {지난주 진행상황, Action Item} 목록
  - summary: 전체 회의 핵심 요약 (3줄 이내)
  - agenda: 주요 아젠다 리스트
```

> **중요**: 2-A 완료를 기다리지 않고 2-B를 동시에 시작한다.
> Step 3는 2-A, 2-B가 모두 완료된 후 시작한다.

---

## Step 3: publisher + minutes-generator 병렬 호출

Step 2-A, 2-B 완료 후 두 에이전트를 **동시에** 호출한다.
각 에이전트는 서로 다른 Step 2 출력을 입력으로 사용하므로 완전히 독립적으로 실행 가능.

### publisher 호출 (Step 2-A 출력 기반)

```
Task: flash_analysed_{YYYYMMDD}.json을 3가지 포맷(Markdown, Google Docs, Gmail)으로 변환해줘.
에이전트 스펙: .claude/agents/publisher/AGENT.md

입력: pgm-agent-system/output/flash_analysed_{YYYYMMDD}.json
출력:
  - pgm-agent-system/output/flash_{YYYYMMDD}.md
  - Google Docs 초안 URL
  - Gmail Draft ID
```

### minutes-generator 호출 (Step 2-B 출력 기반) ← publisher와 동시 실행

```
Task: minutes_analysed_{YYYYMMDD}.json을 기반으로 회의록 초안과 Slack 요약을 생성해줘.
에이전트 스펙: .claude/agents/minutes-generator/AGENT.md

입력: pgm-agent-system/output/minutes_analysed_{YYYYMMDD}.json
출력:
  - pgm-agent-system/output/meeting_minutes_{YYYYMMDD}.md
  - Google Docs 회의록 URL
  - pgm-agent-system/output/slack_summary_{YYYYMMDD}.txt
```

---

## Step 4: weekly-poster (weekly/full 모드)

### 4-A: Initiative별 파싱

Step 2-B의 `minutes_analysed_{YYYYMMDD}.json`에서 `initiatives` 필드를 재사용한다.
(Confluence 재파싱 불필요 — Step 2-B에서 이미 Initiative별로 추출됨)

`minutes_analysed_{YYYYMMDD}.json` 파일이 없는 경우(weekly 단독 모드)에만
`confluence_{YYYYMMDD}.md` 전문을 분석하여 각 Jira Initiative(TM-XXXX)별로 논의 내용 추출.

**Initiative 식별**:
- 회의록에 명시된 `TM-XXXX` 직접 추출
- 이니셔티브명만 언급된 경우 `input/initiatives/index.md`에서 매핑

**섹션 분류 기준**:

| 항목 | 분류 기준 |
|------|----------|
| 지난주 진행상황 | 완료된 작업, 진행된 미팅, 결정된 사항, 배포/릴리스 내용 |
| Action Item (이번주) | 다음 액션, ETA가 있는 작업, 담당자 배정 태스크, 후속 논의 필요 사항 |

**항목 작성 규칙**:
- 각 항목 1줄 요약 (50자 이내)
- ETA 있으면 포함: `기능 X 개발 완료 (ETA: 3/15)`
- 담당자 명시 시 포함: `API 설계 문서 작성 (담당: 홍길동)`
- Jira 티켓 언급 시 sub 항목으로:
  ```json
  { "text": "추천 알고리즘 개선 완료", "sub": ["PSN-704: 스케줄링 시스템 고도화"] }
  ```

### 4-B: 마크다운 미리보기 + 사용자 승인

```
[PGM] 회의록 분석 완료 — {N}주차

---
### TM-XXXX — {이니셔티브명}

**지난주 진행상황**
- 항목1
- 항목2

**Action Item (이번주)**
- 항목1 (ETA: MM/DD)

---
총 {N}개 Initiative, {M}개 항목 추출.
Jira Weekly 코멘트를 게시할까요? (수정 내용이 있으면 말씀해주세요)
```

**반드시 사용자 승인 후 게시** — 게시는 되돌리기 어렵다.

### 4-C: weekly_draft.json 생성 및 Jira 게시

승인 후 JSON 생성:
```json
{
  "week": 10,
  "source_url": "https://...",
  "generated_at": "2026-03-09",
  "updates": [
    {
      "ticket": "TM-2055",
      "initiative_name": "MATCH Phase2 - Foundation",
      "prev_week": ["항목1", { "text": "항목2", "sub": ["PSN-xxx"] }],
      "action_items": ["항목1 (ETA: MM/DD)"]
    }
  ]
}
```

저장: `pgm-agent-system/output/weekly_draft_{YYYYMMDD}.json`

Jira 코멘트 게시:
```bash
cd /Users/musinsa/Documents/agent_project/pm-studio && \
python3 .claude/skills/weekly-updater/scripts/post_weekly_comment.py \
  --input pgm-agent-system/output/weekly_draft_{YYYYMMDD}.json
```

결과: `pgm-agent-system/output/weekly_result_{YYYYMMDD}.json`

---

## initiative-weekly 모드

`--initiative-weekly` 모드는 독립 파이프라인으로 동작한다. 기존 flash/weekly/full 파이프라인과 별개.

```
initiative-weekly-agent 서브에이전트 호출:
  에이전트 스펙: .claude/agents/initiative-weekly-agent/AGENT.md

  입력:
    - JIRA_KEY: Initiative 키 (예: TM-2058)
    - WEEKLY_DOC_URL: 이니셔티브 위클리 Confluence URL
    - MEETING_NOTES_URL: 회의록 URL (선택)

  출력:
    - Confluence 위클리 문서 업데이트 (updateConfluencePage)
    - Jira Description 'Weekly 공유사항' 섹션 수정 (editJiraIssue)
```

이 모드는 Step 0~5 파이프라인을 거치지 않는다. initiative-weekly-agent가 자체 파이프라인으로 완결 처리.

---

## Step 5: Self-Validation + Artifacts 갱신

### Self-Validation 체크리스트

| # | 검증 항목 | 통과 기준 | 재호출 대상 |
|---|----------|----------|------------|
| 1 | Flash MD 존재 | `flash_{YYYYMMDD}.md` 파일 존재 | publisher |
| 2 | 핵심 수치 볼드 | `**숫자**` 패턴 1개 이상 | publisher |
| 3 | 명사형 종결 어미 | `~함`, `~완료`, `~예정`, `~중` | publisher |
| 4 | 카테고리 4종 완비 | Achievements / Status / Next Week / 이슈&조치 | analyst |
| 5 | 핵심 항목 존재 | `⭐ 핵심` 태그 항목 1개 이상 | analyst |
| 6 | Health Status 표기 | 🟢/🟡/🔴 + 판단 근거 1줄 | publisher |
| 7 | Task 완료 현황 형식 | "현재 N개 완료 / 차주 예상 N+x개" | analyst |
| 8 | 진행 중 Task 진척률 | 진행 중 항목에 예상 Due + 차주 예상 % | analyst |
| 9 | 이슈 섹션 완비 | 담당자·기한·구체 액션 3개 필드 | analyst |
| 10 | 회의록 산출물 완비 | meeting_minutes MD + Docs URL (full 모드만) | minutes-generator |
| 11 | Slack 요약 완비 | slack_summary txt + 200자 이내 (full 모드만) | minutes-generator |
| 12 | Weekly 코멘트 게시 | weekly_result JSON 존재 (weekly/full 모드만) | — |

2회 재시도 후 실패 항목은 `[TBD]` 표시 후 사용자에게 보고.

### Artifacts 갱신

완료 후 `output/_artifacts.json` 업데이트:
```json
{
  "date": "YYYYMMDD",
  "week": {ISO_WEEK},
  "flash_md": "pgm-agent-system/output/flash_{YYYYMMDD}.md",
  "meeting_minutes_md": "pgm-agent-system/output/meeting_minutes_{YYYYMMDD}.md",
  "weekly_draft_json": "pgm-agent-system/output/weekly_draft_{YYYYMMDD}.json",
  "jira_raw_json": "pgm-agent-system/output/jira_raw_{YYYYMMDD}.json",
  "analysed_report_json": "pgm-agent-system/output/analysed_report.json",
  "google_docs_flash_url": "{URL 또는 null}",
  "google_docs_minutes_url": "{URL 또는 null}",
  "gmail_draft_id": "{ID 또는 null}",
  "weekly_result_json": "pgm-agent-system/output/weekly_result_{YYYYMMDD}.json"
}
```

---

## 완료 출력 형식

### flash 모드
```
✅ Weekly Flash Report 생성 완료!

[Flash Report]
📄 Markdown: pgm-agent-system/output/flash_{YYYYMMDD}.md
📝 Google Docs: {URL}
📧 Gmail 초안: {Draft ID}

⭐ 핵심 성과 (상위 3건):
1. {키} — {제목}
2. {키} — {제목}
3. {키} — {제목}
```

### initiative-weekly 모드
```
✅ 이니셔티브 위클리 업데이트 완료! — {N}주차 ({YYYY-MM-DD})

📄 Confluence 위클리 문서 업데이트
   → {WEEKLY_DOC_URL}

📋 Jira {JIRA_KEY} — Weekly 공유사항 업데이트
   → {JIRA_ISSUE_URL}
```

### weekly 모드
```
✅ Weekly Jira 코멘트 게시 완료! — {N}주차

✅ TM-XXXX — {이니셔티브명}
   → {Jira 코멘트 URL}
✅ TM-YYYY — {이니셔티브명}
   → {Jira 코멘트 URL}

📁 결과: pgm-agent-system/output/weekly_result_{YYYYMMDD}.json
```

### full 모드
```
✅ PGM 전체 파이프라인 완료! — {N}주차

[Flash Report]
📄 Markdown: pgm-agent-system/output/flash_{YYYYMMDD}.md
📝 Google Docs: {URL}
📧 Gmail 초안: {Draft ID}

[Meeting Minutes]
📋 Markdown: pgm-agent-system/output/meeting_minutes_{YYYYMMDD}.md
📝 Google Docs (회의록): {URL}
💬 Slack 요약: pgm-agent-system/output/slack_summary_{YYYYMMDD}.txt

[Weekly Jira 코멘트]
✅ TM-XXXX — {이니셔티브명} → {URL}
✅ TM-YYYY — {이니셔티브명} → {URL}

📢 Slack 아젠다 미리보기:
{slack_summary 첫 4줄}
```

---

## 문서 작성 원칙 (Writing Rules)

→ `CONVENTIONS.md §4` 참조

### WR-1: Health Status 표기 (보고서 최상단)

```
| 전체 상태 | 🟢 정상 진행 | 계획 대비 차질 없음 |
```

### WR-2: Task 완료율 — 현재+차주 형식

```
현재: {N}개 중 {n}개 완료 ({%}) — {상태 한 줄}
차주 예상: {n+x}개 완료 (+{x}개) — {완료 예정 Task 간략 서술}
```

### WR-3: 이슈·블로커 — 담당/기한/액션 형식

```
| 이슈 | 현재 상태 | 필요 조치 | 담당 | 기한 |
```

### WR-4: 맥락 없는 섹션 추가 금지

새 섹션 추가 시 첫 줄에 "왜 이 내용이 이 문서에 있는지" 한 문장 설명.

### WR-5: 진행 중 Task에 차주 예상 진척률 표기

```
| 항목 | 담당 | 예상 Due | 차주 예상 진척 |
```

---

## 오류 처리

→ `CONVENTIONS.md §3` 참조

| 추가 오류 | 처리 방법 |
|----------|----------|
| Initiative 키 없음 (weekly) | 회의록에서 TM-XXXX 미발견 시 사용자에게 직접 입력 요청 |
| 항목이 너무 많음 (10개+) | "항목이 많습니다. 핵심 항목만 포함할까요?" 확인 |
| 특정 티켓 게시 실패 | 해당 티켓 skip + 결과에 오류 표시, 나머지 계속 |
