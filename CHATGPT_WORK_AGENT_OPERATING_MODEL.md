# ChatGPT Work × VS Code Agent Operating Model

> ChatGPT Work와 VS Code 기반 Agent Runtime(현재 Claude Code, 향후 Codex 포함)을 어떻게 역할 분리하고 연결할지 정의하는 운영 원칙.
>
> 이 문서는 현재 repo의 `CLAUDE.md`, `CAPABILITY_MAP.md`, `WORKFLOW_PATTERNS.md`, `CONVENTIONS.md`, `.claude/agents/`, `.claude/skills/` 구조를 전제로 한다.

---

## Executive Summary

앞으로의 기본 운영 모델은 **ChatGPT Work를 업무의 Front Door이자 Context/Orchestration Plane으로, 이 repo의 Agent System을 Method/Execution Plane으로 사용하는 구조**를 권장한다.

핵심 원칙은 다음과 같다.

1. **ChatGPT Work는 살아 있는 업무 맥락을 다룬다.** Slack, Confluence, Jira, Calendar, Notion, Figma, 웹 등 여러 소스에서 최신 정보를 수집하고, 모호한 문제를 탐색하며, 사람과 함께 방향을 결정한다.
2. **VS Code Agent는 반복 가능한 방법론을 실행한다.** PRD 생성·검증, Red Team, 데이터 분석, Chronicle, 품질 검사, 파일 변환, 레지스트리·체크포인트처럼 버전 관리와 재현성이 필요한 작업을 담당한다.
3. **SaaS 접속 자체를 위한 Agent는 점진적으로 얇게 만든다.** `confluence-reader`, `/slack`, `jira-creator`, Gmail wrapper처럼 Work가 네이티브 Connector로 처리할 수 있는 영역은 중복 구현을 최소화한다.
4. **repo의 강점은 Connector가 아니라 Methodology다.** `/prd`의 Phase 구조, Generator–Verifier 루프, `/data`의 조회→검증→분석→시각화, `/chronicle`의 누적 Wiki와 lint, Artifact Bus와 Checkpoint는 유지·강화한다.
5. **현재 `Chief of Staff`의 역할을 재정의한다.** 지금은 `CLAUDE.md`가 “사용자와의 유일한 접점”으로 정의되어 있지만, 향후에는 Work가 사용자-facing Front Door가 되고 로컬 Chief of Staff는 **repo 내부 실행 라우터**가 되는 편이 적합하다.
6. **Claude/Codex 등 Runtime별 규칙은 얇은 Adapter로 관리한다.** 업무 규칙과 방법론을 특정 Runtime 파일에 중복 작성하지 않고, 공통 문서·스크립트를 Single Source of Truth로 유지한다.

한 문장으로 정리하면:

> **Work에서 찾고·판단하고·조율하며, Agent에서 표준화하고·검증하고·반복 실행하고, 다시 Work에서 공유·반영한다.**

---

## 1. 왜 역할 분리가 필요한가

현재 repo는 이미 단순한 개인용 프롬프트 모음이 아니라 하나의 PM Operating System에 가깝다.

- `CLAUDE.md`: Chief of Staff 및 라우팅
- `CAPABILITY_MAP.md`: 팀별 역할·Trigger·Input/Output 정의
- `WORKFLOW_PATTERNS.md`: Discovery → PRD → Red Team → Epic/Jira 등 복합 실행 패턴
- `CONVENTIONS.md`: 파일 규칙, 승인 규칙, Artifact Bus, Checkpoint, Next Action
- `.claude/agents/`: Confluence, Jira, 문서 등 역할 기반 Sub-agent
- `.claude/skills/`: PRD, Data, Discovery, GTM, Slack, Chronicle 등 재사용 가능한 Skill
- 각 `*-agent-system/`: 특정 문제에 대한 세부 실행 시스템

이 구조의 장점은 **업무 방법론을 코드와 문서로 고정하고 반복할 수 있다는 것**이다.

반면 최근 ChatGPT Work는 업무 문서뿐 아니라 연결된 앱과 파일을 직접 다룰 수 있기 때문에, 과거에는 Agent repo에서 직접 구현해야 했던 “정보를 가져오는 역할” 중 상당 부분을 Work가 더 낮은 운영 비용으로 수행할 수 있다.

따라서 앞으로의 문제는 “Work와 VS Code 중 하나를 선택”하는 것이 아니라 다음 두 질문으로 바뀐다.

- 어떤 작업을 **살아 있는 업무 Context에 가까이 둘 것인가?**
- 어떤 작업을 **버전 관리되는 재현 가능한 Method에 가깝게 둘 것인가?**

---

## 2. ChatGPT Work와 VS Code Agent의 기본 차이

| 구분 | ChatGPT Work | VS Code Agent / Repo |
|---|---|---|
| 중심 객체 | 업무 목표, 대화, 문서, 연결된 앱 | Repository, 파일, Script, Git |
| 강한 Context | Slack·Confluence·Jira·Notion·Calendar·웹 등 최신 업무 정보 | repo 내부 문서, 코드, 상태파일, 실행 결과 |
| 강한 문제 | 모호한 문제, 탐색, 비교, 종합, 의사결정 | 정형화된 실행, 반복 처리, 검증, 자동화 |
| 작업 방식 | 자연어 중심의 동적 Orchestration | Skill + Script + Convention 중심 |
| 재현성 | 상대적으로 낮음 | 높음 |
| 버전 관리 | 업무 산출물 중심 | Method 자체를 Git으로 관리 가능 |
| 외부 SaaS 접근 | 네이티브 Connector 활용에 유리 | API/MCP/Auth 설정 필요 |
| 품질 Gate | Agent 판단 중심 | Validator, Red Team, lint, test와 결합 가능 |
| 적합한 빈도 | 일회성~가변적인 고난도 지식 업무 | 반복적이고 안정된 업무 |
| 대표 결과 | 판단, 초안, 공유용 문서, SaaS 반영 | 검증된 Markdown/JSON/HTML, 코드, Registry |

### 판단 기준

다음 조건이 많을수록 **Work 우선**이다.

- 최신 Slack/Confluence/Jira 등 여러 소스를 동시에 봐야 함
- 처음 하는 문제라 Input/Output이 아직 안정되지 않음
- 사용자와 여러 번 대화하며 방향을 결정해야 함
- 결과가 즉시 Confluence/Notion/Jira/Calendar 등에 반영되어야 함
- 작업 절차보다 문제 이해가 더 중요함

다음 조건이 많을수록 **repo Agent 우선**이다.

- 동일 유형 작업을 반복함
- 실행 순서와 품질 기준을 고정할 수 있음
- 산출물 형식이 명확함
- 스크립트, SQL, lint, test, diff가 필요함
- 실패 후 특정 단계부터 재실행해야 함
- 결과와 방법론 자체를 Git에서 추적할 가치가 있음

---

## 3. 현재 repo에서 이미 잘 만들어진 것

### 3.1 Method Layer

현재 가장 가치가 높은 자산은 특정 SaaS API 호출 코드보다 **업무를 수행하는 방식 자체**다.

예를 들어 `/prd`는 단순히 “PRD를 써주는 프롬프트”가 아니다.

- Rough Note 또는 Initiative Context 로드
- 필요 시 Phase 0 가정 검증
- PRD 생성
- Red Team 검증
- 보강본 생성
- 산출물 Registry 등록

처럼 하나의 재현 가능한 Product Planning Method를 구성한다.

`/data` 역시 CRM·Amplitude·Databricks·파일을 하나의 인터페이스로 묶고,

```text
조회 → 전처리·검증 → 전문 분석 → 인사이트 통합 → 시각화
```

라는 분석 Pipeline을 갖는다.

`/chronicle`은 Jira·Confluence·Slack·작업 로그를 일회성으로 요약하는 것이 아니라 프로젝트·Decision·Pattern·Growth Wiki를 지속적으로 갱신하고 lint한다.

이러한 영역은 Work가 정보를 더 쉽게 가져올 수 있게 되더라도 **repo에 남겨야 하는 핵심 경쟁력**이다.

### 3.2 Stateful Execution Layer

`CONVENTIONS.md`의 다음 요소도 repo가 담당하기 적합하다.

- Artifact Bus (`_artifacts.json`)
- Pipeline Checkpoint (`.pipeline_state.json`)
- 실패 단계부터 재실행
- 산출물 파일명 규칙
- Registry
- lint / validator
- irreversible action의 승인 원칙

이는 대화형 Assistant보다 **작은 Workflow Engine**에 가까운 기능이다.

### 3.3 Cross-runtime 자산

`CAPABILITY_MAP.md`, `WORKFLOW_PATTERNS.md`, `CONVENTIONS.md`처럼 Runtime에 종속되지 않는 문서는 장기적으로 Claude Code, Codex 또는 다른 Agent Runtime이 함께 사용할 수 있다.

향후 투자 우선순위는 이런 **Runtime-neutral 자산**을 늘리는 쪽이어야 한다.

---

## 4. 현재 구조에서 Work와 중복되는 영역

다음 역할은 업무 방법론보다 “외부 시스템에 접속하는 기능”의 비중이 크다.

- `.claude/agents/confluence-reader`
- `.claude/agents/confluence-writer`
- `.claude/agents/jira-creator`
- `/slack`
- Gmail 관련 Tool/Agent
- Calendar 관련 조회·등록
- 일부 Figma 조회 기능

예를 들어 현재 `/slack`은 Bot Token, OAuth Scope, Python Client 또는 MCP 설정이 필요하다. Confluence Reader도 별도의 MCP와 Space Routing을 갖고 있다.

이 구현이 틀렸다는 의미는 아니다. 다만 Work에서 동일 SaaS를 네이티브로 접근할 수 있다면, 앞으로는 **Connector를 직접 유지하는 것보다 상위의 분석·판단 규칙에 투자하는 편이 ROI가 높다.**

### 권장 원칙

> **Source Access는 Work 우선, Method Execution은 repo 우선.**

단, 다음 경우 Connector Skill을 유지한다.

- CI/CD나 예약 실행 등 사람이 대화에 참여하지 않는 자동화가 필요함
- 동일 API를 대량·반복 호출해야 함
- Work Connector가 제공하지 않는 세부 Endpoint가 필요함
- 조직 정책상 특정 인증·네트워크 경계를 따라야 함
- 결과를 Script에서 직접 받아 후속 계산해야 함

즉 기존 Connector Skill은 전부 삭제하기보다 **Fallback / Batch / Automation Adapter**로 축소하는 방향이 적절하다.

---

## 5. Target Operating Model

```text
┌──────────────────────────────────────────────────────────────┐
│                    ChatGPT Work — Front Door                 │
│                                                              │
│  Intent 이해 · 최신 Context 수집 · 탐색 · 비교 · 의사결정   │
│  Slack / Confluence / Jira / Notion / Calendar / Web / Figma│
└──────────────────────────────┬───────────────────────────────┘
                               │
                        Work Handoff Packet
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│             VS Code Agent Runtime — Execution Plane          │
│              Claude Code / Codex / future runtime            │
│                                                              │
│  Local Chief of Staff → /prd /red /data /chronicle /gtm ... │
│  Script · Validator · Registry · Git · Checkpoint · Artifact │
└──────────────────────────────┬───────────────────────────────┘
                               │
                         Verified Artifact
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                   ChatGPT Work — Publish Plane               │
│                                                              │
│  최종 검토 · 사람과 의사결정 · Confluence/Jira/Notion 공유  │
│  Slack 전달 · Calendar 반영 · 후속 Context 연결             │
└──────────────────────────────────────────────────────────────┘
```

### Layer A — Work: Context / Orchestration Plane

Work가 담당할 것:

- “무엇이 문제인가?”를 정의
- 최신 업무 Context 탐색
- 여러 Source의 상충 정보 대조
- 미결정 사항과 Decision 분리
- 이해관계자별 관점 파악
- 한 번성 조사와 외부 리서치
- 최종 사용자와의 반복 논의
- SaaS에 직접 반영할 최종 Action

### Layer B — Repo: Method / Execution Plane

repo Agent가 담당할 것:

- 이미 검증된 업무 절차 실행
- 입력을 정해진 Schema로 변환
- PRD/2-Pager/Red Team 등 표준 산출물 생성
- 정합성·누락·품질 자동 검사
- SQL/Python/Script 실행
- 파일 Batch 처리
- Registry와 Checkpoint 관리
- Git Diff를 통한 변경 이력 관리

### Layer C — Work: Publish / Collaboration Plane

최종 결과를 다시 Work로 가져오는 이유:

- 실제 Source와 대조한 마지막 검증
- 이해관계자에게 맞는 표현 조정
- Confluence/Jira/Slack/Notion 등 실제 업무 Surface에 반영
- 후속 논의를 기존 Context와 이어서 수행

---

## 6. Work Handoff Contract

Work와 repo 사이가 자연어 Copy/Paste에만 의존하면 Context 누락이 반복된다.

따라서 장기적으로 `input/handoffs/` 같은 경량 Handoff Layer를 두는 것을 권장한다.

예시:

```markdown
---
initiative: TM-XXXX
topic: Audience Serving
collected_at: 2026-08-23
requested_output: prd
authoritative_sources:
  - confluence: ...
  - slack: ...
  - jira: ...
---

# Objective
이번 작업에서 결정하거나 생성해야 하는 것

# Confirmed Facts
- 이미 확정된 내용

# Decisions
- 현재 유효한 의사결정

# Open Questions
- 아직 결정되지 않은 내용

# Evidence
- 수치, 사용자 피드백, 기술 제약 등

# Constraints
- 일정, 조직 경계, 정책, 비기능 조건

# Source Notes
- 출처별 핵심 요약
```

핵심은 **모든 원본 대화를 repo에 복제하는 것이 아니라, 실행에 필요한 구조화된 Context만 넘기는 것**이다.

Work는 Context Compression을 담당하고, Agent는 Method Execution을 담당한다.

---

## 7. 현재 Agent / Skill별 권장 배치

| Agent / Skill | 기본 배치 | 권장 방향 |
|---|---|---|
| `/prd` | **Repo** | 유지·강화. Phase, Registry, Red Team 연계를 핵심 자산으로 취급 |
| `/red` | **Repo** | 유지. Generator–Verifier Quality Gate로 사용 |
| `/two-pager` | **Repo** | 경영진 문서 Method가 안정적이면 유지 |
| `/gtm` | **Repo / Hybrid** | Context 수집은 Work, 표준 GTM 산출은 repo |
| `/data` | **Repo / Hybrid** | 반복 분석·검증·Script는 repo, ad-hoc 탐색은 Work |
| `/databricks` | **Repo** | SQL/Script와 직접 결합되는 만큼 유지 가치 높음 |
| `/analyst` | **Repo / Hybrid** | 단발 분석은 Work, 재현 가능한 분석 Type은 repo |
| `/chart` | **Repo** | deterministic rendering이 필요하면 유지 |
| `/chronicle` | **Repo** | 누적 Wiki, lint, Portfolio 생성은 repo의 장기 상태 자산 |
| `/discovery` | **Work → Repo** | 탐색은 Work 우선, 출력 Schema가 필요할 때 Skill 실행 |
| `/market-research` | **Work → Repo** | 최신 리서치는 Work, 반복 산출 Format은 repo |
| `/strategy` | **Work 우선** | 사람과의 논의·외부 최신 Context가 핵심. 필요 시 결과만 기록 |
| `/meeting` | **Hybrid** | Calendar/관련 문서 수집은 Work, 표준 회의록/Decision 추출은 repo 가능 |
| `/pgm` | **Hybrid** | 최신 Jira/Confluence Context는 Work, Flash/Checkpoint/Artifact는 repo |
| `/slack` | **Work 우선** | 네이티브 접근 우선. Batch/자동 실행용 Fallback만 유지 |
| `confluence-reader/writer` | **Work 우선** | 조회·작성 Wrapper 축소. 특수 Space Routing 필요 시 보조 사용 |
| `jira-creator` | **Work 우선 / Repo 검증** | Work가 실제 생성, repo는 티켓 구조·분해·품질 검증 |
| `task-ticket-creator` | **Hybrid** | 티켓 내용 구조화는 repo, 실제 생성은 Work |
| Gmail Agent | **Work 우선** | 메일 Context/발송은 Work, 반복 Template이 필요할 때만 repo |
| Figma Skill | **Hybrid** | 디자인 Context 접근은 Work/Figma Connector, PRD/Spec 변환은 repo |
| `/archive`, `/kb` | **Repo** | 로컬 상태·파일 체계 관리이므로 repo에 적합 |

---

## 8. 대표 Workflow를 앞으로 어떻게 바꿀 것인가

### 8.1 PRD 작성

#### 기존

```text
Local Chief of Staff
→ Confluence Reader / Slack Skill / Jira
→ /prd
→ /red
→ Confluence Writer
```

#### 권장

```text
ChatGPT Work
→ Slack + Confluence + Jira 최신 Context 통합
→ Confirmed / Decision / Open Question 분리
→ Handoff Packet
→ /prd
→ /red
→ 필요 시 qa-agent
→ Verified Markdown 반환
→ ChatGPT Work에서 최종 검토 및 Confluence/Jira 반영
```

이 방식의 장점:

- Source Connector 유지비 감소
- 최신 Context 수집 품질 향상
- repo에는 PRD 방법론과 품질 Gate만 남음
- 실제 사내 문서 수정은 사람이 보는 Work 대화에서 최종 확인 가능

### 8.2 Slack 논의 → Decision Log / 회의 준비

```text
Work에서 관련 Thread·채널·문서 조회
→ 논의 Timeline + 확정/미결정 분류
→ 반복 가능한 형식이 필요하면 repo의 Decision/Meeting Method 실행
→ Work에서 Calendar/Confluence/Slack에 공유
```

단순히 “오늘 Slack 요약” 정도라면 repo를 거치지 않아도 된다.

반대로 여러 주의 Slack을 비교하고 Decision History를 누적하거나 lint해야 한다면 repo의 State Layer로 넘긴다.

### 8.3 데이터 기반 기획

```text
Work
→ 왜 이 분석이 필요한지, 어떤 의사결정을 할지 정의
→ 관련 Jira/PRD/Slack Context 수집

Repo /data
→ 실제 데이터 조회
→ validation
→ 분석
→ chart
→ 재현 가능한 결과 저장

Work
→ 비즈니스 Context와 결합
→ PRD/2-Pager/의사결정으로 연결
```

핵심은 **분석 질문은 Work에서 만들고, 계산·검증은 repo에서 재현 가능하게 실행하는 것**이다.

### 8.4 Weekly Review / Chronicle

`/chronicle`은 Work로 대체하지 않는다.

```text
Work → 이번 주의 Jira/Slack/Confluence/Calendar Context 수집
     ↓
Chronicle ingest → Wiki 누적 → lint → weekly/monthly feedback
     ↓
Work → 결과를 현재 업무 상황과 함께 검토하고 다음 액션 결정
```

Chronicle의 가치는 “이번 주를 요약”하는 것이 아니라 **지난 여러 주의 상태를 구조적으로 누적하고 패턴을 찾는 것**에 있다.

### 8.5 Figma → PRD

```text
Work/Figma Connector
→ 최신 화면·관련 논의·PRD Context 확인
→ 변경의 목적과 미결정 사항 정리
→ repo /figma --prd 또는 /prd
→ /red
→ Work에서 디자인/PRD/개발 커뮤니케이션 연결
```

---

## 9. Chief of Staff 역할 재정의

현재 `CLAUDE.md`는 Chief of Staff를 “사용자와의 유일한 접점”으로 정의한다.

향후 권장 정의는 다음과 같다.

### Before

> 모든 사용자 요청의 Front Door이며 외부 Source 조회부터 실행·게시까지 전체를 직접 조율

### After

> **repo에 들어온 구조화된 요청을 적절한 Skill·Agent·Script로 라우팅하는 Local Execution Router**

즉 책임 범위를 축소한다.

```text
Work Chief of Staff
= Intent + Context + Collaboration

Repo Chief of Staff
= Method Routing + Execution + Validation
```

이렇게 하면 Work와 repo가 서로 “누가 진짜 Orchestrator인가”를 경쟁하지 않는다.

---

## 10. Codex / Claude Code를 함께 쓰기 위한 구조

현재 repo는 `.claude/`, `CLAUDE.md`, Claude MCP 이름 등 Claude Code Runtime에 상당히 결합되어 있다.

Codex를 추가한다면 모든 Skill을 복제하는 방식은 피한다.

### 권장 구조

```text
ai-native-pm/
├── AGENTS.md                  # Codex용 얇은 Entry Point
├── CLAUDE.md                  # Claude Code용 얇은 Entry Point
├── CONVENTIONS.md             # 공통
├── CAPABILITY_MAP.md          # 공통
├── WORKFLOW_PATTERNS.md       # 공통
├── playbooks/                 # 장기적으로 Runtime-neutral Method 후보
├── scripts/                   # 공통 실행 코드
├── input/                     # 공통 Context / Handoff / State
├── output/                    # 공통 Artifact
└── .claude/                   # Claude Runtime Adapter
    ├── agents/
    └── skills/
```

### `AGENTS.md`가 해야 할 일

`CLAUDE.md` 전체를 복사하지 않는다.

대신 다음만 정의한다.

1. 이 repo의 역할
2. 반드시 읽어야 할 공통 문서
3. 요청 유형별 Routing
4. 안전한 실행 규칙
5. Runtime-specific Tool 사용법

업무 Method는 공통 문서나 Script를 참조한다.

### Single Source of Truth 원칙

```text
Business / Product Method
        ↓
CONVENTIONS / CAPABILITY_MAP / WORKFLOW_PATTERNS / playbooks
        ↓
 ┌─────────────────┬─────────────────┐
 │ Claude Adapter  │ Codex Adapter   │
 │ CLAUDE.md       │ AGENTS.md       │
 │ .claude/skills  │ Codex routing   │
 └─────────────────┴─────────────────┘
```

Runtime을 바꿔도 업무 방식이 달라지지 않는 구조가 목표다.

---

## 11. 새로운 Skill을 만들지 판단하는 기준

앞으로 “이것도 Skill로 만들자”는 결정을 다음 Gate로 판단한다.

### Skill화 권장

아래 중 3개 이상에 해당하면 repo Skill 후보로 본다.

- 같은 작업을 이미 여러 번 반복함
- Input과 Output을 Schema로 정의 가능
- 일정한 단계 순서가 존재함
- 사람마다 결과 편차가 크고 품질 기준이 필요함
- Script / SQL / lint / validation이 유용함
- 실패 후 재실행이 필요함
- 산출물을 Git으로 추적할 가치가 있음

### Work에 남기는 것이 나은 경우

- 아직 문제 정의가 계속 바뀜
- 최신 대화와 이해관계자 Context가 핵심임
- 한두 번만 수행할 가능성이 높음
- Skill을 정의하는 비용이 실제 업무보다 큼
- “무엇을 해야 하는가”가 “어떻게 반복할 것인가”보다 중요함

실무적으로는 **동일한 유형을 3회 이상 반복했고 실행 순서가 안정됐을 때 Agentize 후보로 승격**하는 것을 기본 Heuristic으로 사용한다.

---

## 12. Migration Plan

### Phase 0 — 즉시 적용

- ChatGPT Work를 기본 업무 Front Door로 사용
- 새로운 SaaS Reader/Writer wrapper 추가를 원칙적으로 중단
- `/prd`, `/red`, `/data`, `/chronicle` 등 Method Skill 중심으로 투자
- Work에서 구조화된 Context를 만든 후 repo 실행

### Phase 1 — Handoff 표준화

추가 권장:

```text
input/handoffs/
├── _template.md
└── YYYYMMDD_{topic}.md
```

Handoff에 반드시 포함할 것:

- Objective
- Confirmed Facts
- Decisions
- Open Questions
- Evidence
- Constraints
- Source Links

### Phase 2 — Skill Portfolio 정리

모든 Skill에 아래 상태를 붙인다.

```text
CORE       = repo에 계속 투자
HYBRID     = Work Context + repo Method
WORK-FIRST = Work 우선, repo는 fallback
LEGACY     = 신규 투자 중단
```

우선 분류 제안:

- CORE: `prd`, `red`, `data`, `databricks`, `chart`, `chronicle`, `archive`, `kb`
- HYBRID: `pgm`, `meeting`, `gtm`, `discovery`, `market-research`, `figma`, `task-ticket`
- WORK-FIRST: `slack`, Confluence Reader/Writer, Jira Creator, Gmail/Calendar access

### Phase 3 — Codex Adapter 추가

- top-level `AGENTS.md` 추가
- 공통 Method를 Runtime-neutral 문서로 참조
- Claude와 Codex가 같은 Script·Output·Registry 사용
- Runtime별 Prompt 복제를 최소화

### Phase 4 — 측정

Agent System 개선을 느낌이 아니라 다음 지표로 본다.

- Context 준비 시간
- 하나의 PRD/분석 산출물 완료까지 필요한 대화 Turn
- Red Team Critical 재발률
- Source 누락률
- 수동 Copy/Paste 횟수
- Skill 재사용 횟수
- 실패 후 재실행 성공률
- 실제 Publish까지 걸리는 단계 수

---

## 13. Default Routing Rule

앞으로 새 요청이 들어오면 아래 순서로 판단한다.

```text
1. 최신 업무 Context가 필요한가?
   └─ Yes → Work에서 먼저 수집

2. 처음 하는 문제이거나 방향이 아직 모호한가?
   └─ Yes → Work에서 탐색·논의

3. 반복 가능한 Method가 이미 repo에 있는가?
   └─ Yes → Handoff 후 해당 Skill 실행

4. 검증·Script·SQL·Lint·Checkpoint가 필요한가?
   └─ Yes → Repo Agent

5. 최종 결과를 SaaS에 반영해야 하는가?
   └─ Yes → Work에서 최종 검토 후 Publish

6. 같은 작업이 반복되는데 Skill이 없는가?
   └─ 반복 3회 이상 + 구조 안정 → Agentize 검토
```

---

## 14. 최종 권장 상태

목표는 “ChatGPT Work를 많이 쓰는가” 또는 “VS Code Agent를 많이 쓰는가”가 아니다.

좋은 상태는 다음과 같다.

- **Work에는 최신 Context와 사람의 판단이 모인다.**
- **repo에는 시간이 지나도 재사용할 가치가 있는 Method와 State가 쌓인다.**
- **Connector 구현은 최소화하고 Native Integration을 활용한다.**
- **중요한 업무 절차는 코드·문서·Validator로 고정한다.**
- **Runtime은 교체 가능하고 Method는 남는다.**

현재 repo는 이미 PRD, Data, Chronicle, Artifact Bus, Workflow Pattern 등 중요한 Method Layer를 갖고 있다. 앞으로의 고도화 방향은 Agent 수를 계속 늘리는 것이 아니라, **어떤 업무를 Agentize할 가치가 있는지 선별하고 Work와 repo 사이의 Handoff를 표준화하는 것**이어야 한다.

> **Work = Context & Decision OS**  
> **Repo Agent = Method & Execution OS**

이 두 레이어를 분리하면, Work의 빠른 Context 접근성과 repo의 재현성·검증 가능성을 동시에 가져갈 수 있다.
