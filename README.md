# PM Studio

> **AI Native PM을 지향한다.**
> AI가 드래프트를 생성하고, PM은 판단을 내린다.

---

## AI Native PM이란 무엇인가

전통적인 PM은 도구를 *수동으로 조작*한다. 문서를 열고, 템플릿을 채우고, 검색하고, 정리한다.
AI Native PM은 다르게 일한다. **에이전트에게 문맥을 주고 초안을 위임한 뒤, 판단과 방향 결정에 집중한다.**

이 전환의 핵심은 단순한 자동화가 아니다. *PM의 인지 자원을 어디에 쓸 것인가*의 재배분이다.

```
전통적 PM        →    AI Native PM
──────────────────────────────────────────────
문서 작성 (2h)   →    에이전트 초안 → 검토·수정 (30m)
Confluence 검색  →    자연어 질문 → 인사이트 요약 수신
티켓 분해 (1h)   →    에픽 입력 → 티켓 목록 수신 → 우선순위 결정
GTM 브리프 (3h)  →    PRD 입력 → 브리프 생성 → 메시지 판단
```

---

## AI Native PM의 5가지 작동 원칙

### 1. Prompt-First Thinking — 빈 문서가 아닌 에이전트로 시작한다

작업을 시작할 때 새 문서를 열지 않는다.
에이전트에게 요청하면 초안이 나온다. PM의 역할은 그 초안을 *판단하고 방향을 잡는 것*이다.

### 2. Draft Fast, Judge Slow — AI가 빠르게, PM은 깊게

에이전트는 빠르다. 초안 생성, 대안 작성, 형식 변환은 에이전트에게 맡긴다.
PM은 *왜 이 방향인가*, *무엇을 빠뜨렸는가*, *고객에게 맞는가*를 판단하는 데 시간을 쓴다.

### 3. Context as Assets — 컨텍스트를 파일로 축적한다

에이전트의 품질은 컨텍스트의 품질에 비례한다.
이니셔티브 배경(`context.md`), 의사결정 로그(`decisions.md`), 참조 문서(`references.md`)를 구조화해서 쌓는다.
쌓인 컨텍스트가 다음 작업을 더 잘 지원한다 — **지식 플라이휠**.

### 4. Agents as Teammates — 에이전트는 팀원이다

에이전트는 버튼이 아니다. *역할이 있고, 기대 산출물이 있고, 검증 기준이 있는* 팀원으로 다룬다.
각 에이전트에게 명확한 역할을 주고, 결과물을 검토하고, 피드백 루프를 구성한다.

### 5. Human-in-the-Loop — 전략과 판단은 PM의 영역이다

AI가 빠른 초안을 만들더라도, 아래 영역은 반드시 PM이 직접 판단한다:
- 기회 우선순위 결정 (무엇을 만들 것인가)
- 고객 인터뷰 설계와 인사이트 해석
- 스테이크홀더 설득과 관계 관리
- 비즈니스 전략과 연계한 최종 방향 결정

---

## PM 워크플로우 × AI 분업 지도

PM의 일반적인 6단계 워크플로우에서 이 시스템이 어떤 역할을 하는지 정리한다.

```
┌─────────────────────────────────────────────────────────────────┐
│  PM 워크플로우                AI 처리 영역        인간 판단 영역  │
├──────────────┬───────────────────────────┬──────────────────────┤
│  1. Discover │ Confluence 검색·요약       │ 인터뷰 설계           │
│  (탐색)      │ 앱푸시 성과 분석           │ 인사이트 해석         │
│              │ 타 부서 문서 탐색          │ 기회 정의             │
│              │ 외부 벤더 레퍼런스 수집    │                      │
├──────────────┼───────────────────────────┼──────────────────────┤
│  2. Define   │ North Star / KPI 초안 제안 │ 지표 최종 결정        │
│  (정의)      │ 이니셔티브 컨텍스트 로드   │ 성공 기준 합의        │
│              │                           │ 우선순위 판단         │
├──────────────┼───────────────────────────┼──────────────────────┤
│  3. Design   │ PRD 초안 생성             │ 방향 결정 및 수정     │
│  (설계)      │ UX 플로우 + 정책 작성     │ 엣지 케이스 검토      │
│              │ Red Team 검증 질문 생성    │ 기술 협의 및 조율     │
│              │ UX 카피 작성              │ 최종 PRD 승인         │
├──────────────┼───────────────────────────┼──────────────────────┤
│  4. Develop  │ 에픽 → 스토리 분해        │ 스프린트 우선순위     │
│  (개발)      │ Jira 티켓 포맷팅          │ 엔지니어링 협상       │
│              │ 요구사항 P0/P1 분류       │ 범위 조율             │
├──────────────┼───────────────────────────┼──────────────────────┤
│  5. Launch   │ GTM 브리프 생성           │ 출시 전략 결정        │
│  (출시)      │ Before/After 정리         │ 채널 우선순위         │
│              │ 롤아웃 플랜 설계           │ 스테이크홀더 커뮤니케이션│
│              │ Launch Metrics 설정        │ 타이밍 판단           │
├──────────────┼───────────────────────────┼──────────────────────┤
│  6. Learn    │ Confluence 문서 자동 저장  │ 회고 방향 설정        │
│  (학습)      │ 이니셔티브 decisions 기록  │ 다음 이니셔티브 연결  │
│              │ 성과 리포트 요약           │ 전략적 교훈 도출      │
│              │ C레벨 보고서 품질 검토     │                      │
└──────────────┴───────────────────────────┴──────────────────────┘
```

---

## 전체 에이전트 워크플로우 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            PM Studio — 전체 에이전트 맵                              │
└─────────────────────────────────────────────────────────────────────────────────────┘

PM 입력 (슬래시 명령어 or 자연어)
         │
         ├──/discovery──────────────────────────────────────────────┐
         │                                                          │
         │  [PDIS: Product Discovery Intelligence System]           │
         │                                                          │
         │  Phase 0 (--ref 옵션 시): discovery-analyst              │
         │    ├─ fetch_amplitude.py → Amplitude GitHub Docs         │
         │    ├─ fetch_braze.py     → Braze GitHub Docs             │
         │    └─ search_shopify.py  → Shopify App Store             │
         │    └─▶ ext_summary_{날짜}_{주제}.md                      │
         │                                                          │
         │  Phase 1: market-analyst                                 │
         │    ├─ 경쟁사 분석 + 기능 매트릭스                         │
         │    ├─ TAM/SAM/SOM (Conservative/Optimistic)              │
         │    └─▶ output/market-intel.md                            │
         │                                                          │
         │  Phase 2: market-analyst (페르소나)                      │
         │    └─▶ personas/P0{N}.json                               │
         │                                                          │
         │  Phase 3: user-simulator (페르소나별)                    │
         │    └─▶ simulated-interviews/{id}_interview.md            │
         │                                                          │
         │  Phase 4: insight-synthesizer                            │
         │    ├─ Pain Points 클러스터링                              │
         │    ├─ JTBD 분류                                          │
         │    └─▶ output/discovery-synthesis.md                     │
         │                                                          │
         │  Phase 5: 오케스트레이터 직접                             │
         │    └─▶ output/FINAL-DISCOVERY-REPORT.md ─────────────────┘
         │
         ├──/prd────────────────────────────────────────────────────┐
         │                                                          │
         │  [Strategic PRD Builder]                                 │
         │                                                          │
         │  Phase 1: 전략 지표 수립 (HITL)                          │
         │    └─▶ North Star + KPI 초안 → PM 확정                   │
         │                                                          │
         │  Phase 2: requirement-writer + ux-logic-analyst          │
         │    ├─▶ P0/P1 기능 요구사항                               │
         │    └─▶ Mermaid 플로우 + 정책 + 예외케이스                │
         │                                                          │
         │  Phase 2.5: diagram-generator                            │
         │    └─▶ render.py → output/diagrams/*.html                │
         │                                                          │
         │  Phase 3: Self-Review (6개 체크)                         │
         │                                                          │
         │  Phase 4: red-team-validator (/red로도 단독 실행 가능)   │
         │    └─▶ output/redteam_{날짜}_{주제}.md                   │
         │                                                          │
         │  Phase 5: Confluence 자동 업로드                         │
         │    └─▶ PRD + Red Team 2개 페이지 ──────────────────────┐  │
         │                                                       │  │
         ├──/jira─────────────────────────────────────────────────┼──┘
         │                                                        │
         │  [jira-creator Agent]                                  │
         │    자연어 요청 → 참조 티켓 조회 (선택)                   │
         │    → 생성 예정 목록 표 정리 → 사용자 컨펌                │
         │    → create_jira_{이니셔티브}_{날짜}.py 실행             │
         │    └─▶ output/created_{이니셔티브}_tickets.json          │
         │                                                        │
         ├──/mail─────────────────────────────────────────────────┘
         │
         │  [doc-specialist → mail-specialist]
         │    Confluence URL/PageID → doc-specialist
         │      └─▶ output/weekly_flash_v1.md + source_page.xhtml
         │    → mail-specialist: xhtml_to_email_html.py / md_to_html.py
         │    → 사용자 승인 → send_email.py
         │    └─▶ output/send_log.json
         │
         ├──/epic ────────────────────────────────────────────────┤  │
         │                                                       │  │
         │  [Epic Architect]                                     │  │
         │    PRD (Confluence URL or .md) ────────────────────────┘  │
         │    + Jira 이니셔티브 키                                    │
         │                                                          │
         │  Phase 1: epic-architect                                 │
         │    ├─ BE/FE/MLE/DS 직무별 에픽 분리                      │
         │    ├─ AC·우선순위·Start/Due Date 계산                    │
         │    ├─▶ epic_spec_{날짜}_{주제}.json                      │
         │    └─▶ Confluence [Draft] Epic Specification (HITL)     │
         │                                                          │
         │  Phase 2: jira-skill (컨펌 후 실행)                      │
         │    ├─ fetch_initiative.py: 라벨·컴포넌트 추출            │
         │    ├─ create_tickets.py: 에픽 티켓 일괄 생성              │
         │    └─▶ output/jira_result_{날짜}_{주제}.json ────────────┘
         │
         ├──/gtm────────────────────────────────────────────────────┐
         │                                                          │
         │  [GTM Agent System]                                      │
         │    input/prd_*.md                                        │
         │                                                          │
         │  message-architect                                       │
         │    └─▶ messaging_draft.json (One-liner, Key Message 등)  │
         │                                                          │
         │  channel-planner                                         │
         │    └─▶ strategy_draft.json (Before/After, 롤아웃 등)     │
         │                                                          │
         │  brief-formatter                                         │
         │    └─▶ GTM_Brief_{날짜}_{주제}.md ────────────────────────┘
         │
         ├──/report─────────────────────────────────────────────────┐
         │                                                          │
         │  [C레벨 Report Quality System]                           │
         │    보고서 파일 or Confluence URL                          │
         │                                                          │
         │  report-red-team                                         │
         │    ├─ 9개 원칙 기반 피드백 (A~I)                         │
         │    │   A. 두괄식 구조  B. Executive Summary               │
         │    │   C. 숫자/근거   D. Ask 명확성   E. MECE            │
         │    │   F. So What    G. 반론 선제     H. 독자관점+정보계층│
         │    │   I. 실행가능성                                      │
         │    ├─▶ 피드백 테이블 (🔴/🟡/🟢 우선순위)                  │
         │    ├─▶ 수정 제안                                          │
         │    ├─▶ 종합 판정 (즉시결재/질문후결재/반려가능)            │
         │    └─▶ report-agent-system/output/report_review_*.md     │
         │        + Confluence 자동 업로드 (하위 페이지) ────────────┘
         │
         ├──/pgm────────────────────────────────────────────────────┐
         │                                                          │
         │  [Weekly Flash Report System]                            │
         │    Jira 프로젝트 키 + 사용자 메모                         │
         │                                                          │
         │  Step 1: jira-parser 스킬                                │
         │    └─▶ output/jira_raw_{날짜}.json                       │
         │                                                          │
         │  Step 2: analyst 서브에이전트                             │
         │    └─▶ output/analysed_report.json                       │
         │                                                          │
         │  Step 3: publisher + minutes-generator (병렬)             │
         │    publisher:                                            │
         │      ├─▶ output/flash_{날짜}.md                          │
         │      ├─▶ Google Docs 초안 URL                            │
         │      └─▶ Gmail 초안 ID                                   │
         │    minutes-generator:                                    │
         │      ├─▶ output/meeting_minutes_{날짜}.md                │
         │      ├─▶ Google Docs 회의록 초안 URL                     │
         │      └─▶ output/slack_summary_{날짜}.txt                 │
         │                                                          │
         │  Step 4: Self-Validation (12개 항목) ────────────────────┘
         │
         └──(자연어 요청)────────────────────────────────────────────┐
                                                                    │
            [Confluence Intelligence Agent] (루트 CLAUDE.md)        │
              조회(Read): confluence-reader                          │
                └─▶ output/context.json → 인사이트 요약              │
              업로드(Write): confluence-writer                       │
                └─▶ output/draft.html → Confluence 페이지 URL ───────┘

                              ↕ (모든 시스템 공통)
                    input/initiatives/ 컨텍스트 공유
                    (context.md, decisions.md, references.json)
```

---

## AI Native PM으로 일하기 — 상황별 에이전트 활용 가이드

### 상황 1: "이 이슈, 우리 팀에서 다룬 적 있어?"

```
에이전트: Confluence Intelligence Agent (루트)
입력: "앱푸시 리텐션 관련 분석 찾아줘"
출력: 관련 문서 3건 + 핵심 인사이트 요약
소요: 1~2분
```

**활용 패턴:** 회의 전 사전 조사, 이슈 히스토리 파악, 타 팀 문서 탐색 시 사용.

---

### 상황 2: "시장을 먼저 파악하고 싶어"

```
에이전트: Product Discovery Intelligence System (/discovery)
입력: /discovery 리텐션 마케팅 전략 탐색 --ref all
출력: 외부 벤더 레퍼런스(Amplitude/Braze) + 시장 분석 + 가상 인터뷰 + 최종 보고서
소요: 4~6시간 (에이전트 런 기준)
```

**활용 패턴:**
1. `--ref all` 옵션으로 업계 최고 툴 접근 방식 먼저 파악
2. 시장 분석 → 페르소나 → 가상 인터뷰로 디스커버리 전체 커버
3. 최종 보고서를 PRD 입력으로 재사용

---

### 상황 3: "아이디어가 있는데 PRD를 써야 해"

```
에이전트: Strategic PRD Builder (/prd)
입력: Rough Note (자유 형식 아이디어 메모)
출력: PRD 초안 + Red Team 검증 질문지 + Confluence 자동 업로드
소요: 10~20분
```

**활용 패턴:**
1. 아이디어를 자유 형식으로 입력 (불완전해도 됨)
2. 에이전트가 North Star / KPI 초안을 제안 → PM이 지표 확정
3. 기능 요구사항 + 플로우 초안 수신 → 검토 및 수정
4. Red Team 질문 수신 → 빠뜨린 엣지 케이스 확인

---

### 상황 4: "기존 PRD를 Red Team 검증만 다시 하고 싶어"

```
에이전트: red-team-validator (/red)
입력: prd 파일 경로 또는 최근 PRD 자동 선택
출력: 30개+ 비판 질문 + 취약점 분류 + 개선 제안
소요: 5~10분
```

---

### 상황 5: "PRD 승인났는데, 티켓을 써야 해"

```
에이전트: Epic Architect (/epic)
입력: PRD 또는 에픽 설명
출력: P0/P1 기준 분해된 Jira 티켓 목록 + 포맷팅
소요: 5~10분
```

**활용 패턴:** PRD의 기능 요구사항을 입력하면 스토리/태스크 단위로 분해. PM은 우선순위와 담당자 배정에 집중.

---

### 상황 6: "런칭 전, 마케터에게 줄 GTM 브리프가 필요해"

```
에이전트: GTM Agent System (/gtm)
입력: PRD 파일 (prd_*.md)
출력: GTM_Brief_*.md (One-liner / Before-After / Key Message / 롤아웃 / Launch Metrics)
소요: 5~10분
```

**활용 패턴:**
1. `gtm-agent-system/input/`에 PRD 파일 배치
2. 에이전트가 마케팅 언어로 변환 (기술 용어 자동 제거)
3. PM이 One-liner와 Key Message 최종 검토 후 확정

---

### 상황 7: "오늘 회의 내용, Confluence에 남겨야 해"

```
에이전트: Confluence Intelligence Agent (루트)
입력: "오늘 대화 내용 정리해서 Confluence에 올려줘"
출력: XHTML 변환 → Confluence 자동 업로드 → 페이지 URL 반환
소요: 2~3분
```

**활용 패턴:** 회의 직후 대화 내용 입력 → 에이전트가 문서 구조화 + 업로드.

---

### 상황 8: "C레벨 보고서 올리기 전에 품질 검토가 필요해"

```
에이전트: C레벨 Report Quality System (/report)
입력: 보고서 파일 경로 또는 Confluence URL
출력: 9개 원칙 기반 피드백 + 수정 제안 + 종합 판정 + Confluence 업로드
소요: 5~10분
```

**활용 패턴:**
1. 보고서 초안 완성 후 `/report [파일경로]` 실행
2. 🔴 Critical 항목 우선 수정
3. 종합 판정 "즉시 결재 가능" 상태로 올리기

---

### 상황 9: "이번 주 진행 현황을 팀장/C레벨에게 공유해야 해"

```
에이전트: Weekly Flash Report System (/pgm)
입력: /pgm MATCH 이번 주 추가할 메모 내용
출력: output/flash_{날짜}.md + Google Docs 초안 URL + Gmail 초안 ID
소요: 3~5분
```

**활용 패턴:**
1. Jira 프로젝트 키와 보충 메모를 함께 입력
2. analyst가 Done/In Progress/Blocked 티켓을 자동 분류 및 우선순위 판단
3. publisher가 Markdown + Google Docs + Gmail 초안 3종 동시 생성
4. Gmail 초안을 열어 수신자 추가 후 발송

---

## 슬래시 커맨드 전체 목록

| 커맨드 | 에이전트 시스템 | 핵심 기능 |
|--------|--------------|----------|
| `/discovery` | PDIS | 시장 탐색 + 가상 인터뷰 + 디스커버리 보고서 |
| `/prd` | Strategic PRD Builder | Rough Note → PRD + Red Team + Confluence 업로드 |
| `/red` | red-team-validator | PRD 단독 Red Team 검증 |
| `/epic` | Epic Architect | PRD → Jira 에픽 티켓 자동 생성 |
| `/jira` | jira-creator | 자연어 → Jira 티켓 일괄 생성 (컨펌 후 실행) |
| `/gtm` | GTM Agent System | PRD → GTM 브리프 생성 |
| `/report` | C레벨 Report Quality System | 보고서 품질 검토 + 종합 판정 |
| `/pgm` | Weekly Flash Report System | Jira + 메모 → 주간 보고서 + 회의록 + Slack 요약 |
| `/mail` | mail-specialist + doc-specialist | Confluence / MD → Gmail 발송 |

---

## 이니셔티브 컨텍스트 관리 — 지식 플라이휠 구성법

AI Native PM의 핵심 습관은 **컨텍스트를 파일로 남기는 것**이다.
에이전트는 `input/initiatives/` 폴더를 자동으로 참조하며, 축적된 컨텍스트일수록 더 정확한 초안을 생성한다.

> **참고**: `input/` 폴더는 gitignore 처리되어 있습니다. 이니셔티브 컨텍스트는 로컬에서만 관리됩니다.

### 이니셔티브 시작 시 해야 할 일

```bash
# 1. 템플릿 복사
cp -r input/initiatives/_template input/initiatives/2026Q1/TM-xxxx

# 2. meta.json — 티켓 ID, 상태, 기간, 관련 Confluence Space 입력
# 3. context.md — 배경, 목표, 핵심 가설, 성공 지표 작성
# 4. input/initiatives/index.md 테이블에 행 추가
```

### 이니셔티브 진행 중 유지할 파일

| 파일 | 업데이트 시점 | 내용 |
|------|-------------|------|
| `context.md` | 방향이 바뀔 때마다 | 배경·목표·핵심 가설 변경 이력 |
| `decisions.md` | 의사결정 직후 | 결정 내용, 배경, 대안, 결과 |
| `references.md` | 문서/슬랙 링크 생길 때마다 | Confluence URL, Jira 링크 |
| `output/` | 산출물 생성 시 | PRD, GTM 브리프, 분석 결과 |

**원칙:** 에이전트에게 "이번 TM-2061 관련해서 PRD 써줘"라고 하면, `context.md`를 읽고 배경을 이해한 상태에서 작업을 시작한다.

---

## 에이전트 모델 정책

각 에이전트는 작업 특성에 따라 최적 모델을 개별 지정한다. 지정이 없는 에이전트는 오케스트레이터(Sonnet 4.6)를 상속한다.

| 에이전트 | 모델 | 지정 방식 | 근거 |
|---------|------|---------|------|
| `confluence-reader` | Sonnet 4.6 | 상속 (기본값) | 토픽 라우팅·요약 판단 필요 |
| `confluence-writer` | **Haiku 4.5** | AGENT.md 프론트매터 | XHTML 변환·포맷팅 위주, 판단 불필요 |
| `requirement-writer` | Sonnet 4.6 | 상속 (기본값) | P0/P1 분류 전략적 판단 필요 |
| `ux-logic-analyst` | Sonnet 4.6 | 상속 (기본값) | 플로우·정책 설계 복잡도 있음 |
| `red-team-validator` | Sonnet 4.6 | AGENT.md 프론트매터 | 비판적 질문 생성, 필요 시 Opus 사용 가능 |
| `report-red-team` | Sonnet 4.6 | AGENT.md 프론트매터 | C레벨 보고서 품질 판단, 높은 정확도 필요 |
| `message-architect` (GTM) | Sonnet 4.6 | 상속 (기본값) | One-liner·카피 창작 |
| `channel-planner` (GTM) | Sonnet 4.6 | 상속 (기본값) | Before/After·롤아웃 전략 판단 |
| `epic-decomposer` | Haiku 4.5 | AGENT.md 추가 예정 | 기계적 스토리 분해·포맷팅 |
| `ticket-formatter` | Haiku 4.5 | AGENT.md 추가 예정 | 순수 포맷팅, 가장 단순한 작업 |
| `discovery-analyst` | Sonnet 4.6 | AGENT.md 프론트매터 | 벤더 문서 분석·인사이트 합성 |
| `market-analyst` | Sonnet 4.6 | 상속 (기본값) | 시장 분석·페르소나 생성 판단 필요 |
| `user-simulator` | Sonnet 4.6 | 상속 (기본값) | 페르소나 역할극, 다양한 시각 필요 |
| `insight-synthesizer` | Sonnet 4.6 | 상속 (기본값) | JTBD·OST 도출 복잡도 있음 |

**모델 지정 방법** — AGENT.md 최상단에 YAML 프론트매터 추가:
```yaml
---
model: claude-sonnet-4-6            # Sonnet 4.6 (기본값)
# model: claude-opus-4-6           # Opus 4.6 (명시적으로 요청 시만)
# model: claude-haiku-4-5-20251001  # Haiku 4.5
---
```

---

## 현재 이 시스템으로 할 수 있는 것

### 시스템 구성 전체 지도

```
pm-studio/
├── CLAUDE.md                        ← 루트 오케스트레이터 (Confluence Intelligence Agent)
├── README.md                        ← 이 파일
├── SKILL_README.md                  ← 스킬 레퍼런스 (사용 가능한 기술 목록)
├── config/
│   └── spaces.json                  ← Confluence Space 키 매핑 및 토픽 라우팅
├── input/                           ← 외부 입력 자료 (gitignore) — hld/ meetings/ refs/ data/
├── Rough Notes/                     ← 빠른 메모·아이디어 초안 (gitignore)
├── initiatives/
│   ├── index.md                     ← 분기별 이니셔티브 현황 인덱스
│   ├── _template/                   ← 이니셔티브 추가용 템플릿 (input/ 포함)
│   ├── _kb/                         ← 지식 베이스 (Jira 티켓 없는 참조 문서)
│   └── 2026Q1/                      ← Q1 이니셔티브 (각 폴더에 input/ + output/ 포함)
├── .claude/
│   ├── agents/
│   │   ├── confluence-reader/       ← Confluence 검색·요약 (루트 오케스트레이터 서브에이전트)
│   │   ├── confluence-writer/       ← Confluence 업로드 (루트 오케스트레이터 서브에이전트)
│   │   ├── doc-specialist/          ← Confluence 페이지 → Weekly Flash 마크다운 추출 (/mail)
│   │   ├── jira-creator/            ← 자연어 → Jira 티켓 일괄 생성 (/jira)
│   │   └── mail-specialist/         ← MD/XHTML → Gmail HTML 변환 + 발송 (/mail)
│   └── skills/
│       ├── confluence-tool/         ← Confluence API 공통 스크립트
│       ├── gmail-tool/              ← Gmail SMTP 발송 스크립트
│       ├── discovery/               ← /discovery 스킬
│       ├── prd/                     ← /prd 스킬
│       ├── red/                     ← /red 스킬
│       ├── epic/                    ← /epic 스킬
│       ├── jira/                    ← /jira 스킬 [NEW]
│       ├── gtm/                     ← /gtm 스킬
│       ├── report/                  ← /report 스킬
│       ├── pgm/                     ← /pgm 스킬
│       └── mail/                    ← /mail 스킬 [NEW]
├── output/                          ← 공통 산출물 (context.json, draft.html, 로그)
├── prd-agent-system/                ← PRD 자동 생성 에이전트 시스템
│   └── .claude/agents/
│       ├── requirement-writer/
│       ├── ux-logic-analyst/
│       ├── diagram-generator/
│       └── red-team-validator/      ← /red 단독 실행 가능
├── epic-ticket-system/              ← PRD → 에픽 분해 + Jira 티켓 자동 생성
├── gtm-agent-system/                ← GTM 브리프 자동 생성 에이전트 시스템
│   └── .claude/agents/
│       ├── message-architect/
│       ├── channel-planner/
│       └── brief-formatter/
├── ux-copywriter-system/            ← UX 카피라이팅 에이전트 시스템
├── report-agent-system/             ← C레벨 보고서 품질 검토 시스템
│   ├── CLAUDE.md                    ← 보고서 리뷰 오케스트레이터
│   ├── references/
│   │   └── report_principles.md    ← 9개 C레벨 보고서 품질 원칙
│   └── .claude/agents/
│       └── report-red-team/        ← 보고서 비판·피드백 에이전트
├── pgm-agent-system/                ← [NEW] Weekly Flash Report 시스템
│   ├── CLAUDE.md                    ← Flash Report 오케스트레이터
│   ├── config.json                  ← 프로젝트·채널 설정
│   ├── input/                       ← 사용자 메모 임시 저장
│   ├── output/                      ← 생성된 리포트 저장
│   └── .claude/
│       ├── agents/
│       │   ├── analyst/             ← Jira 데이터 분류·우선순위 판단
│       │   └── publisher/           ← MD/Docs/Gmail 3종 포맷 변환
│       ├── agents/
│       │   ├── analyst/             ← Jira 데이터 분류·우선순위 판단
│       │   ├── publisher/           ← MD/Docs/Gmail 3종 포맷 변환
│       │   └── minutes-generator/   ← [NEW] 아젠다 선별 + 회의록 + Slack 요약
│       └── skills/
│           ├── jira-parser/         ← Jira API 티켓 수집
│           ├── google-api-handler/  ← Google Docs·Gmail 초안 생성
│           ├── slack-notifier/      ← [NEW] Slack Webhook 전송
│           └── file-generator/      ← Markdown 파일 생성
└── discovery-intelligence-system/  ← [ENHANCED] PDIS + External Knowledge Connector
    ├── CLAUDE.md                    ← Lead Researcher 오케스트레이터
    ├── scripts/                     ← [NEW] 외부 데이터 수집 스크립트
    │   ├── fetch_amplitude.py       ← Amplitude GitHub Docs 수집
    │   ├── fetch_braze.py           ← Braze GitHub Docs 수집
    │   └── search_shopify.py        ← Shopify App Store 벤치마크
    ├── references/
    │   ├── vendor_endpoints.json    ← [NEW] 벤더 라우팅 규칙
    │   ├── jtbd_guide.md
    │   ├── ost_guide.md
    │   └── discovery_report_template.md
    ├── personas/
    ├── simulated-interviews/
    └── .claude/agents/
        ├── discovery-analyst/       ← [NEW] External Knowledge Connector
        ├── market-analyst/
        ├── user-simulator/
        └── insight-synthesizer/
```

---

### 에이전트 시스템 1: Confluence Intelligence Agent

**위치:** 루트 `CLAUDE.md`
**핵심 기능:** Confluence를 자연어로 검색하고, 대화 내용을 문서화한다.

| 입력 | 처리 | 출력 |
|------|------|------|
| "앱푸시 성과 찾아줘" | 토픽 감지 → Space 자동 선택 → 검색 | 관련 문서 + 인사이트 요약 |
| "오늘 대화 Confluence에 올려줘" | XHTML 변환 → 중복 체크 → 업로드 | Confluence 페이지 URL |

**서브 에이전트:**
- `confluence-reader` — 키워드 추출 → Space 라우팅 → 검색 → 상위 3건 요약
- `confluence-writer` — Storage Format 변환 → 포맷 검증 → 업로드 (2회 재시도)
- `doc-specialist` — Confluence 페이지 → Weekly Flash 마크다운 추출 (`/mail` 경유 또는 직접 호출)
- `jira-creator` — 자연어 요청 → Jira 티켓 일괄 생성 (`/jira` 경유 호출)
- `mail-specialist` — 마크다운 / XHTML → Gmail 발송 HTML 변환 + SMTP 발송 (`/mail` 경유 호출)

**Space 자동 라우팅:** 질문 키워드에 따라 탐색 Space가 자동 결정된다.

| 질문 키워드 예시 | 추가 탐색 Space |
|----------------|--------------|
| 그로스, 리텐션, CRM, 캠페인 | `retentionmarketing` → `LTV` → `GP` |
| 추천, 개인화, 피드, 랭킹 | `29CMRec` |
| 29CM, 이구, 29씨엠 | `29PRODUCT` → `2CEE` → `29CMTECH` |
| (모든 질문 공통) | `membership` → `PE` → 개인 Space |

---

### 에이전트 시스템 2: Product Discovery Intelligence System (PDIS)

**위치:** `discovery-intelligence-system/`
**핵심 기능:** 2주 소요되던 디스커버리 과정을 4~6시간의 에이전트 런으로 단축.

**[NEW] Phase 0 — External Knowledge Connector (discovery-analyst)**

```
탐색 주제 분석
    ↓
벤더 라우팅 (vendor_endpoints.json routing_rules 기반)
    ├── Amplitude → fetch_amplitude.py → GitHub Docs 수집
    ├── Braze    → fetch_braze.py     → GitHub Docs 수집
    └── Shopify  → search_shopify.py  → App Store 벤치마크
    ↓
ext_summary_{날짜}_{주제}.md (Phase 1 시장 분석 입력으로 전달)
```

**Phase 1~5 — 기존 워크플로우**

```
Phase 1: market-analyst → output/market-intel.md
Phase 2: market-analyst → personas/P0{N}.json
Phase 3: user-simulator → simulated-interviews/{id}_interview.md
Phase 4: insight-synthesizer → output/discovery-synthesis.md
Phase 5: 오케스트레이터 → output/FINAL-DISCOVERY-REPORT.md
```

**외부 참조 옵션:**
```bash
/discovery 리텐션 전략 탐색 --ref all        # 전체 벤더 자동 선택
/discovery 푸시 알림 개선 --ref braze        # Braze만
/discovery 커머스 앱 분석 --ref shopify      # Shopify App Store만
/discovery 퍼널 분석 기회 (옵션 없음)        # Phase 0 스킵
```

---

### 에이전트 시스템 3: Strategic PRD Builder

**위치:** `prd-agent-system/`
**핵심 기능:** Rough Note → 전략 지표 수립 → 기능 요구사항 → UX 플로우 → Red Team 검증 → Confluence 업로드.

```
Rough Note (자유 형식)
    ↓
Phase 1: North Star + KPI 초안 제안 → PM 확정
    ↓
Phase 2: 서브 에이전트 순차 실행
    ├── requirement-writer: P0/P1 기능 요구사항
    └── ux-logic-analyst: Mermaid 플로우 + 정책 + 예외케이스
    ↓
Phase 2.5: 다이어그램 시각화 (diagram-generator)
    └── .mmd 저장 → render.py → output/diagrams/*.html
    ↓
Phase 3: 통합 + Self-Review (6개 항목 체크)
    ↓
Phase 4: Red Team Validation (30개 이상 비판 질문)
    ↓
Confluence 자동 업로드: PRD + Red Team 질문지 2개 문서
```

**주요 산출물:**
- `output/prd_{YYYYMMDD}_{주제}.md` — 완성된 PRD
- `output/redteam_{YYYYMMDD}_{주제}.md` — Red Team 검증 질문지
- `output/diagrams/*.html` — 브라우저에서 바로 열리는 Mermaid 플로우 시각화
- Confluence 페이지 2개 (자동 업로드)

---

### 에이전트 시스템 4: Epic Architect (개발 실행 연동)

**위치:** `epic-ticket-system/`
**핵심 기능:** 완성된 PRD를 직무별(BE/FE/MLE/DS) 에픽으로 분해하고,
Confluence 초안 문서를 자동 생성한 뒤 개발자 컨펌 후 Jira 에픽 티켓을 자동 생성한다.

**데이터 흐름:**
```
PRD (Confluence URL or .md)  +  Jira 이니셔티브 키
    ↓
[Phase 1] epic-architect 에이전트
    → 직무별 에픽 분리 (BE/FE/MLE/DS)
    → AC·우선순위·Start/Due Date 계산 (dependency_rules.md 참조)
    → epic_spec_{날짜}_{주제}.json 저장
    → Confluence에 [Draft] Epic Specification 하위 페이지 자동 생성
    ↓ 사용자 컨펌 ("실행" 입력)
[Phase 2] jira-skill 스크립트
    → fetch_initiative.py: 부모 이니셔티브 라벨·컴포넌트 추출
    → create_tickets.py: 에픽 티켓 일괄 생성 (라벨 상속 + 직무 라벨 추가)
    → Jira 티켓 URL 목록 출력
```

**주요 산출물:**
- Confluence: `[Draft] {주제} Epic Specification` (PRD 하위 페이지)
- Jira: 에픽 티켓 N개 (라벨 자동 상속, Start/Due Date 포함)
- `output/epic_spec_{날짜}_{주제}.json` — 에픽 명세 JSON
- `output/jira_result_{날짜}_{주제}.json` — 생성된 Jira 티켓 URL

**추가 환경변수 필요:**
```bash
export JIRA_PROJECT_KEY="TM"   # Jira 프로젝트 키
```

---

### 에이전트 시스템 5: GTM Agent System

**위치:** `gtm-agent-system/`
**핵심 기능:** PRD를 입력하면 마케터가 즉시 사용 가능한 GTM 브리프를 생성한다.

**데이터 흐름:**
```
input/prd_*.md
    → [메인 오케스트레이터] PRD 파싱 → prd_parsed.json
    → [message-architect]  One-liner / 페르소나 Pain-point / Key Message → messaging_draft.json
    → [channel-planner]    Before/After / 범위 / 롤아웃 / Launch Metrics → strategy_draft.json
    → [brief-formatter]    JSON 2개 + 템플릿 결합 → GTM_Brief_{YYYYMMDD}_{주제}.md
```

**산출물 8개 섹션:** One-liner · Target User · Before/After · Key Message · What's in/out · Rollout Plan · Enablement · Launch Metrics

**핵심 제약 (자동 검증):**
- One-liner 50자 이하 + 시스템명 금지
- Before/After에 수치 또는 Step 수 변화 필수
- Phase 1 / Phase 2 범위 명확히 분리

---

### 에이전트 시스템 6: UX Copywriter System

**위치:** `ux-copywriter-system/`
**핵심 기능:** 기능 설명을 입력하면 사용자 중심 UI 텍스트와 마이크로카피를 생성한다.

**서브 에이전트:**
- `message-architect` — 메시지 구조 설계 (톤, 계층, 맥락)
- `ui-text-writer` — 버튼 레이블, 안내문, 에러 메시지 등 실제 UI 텍스트 작성

---

### 에이전트 시스템 7: C레벨 Report Quality System

**위치:** `report-agent-system/`
**핵심 기능:** C레벨 보고를 위한 문서의 품질을 9개 원칙 기반으로 검토하고,
종합 판정(즉시 결재 가능 / 질문 후 결재 / 반려 가능성 있음)을 내린다.

---

### 에이전트 시스템 8: Weekly Flash Report System

**위치:** `pgm-agent-system/`
**핵심 기능:** Jira 티켓과 사용자 메모를 결합하여 핵심 성과 위주의 Weekly Flash Report를 생성하고,
Markdown / Gmail 초안 / Google Docs 초안 3가지 포맷으로 자동 배포(초안)한다.

**데이터 흐름:**
```
Jira 프로젝트 키 + 사용자 메모
    ↓
[Step 1] jira-parser 스킬
    → 이번 주 Done/In Progress/Blocked 티켓 수집
    → output/jira_raw_{YYYYMMDD}.json
    ↓
[Step 2] analyst 서브에이전트
    → 항목 분류 + 우선순위 판단 (⭐ 핵심 태그 포함)
    → output/analysed_report.json
    ↓
[Step 3] publisher 서브에이전트
    → output/flash_{YYYYMMDD}.md
    → Google Docs 초안 URL
    → Gmail 초안 ID
    ↓
[Step 4] Self-Validation (5개 체크)
    → 산출물 3종 완비 / 볼드 처리 / 명사형 어미 / 카테고리 4종 / 우선 항목 존재
```

**주요 산출물:**
- `output/flash_{YYYYMMDD}.md` — 로컬 마크다운 최종본
- Google Docs 초안 URL — 문서 링크 공유용
- Gmail 초안 ID — 이메일 발송 준비 완료
- `output/meeting_minutes_{YYYYMMDD}.md` — 회의록 초안 (minutes-generator)
- Google Docs 회의록 초안 URL — 회의록 공유용
- `output/slack_summary_{YYYYMMDD}.txt` — Slack 사전 아젠다 요약

**추가 환경변수 필요:**
```bash
export JIRA_API_TOKEN="..."          # Jira API 인증
export GOOGLE_CREDENTIALS_JSON="..." # Google Docs/Gmail OAuth 인증
```

**보고서 유형 지원:**
- 투자케이스 / 예산 승인 요청
- 전략 로드맵 / 계획 보고
- 현황 보고 / KPI 리뷰
- 제안 보고 / 신규 이니셔티브

**9개 검토 원칙 (references/report_principles.md):**

| 원칙 | 핵심 질문 |
|------|---------|
| A. 두괄식 구조 | 첫 문단만 읽고 결재 판단이 가능한가? |
| B. Executive Summary | 요약만으로 보고서 전체를 대체할 수 있는가? |
| C. 숫자와 근거 | 모든 주장에 수치와 측정 방법이 있는가? |
| D. Ask 명확성 | 하나의 명확한 요청(무엇/기한/자원)이 있는가? |
| E. MECE 완결성 | 분류 체계가 겹치지 않고 전체를 포함하는가? |
| F. So What 연결 | 모든 데이터 뒤에 시사점이 명시되는가? |
| G. 반론 선제 처리 | C레벨의 예상 질문 3가지를 먼저 답하는가? |
| H. 독자 관점 + 정보 계층 | 전략 → 계획 → 세부사항 순서로 배치되는가? |
| I. 실행 가능성 | 구체적 날짜·자원·의존성이 명시되는가? |

**데이터 흐름:**
```
보고서 파일 or Confluence URL
    ↓
[report-red-team]
    ├─ 9개 원칙 × 피드백 항목 테이블 (🔴🟡🟢 우선순위)
    ├─ 각 피드백별 수정 제안
    └─ 종합 판정 + 결재 가능성 분석
    ↓
report-agent-system/output/report_review_{YYYYMMDD}_{주제}.md
    ↓ (선택)
Confluence 하위 페이지 자동 업로드
```

---

## 환경 설정

### 필수 환경변수

```bash
export CONFLUENCE_URL="https://musinsa-oneteam.atlassian.net"
export CONFLUENCE_EMAIL="your-email@musinsa.com"
export CONFLUENCE_API_TOKEN="ATATT3x..."
export CONFLUENCE_SPACE_KEY="~your-personal-space-key"
```

API 토큰 발급: Atlassian 계정 → Security → API tokens

### 선택 환경변수

```bash
export CONFLUENCE_PARENT_PAGE_ID="123456"  # 하위 페이지 생성 시 부모 페이지 ID
export GITHUB_TOKEN="ghp_..."              # PDIS 외부 레퍼런스 수집 시 Rate Limit 방지
export JIRA_PROJECT_KEY="TM"              # Epic Architect Jira 연동
```

---

## 스킬 스크립트 직접 사용

### search.py — Confluence 검색

```bash
python3 .claude/skills/confluence-tool/scripts/search.py \
  --query "앱푸시 성과" \
  --space retentionmarketing \
  --limit 10

# 접근 가능한 전체 Space 목록 확인
python3 .claude/skills/confluence-tool/scripts/search.py --list-spaces
```

### upload.py — Confluence 업로드

```bash
# 사전 조건: output/draft.html에 Confluence Storage Format(XHTML) 필요
python3 .claude/skills/confluence-tool/scripts/upload.py \
  --title "[202603] 앱푸시 월간 성과 분석" \
  --space membership \
  --parent-id 123456
```

### render.py — Mermaid 다이어그램 시각화

```bash
# 전체 .mmd 일괄 렌더링 (PRD 생성 후 자동 실행)
python3 prd-agent-system/.claude/skills/diagram-generator/scripts/render.py --all

# 단일 파일
python3 prd-agent-system/.claude/skills/diagram-generator/scripts/render.py \
  prd-agent-system/output/diagrams/campaign_user_flow.mmd

# 인라인 코드 직접 렌더링
python3 prd-agent-system/.claude/skills/diagram-generator/scripts/render.py \
  --inline "flowchart TD\n  A --> B" --name my_flow
```

### assemble.py — GTM 브리프 조립

```bash
python3 gtm-agent-system/.claude/skills/brief-formatter/scripts/assemble.py \
  --messaging gtm-agent-system/output/messaging_draft.json \
  --strategy  gtm-agent-system/output/strategy_draft.json \
  --template  gtm-agent-system/references/gtm_template.md \
  --output    gtm-agent-system/output/GTM_Brief_20260302_샘플.md
```

### PDIS 외부 레퍼런스 스크립트 직접 사용

```bash
# Amplitude GitHub Docs 수집
python3 discovery-intelligence-system/scripts/fetch_amplitude.py \
  --topic "retention cohort" \
  --limit 5 \
  --output discovery-intelligence-system/output/ext_amplitude_20260304.md

# Braze GitHub Docs 수집
python3 discovery-intelligence-system/scripts/fetch_braze.py \
  --topic "push notifications canvas" \
  --limit 5 \
  --output discovery-intelligence-system/output/ext_braze_20260304.md

# Shopify App Store 벤치마크
python3 discovery-intelligence-system/scripts/search_shopify.py \
  --query "loyalty rewards" \
  --limit 3 \
  --output discovery-intelligence-system/output/ext_shopify_20260304.md
```

---

## 세션 로그 — AI 작업 이력 자동 기록

`/staff` 호출 시마다 `output/logs/staff_sessions.jsonl`에 세션 로그가 자동 기록된다.

```jsonc
{
  "id": "20260409_090501",
  "start_ts": "2026-04-09T09:05:01+09:00",
  "end_ts":   "2026-04-09T09:18:42+09:00",
  "request":  "Audience API PRD 작성",
  "summary":  "Audience API 콘솔 PRD 작성 + Red Team 검증 완료",
  "skills":   ["/staff", "confluence-reader", "/prd", "/red"],
  "outputs":  ["prd_20260409_audience_api.md"],
  "output_types": ["prd", "confluence-edit"],   // ← 산출물 유형 분류
  "status":   "completed",
  "model":    "claude-sonnet-4-6",
  "tokens_in":  18400,
  "tokens_out": 4200,
  "cost_usd":   0.1182,
  "duration_sec": 821
}
```

### `output_types` 허용 값

| 유형 | 설명 |
|------|------|
| `prd` | PRD 신규 작성 |
| `prd-edit` | PRD 수정·보완 |
| `2-pager` | 2-Pager 의사결정 문서 |
| `confluence-page` | Confluence 페이지 신규 생성 |
| `confluence-edit` | Confluence 페이지 수정 |
| `jira-ticket` | Jira 티켓 생성 |
| `diagram` | Mermaid 등 다이어그램 |
| `meeting-notes` | 회의록 |
| `analysis` | 분석 보고서 / 인사이트 |
| `strategy` | 전략 문서 / 자문 |
| `report` | C레벨 보고서 |
| `markdown-doc` | 일반 마크다운 문서 |
| `script` | Python / 코드 스크립트 |
| `design-spec` | 화면 설계서 (Figma 기반) |
| `agent-skill` | 에이전트 / 스킬 설계·수정 |

로그 파일은 `output/logs/staff_sessions.jsonl`에 누적되며, 세션 통계·비용 분석에 활용된다.

---

## 산출물 경로 전체 목록

| 경로 | 설명 |
|------|------|
| `output/context.json` | Confluence 검색 결과 캐시 |
| `output/draft.html` | Confluence 업로드용 XHTML 초안 |
| `output/upload_result.json` | 업로드 결과 (페이지 URL 포함) |
| `output/confluence_skill.log` | API 호출 전체 로그 |
| `output/logs/staff_sessions.jsonl` | /staff 세션 로그 (스킬·산출물 유형·비용 포함) |
| `prd-agent-system/output/prd_*.md` | 생성된 PRD 파일 |
| `prd-agent-system/output/redteam_*.md` | Red Team 검증 질문지 |
| `prd-agent-system/output/diagrams/*.mmd` | Mermaid 플로우 소스 |
| `prd-agent-system/output/diagrams/*.html` | 브라우저 렌더링 다이어그램 (file://로 바로 열기) |
| `gtm-agent-system/output/GTM_Brief_*.md` | 생성된 GTM 브리프 |
| `gtm-agent-system/output/prd_parsed.json` | GTM용 PRD 파싱 결과 |
| `gtm-agent-system/output/messaging_draft.json` | 메시징 초안 |
| `gtm-agent-system/output/strategy_draft.json` | 전략 초안 |
| `epic-ticket-system/output/epic_spec_*.json` | 직무별 에픽 명세 (AC·날짜·의존성 포함) |
| `epic-ticket-system/output/jira_result_*.json` | 생성된 Jira 에픽 티켓 URL 목록 |
| `report-agent-system/output/report_review_*.md` | C레벨 보고서 품질 검토 결과 |
| `pgm-agent-system/output/flash_*.md` | Weekly Flash Report 로컬 마크다운 |
| `pgm-agent-system/output/analysed_report.json` | Jira 데이터 분류·우선순위 결과 캐시 |
| `pgm-agent-system/output/jira_raw_*.json` | Jira API 원시 티켓 데이터 |
| `discovery-intelligence-system/output/ext_amplitude_*.md` | Amplitude 외부 레퍼런스 |
| `discovery-intelligence-system/output/ext_braze_*.md` | Braze 외부 레퍼런스 |
| `discovery-intelligence-system/output/ext_shopify_*.md` | Shopify App Store 벤치마크 |
| `discovery-intelligence-system/output/ext_summary_*.md` | PDIS Phase 0 통합 요약 |
| `discovery-intelligence-system/output/market-intel.md` | 시장 분석 결과 |
| `discovery-intelligence-system/output/discovery-synthesis.md` | 인사이트 합성 결과 |
| `discovery-intelligence-system/output/FINAL-DISCOVERY-REPORT.md` | 최종 디스커버리 보고서 |
| `input/initiatives/{분기}/{티켓}/output/` | 이니셔티브별 산출물 |

---

## 오류 처리

| 오류 | 원인 | 처리 |
|------|------|------|
| 401 Auth Error | API 토큰 만료 | 토큰 재발급 후 환경변수 업데이트 |
| 검색 결과 0건 | 대상 Space에 문서 없음 | 타 부서 Space 에스컬레이션 (에이전트가 자동 제안) |
| 업로드 실패 | 포맷 오류 또는 권한 없음 | `output/draft.html` 경로 안내 + 수동 업로드 가능 |
| 404 Not Found | Space 키 미존재 | `config/spaces.json` Space 키 확인 |
| One-liner 50자 초과 | 메시징 생성 오류 | message-architect 자동 재시도 (최대 3회) |
| GitHub API 403 | Rate Limit 초과 | `GITHUB_TOKEN` 환경변수 설정 후 재실행 |
| Shopify 파싱 실패 | 동적 렌더링 구조 변경 | 직접 URL 링크 제공 + 수동 확인 안내 |

---

## 현재 이니셔티브 현황 (2026 Q1)

자세한 내용은 `input/initiatives/index.md` 참조.

| 티켓 | 이니셔티브 | 상태 | 마감 |
|------|-----------|------|------|
| TM-2061 | Campaign Meta Engine (Phase 1): CMS 연동 기반 캠페인·소재 관리 표준화 | In Progress | 2026-03-31 |
| TM-2134 | 무신사 Targeted Coupon 실험 (2차: CRM 스코어 V2 + 빅배너) | In Progress | 2026-12-31 |

---

> **최종 업데이트**: 2026-03-07 | **구동 환경**: Claude Code (claude-sonnet-4-6) + Atlassian Confluence REST API + Google Workspace API + Gmail SMTP + Jira REST API v3
