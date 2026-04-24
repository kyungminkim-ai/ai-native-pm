# CAPABILITY_MAP — 팀별 역량 맵

> 비서실장이 역량 점검 시 참조하는 문서.
> 각 팀의 역할, 트리거, 입력/출력, 호출 방법을 정의한다.
> 마지막 업데이트: 2026-04-12

---

## 팀 구성 개요

```
pm-studio
├── [기획팀]        PRD 작성 · Red Team 검증 · 2-Pager
├── [PGM팀]        Weekly Flash · C레벨 보고서 검토
├── [디스커버리팀]  시장/제품 Discovery 분석
├── [지식팀]        Confluence 조회/저장
├── [커뮤니케이션팀] Jira 티켓 생성
├── [미팅팀]        회의록 작성 · Confluence 업로드
├── [데이터팀]      Databricks 탐색 · 쿼리 · 분석
├── [분석팀]        데이터 분석 인사이트 (트렌드/세그먼트/퍼널/코호트/A-B테스트)
├── [협업팀]        Slack 대화 조회 · 챗봇
├── [디자인팀]      Figma 화면 분석 · 설계서 생성
└── [전략팀]        전략 자문 · 논의 (Lenny's Podcast + Braze Docs + Garry Tan ETHOS 기반)
```

---

## [기획팀] PRD / 검증

### 역할
기능 기획서 작성부터 Jira 실행 준비까지의 전체 기획 파이프라인을 담당한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| 2-Pager 작성 + 검토 | Skill: `/two-pager` | claude-sonnet-4-6 |
| **PRD 가정 검증 (Pre-PRD)** | Skill: `/prd --validate` | claude-sonnet-4-6 |
| PRD 작성 | Skill: `/prd` | claude-sonnet-4-6 |
| Red Team 검증 | Skill: `/red` | claude-sonnet-4-6 |
| **PRD 스코프 캘리브레이션** | Skill: `/red --scope [expand\|selective\|hold\|reduce]` | claude-sonnet-4-6 |

### 트리거 키워드
2-Pager, 2페이저, 의사결정 문서, 경영진 보고, BLUF, PRD, 기능 기획, 요구사항, 제품 명세, Red Team, 가정 검증, 반론, Epic, 에픽, 티켓 분해, 스코프,
데이터 파이프라인, 데이터 연동, API 연동, 로그 수집, 배치 파이프라인, 스키마, 데이터 카탈로그,
**문제 정의, 가정 검증, 최소 버전, MVP, 기획 전 검토, 스코프 확장, 스코프 축소**

### 세부 역량

#### 2-Pager 작성 + 검토 (`/two-pager`)
- **입력**: 아이디어/문제 정의 텍스트, TM-XXXX, 또는 `--refs [Confluence URL]`
- **출력**: `prd-agent-system/output/two_pager_{YYYYMMDD}_{주제}.md`
- **구조**: BLUF → 배경·문제 → 솔루션 → 대안 검토 → 리스크 → 성공 지표 → 요청 사항 (7섹션 고정)
- **특징**:
  - `two-pager-writer`: 독자 질문 목록 선제 생성 → 7섹션 완성된 문장으로 작성
  - `two-pager-reviewer`: Silent Read 시뮬레이션 → 약한 섹션 직접 재작성 + `> [!COMMENT]` 코멘트 + 예시 문장 삽입
  - PRD 연결 없음 — `/prd`는 별도 요청 시에만 실행
- **실행**: `.claude/skills/two-pager/SKILL.md` 워크플로우 따름

#### 기능 PRD 작성 (`/prd`)
- **입력**: 이니셔티브 ID(TM-XXXX) 또는 rough note 텍스트
- **출력**: `prd-agent-system/output/prd_{YYYYMMDD}_{주제}.md`
- **특징**: TM-XXXX 입력 시 이니셔티브 KB 자동 로드, 이니셔티브 output/ 폴더에도 저장
- **실행**: `prd-agent-system/CLAUDE.md` 워크플로우 따름

#### 데이터 PRD 작성 (`/prd` — 데이터 파이프라인 요청 시 자동 분기)
- **입력**: 데이터 파이프라인 rough note + 선택적 Confluence 참조
- **출력**: `prd-agent-system/output/prd-data_{YYYYMMDD}_{주제}.md`
- **PRD 유형**: API 연동형 / 로그 수집형 / 배치 파이프라인형 / 혼합형 자동 분류
- **목차 구조**: I.문서개요 / II.배경 및 이해관계자 / III.데이터정의 및 수집 / IV.활용 및 운영 / V.거버넌스 / VI.부록 (6섹션 고정)
- **특징**: 스키마 명세 + 데이터 흐름 Mermaid + 개인정보 처리 + 카탈로그 등록 계획 포함
- **실행**: `prd-agent-system/CLAUDE.md` Section 1-A 판별 → `data-prd-writer` 에이전트
- **기능 PRD와 구분**: 파일명 prefix `prd-data_` 사용 (기능 PRD는 `prd_`)

#### PRD 가정 검증 (`/prd --validate`)
- **입력**: 아이디어 수준의 rough note 텍스트
- **출력**: Phase 0 검증 요약 → Phase 1 이후 PRD 전체 파이프라인으로 자동 연결
- **5개 질문**: 수요 증거 / 현재 대안 / 타깃 사용자 구체화 / 최소 버전 / 핵심 전제
- **특징**: TM-XXXX 없는 새 주제 시작 시 자동 판단 실행 (명시 불필요)
- **실행**: `prd-agent-system/CLAUDE.md` Section 0

#### Red Team 검증 (`/red`)
- **입력**: PRD 파일 경로 또는 Confluence URL
- **출력**: `prd-agent-system/output/redteam_{YYYYMMDD}_{주제}.md`
- **특징**: 9카테고리 반론 질문 생성, Critical/Important/Minor 우선순위 태깅
- **의존**: PRD 파일 필요 (없으면 confluence-reader로 검색)

#### PRD 스코프 캘리브레이션 (`/red --scope`)
- **입력**: PRD 파일 + `--scope expand|selective|hold|reduce`
- **출력**: Red Team 질문지 + **Scope Calibration 섹션** 추가
- **모드**: expand(더 크게) / selective(골라서 확장) / hold(완성도 집중, 기본) / reduce(범위 축소)
- **특징**: 스코프 방향 결정이 필요할 때 Red Team과 함께 사용

#### QA 문서 생성 (`qa-agent`)
- **입력**: PRD 파일 경로 (`prd_path`) + 선택적 날짜·주제
- **출력**:
  - `prd-agent-system/output/qa_testcase_{YYYYMMDD}_{주제}.md` — QA 테스트케이스 (Happy Path / Edge / Error / UI State)
  - `prd-agent-system/output/qa_briefing_{YYYYMMDD}_{주제}.md` — PM QA 킥오프 미팅 브리핑
- **특징**: P0 기능당 TC 최소 3개, FE 동작 명세 → UI State TC 자동 변환, OQ 미결 항목 자동 보류 처리
- **실행**: `prd-agent-system/.claude/agents/qa-agent/AGENT.md` 워크플로우 따름

### 팀 내 표준 파이프라인
```
[의사결정 단계]   /two-pager → (사용자 논의/수정)
                       ↓ (별도 요청 시)
[기획 단계]      /prd → (Phase 4: Red Team 자동) → (Phase 5: 보강 자동 → _v2.md)
                              → (Phase 4.5: Critical 재검증 자동, 최대 2회 루프)
                              → qa-agent
```
> **Generator-Verifier 루프**: Phase 4.5가 Red Team Critical 항목의 실제 해소를 검증.
> 미해소 시 Phase 5 재실행 (최대 2회), 이후 강제 통과 + 사용자 보고.
> 상세: `prd-agent-system/.claude/rules/phase45-reverify.md`

---

## [PGM팀] PM Command Center

### 역할
PM의 주간 업무 전반을 담당하는 통합 허브.
Jira 성과 분석, 회의록 처리, Initiative 코멘트 게시, 보고서 배포, 과제 분류를 단일 파이프라인으로 연결한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| PGM Command Center (통합) | Skill: `/pgm` | claude-sonnet-4-6 |
| Weekly Flash 생성 | Skill: `/pgm [JIRA_KEY]` | claude-sonnet-4-6 |
| 회의록 → Jira 코멘트 | Skill: `/pgm --weekly [URL]` | claude-sonnet-4-6 |
| Flash + 회의록 + 코멘트 통합 | Skill: `/pgm --full [KEY] [URL]` | claude-sonnet-4-6 |
| **이니셔티브 위클리 업데이트** | **Skill: `/pgm --initiative-weekly [JIRA_KEY] [WEEKLY_DOC_URL]`** | claude-sonnet-4-6 |
| C레벨 보고서 검토 | Skill: `/report` | claude-sonnet-4-6 |
| 과제 검토 (MATCH 분류) | Skill: `/ticket-review` | claude-sonnet-4-6 |

### 트리거 키워드
Weekly Flash, 주간 보고, 성과 정리, KPI, 이번 주 결과, 회의록, 미팅 정리, Jira 업데이트,
보고서 검토, C레벨, 결재, 과제 검토, 티켓 분류, MATCH 과제,
이니셔티브 위클리, 위클리 업데이트, Weekly 공유사항, Initiative 주간 정리

### 세부 역량

#### PGM 통합 실행 (`/pgm --full`)
- **입력**: Jira 프로젝트 키 + Confluence 회의록 URL + 선택적 메모
- **출력**:
  - `pgm-agent-system/output/flash_{YYYYMMDD}.md` + Google Docs + Gmail
  - `pgm-agent-system/output/meeting_minutes_{YYYYMMDD}.md` + Google Docs
  - `pgm-agent-system/output/slack_summary_{YYYYMMDD}.txt`
  - `pgm-agent-system/output/weekly_draft_{YYYYMMDD}.json`
  - Jira Initiative별 Weekly 코멘트 게시
  - `pgm-agent-system/output/_artifacts.json` 갱신
- **특징**: 체크포인트 기반 파이프라인 — 재실행 시 완료 단계 스킵
- **실행**: `pgm-agent-system/CLAUDE.md` `full` 모드

#### Weekly Flash Report (`/pgm [JIRA_KEY]`)
- **입력**: Jira 프로젝트 키 + 선택적 메모
- **출력**: Flash Report 3종 (MD + Docs + Gmail)
- **특징**: WoW 트렌드 포함 (이전 주 데이터 있을 때), 체크포인트 지원
- **실행**: `pgm-agent-system/CLAUDE.md` `flash` 모드

#### 이니셔티브 위클리 업데이트 (`/pgm --initiative-weekly [JIRA_KEY] [WEEKLY_DOC_URL]`)
- **입력**: Initiative 키(TM-XXXX) + 이니셔티브 위클리 Confluence URL + 선택적 회의록 URL(`--notes`)
- **출력**:
  - Confluence 이니셔티브 위클리 문서에 이번 주 요약 섹션 추가
  - Jira TM-XXXX Description 내 `Weekly 공유사항` 섹션 업데이트
- **특징**: 위클리 문서 + 회의록 동시 참조 → AI 종합 → 미리보기 → 사용자 승인 → 실행
- **주의**: 실행 전 반드시 사용자 승인 (Confluence 수정 + Jira Description 수정은 되돌리기 어려움)
- **실행**: `pgm-agent-system/.claude/agents/initiative-weekly-agent/AGENT.md`

#### 회의록 → Jira 코멘트 (`/pgm --weekly [URL]` 또는 `/weekly`)
- **입력**: Confluence 회의록 URL
- **출력**: TM-XXXX 티켓별 `N주차 Weekly 공유사항` 코멘트
- **특징**: AI 파싱 → 마크다운 미리보기 → 사용자 승인 → 게시
- **섹션**: `지난주 진행상황` + `Action Item (이번주)`
- **주의**: 게시 전 반드시 사용자 승인 (되돌리기 어려움)

#### C레벨 보고서 품질 검토 (`/report`)
- **입력**: 보고서 파일 경로 (없으면 `_artifacts.json`에서 이번 주 Flash 자동 선택)
- **출력**: `report-agent-system/output/report_review_{YYYYMMDD}_{주제}.md`
- **특징**: 즉시 결재 가능 / 질문 후 결재 / 반려 가능성 3단계 판정
- **의존**: `report-agent-system/.claude/agents/red-team-validator` 내부 호출

#### 과제 검토 (`/ticket-review`)
- **입력**: Jira 내보내기 CSV (`input/data/*.csv`) 또는 JQL
- **출력**: `pgm-agent-system/output/ticket_review_{YYYYMMDD}.md`
- **특징**:
  - MATCH 팀 과제 자동 식별 (명시적 지표 + 도메인 키워드)
  - 유사 과제 에픽·레이블·의미 기반 클러스터링
  - 판단 경계 과제는 `판단 필요` 별도 분류
- **실행**: `pgm-agent-system/.claude/agents/ticket-reviewer/AGENT.md`

### 팀 내 표준 파이프라인

```
# 주간 전체 실행 (권장) — Agent Teams 병렬 패턴
/pgm --full MATCH {CONFLUENCE_URL}
  Step 1: Jira 수집 ┐ (병렬)
          Confluence ┘
  Step 2: Flash 분석 ┐ (병렬) ← 개선: 기존 단일 analyst → 2개 독립 분석으로 분리
          회의록 분석 ┘
  Step 3: publisher ┐ (병렬)
          minutes-generator ┘
  Step 4: weekly-poster (minutes_analysed 재사용)

# 단계별 실행
/pgm MATCH              → Flash만
/pgm --weekly {URL}     → 회의록 코멘트만

# 보고서 검토
/pgm → /report
```

### Artifact Bus 참조

`pgm-agent-system/output/_artifacts.json`에서 이번 주 산출물 경로 확인:
- `/report` 호출 시 → `flash_md` 필드에서 입력 파일 자동 선택
- `/mail` 호출 시 → `flash_md` 또는 `meeting_minutes_md` 참조

---

## [디스커버리팀] 시장/제품 분석

### 역할
시장 조사, 경쟁사 분석, 사용자 인터뷰 시뮬레이션, 화이트스페이스 발굴을 수행한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| Discovery 분석 | Skill: `/discovery` | claude-sonnet-4-6 |
| 웹 화면 분석 | Skill: `/discovery --mode web-analysis` | claude-sonnet-4-6 |

### 트리거 키워드
Discovery, 시장 분석, 경쟁사, 화이트스페이스, 사용자 인터뷰, 벤치마크, 트렌드, Amplitude, Braze, Shopify, 외부 레퍼런스, 화면 분석, UI 분석, 화면 설계서, 서비스 분석

### 세부 역량

#### Product Discovery (`/discovery`)
- **입력**: 탐색 주제 텍스트 + 선택적 옵션
  - `--ref all/amplitude/braze/shopify`: 외부 벤더 레퍼런스 수집
  - `--initiative TM-XXXX`: 이니셔티브 컨텍스트 로드
- **출력**: `discovery-intelligence-system/output/` 내 분석 보고서
- **특징**: 외부 레퍼런스 수집(Phase 0) → 시장 분석 → 가상 인터뷰 → 인사이트 합성 → 보고서 5단계
- **실행**: `discovery-intelligence-system/CLAUDE.md` 워크플로우 따름

#### 웹 화면 분석 (`/discovery --mode web-analysis`)
- **입력**: 대상 서비스 URL + 선택적 옵션
  - `--depth gnb`: 기능 중심 탐색 — GNB 항목 순회 (기본값)
  - `--depth scenario "{목적}"`: 시나리오 중심 탐색
  - `--menu "{메뉴명}"`: 특정 메뉴만 분석
  - `--initiative TM-XXXX`: 이니셔티브 연결
- **출력**: `discovery-intelligence-system/web-analyzer-agent/output/screen_spec.md` + `screenshots/`
- **특징**: Playwright 브라우저 자동화 + Claude Vision 분석. Google OAuth 감지 시 Semi-Auto 로그인
- **사전 조건**: `pip install playwright && playwright install chromium`
- **실행**: `discovery-intelligence-system/web-analyzer-agent/CLAUDE.md` 워크플로우 따름
- **연계**: Reference 분석과 연결 가능 (`--mode reference --input screenshots/`)

---

## [지식팀] Confluence & Notion

### 역할
사내 지식 저장소(Confluence, Notion)에서 정보를 검색·조회하고, 새 문서를 생성·저장한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| Confluence 검색/조회 | Agent: `confluence-reader` | claude-haiku-4-5 |
| Confluence 페이지 저장 | Agent: `confluence-writer` | claude-haiku-4-5 |

### 트리거 키워드
찾아줘, 알려줘, 어디에, 검색, Confluence, 저장해줘, 올려줘, 문서화, 위키

### 세부 역량

#### Confluence 검색/조회 (`confluence-reader` agent)
- **입력**: 검색 키워드 또는 질문 텍스트
- **출력**: `output/context.json` + 마크다운 요약
- **Space 결정 로직**:
  - always_include: `membership`, `PE`, 개인 Space (항상 검색)
  - 토픽 라우팅 (키워드 감지 시 추가):
    - 마케팅/그로스: `retentionmarketing` → `LTV` → `GP`
    - 추천: `29CMRec`
    - 29CM: `29PRODUCT` → `2CEE` → 등
- **에스컬레이션**: 전체 Space 검색 후 0건 → `escalate: true` 반환 → 사용자에게 `--space ALL` 재검색 제안

#### Confluence 페이지 저장 (`confluence-writer` agent)
- **입력**: 대화 내용 또는 분석 결과 + 대상 Space
- **출력**: Confluence 페이지 URL + `output/draft.html`
- **제목 규칙**: `[YYYYMM] {주제} 분석` (50자 이하)
- **중복 처리**: 동일 제목 존재 시 업데이트 여부 사용자 확인
- **이니셔티브 우선**: `meta.json.confluence.primary_space`가 있으면 spaces.json보다 우선

### 팀 내 표준 패턴
```
# 조회
confluence-reader → 요약 → 사용자 답변

# 저장
(선택) confluence-reader로 중복 확인 → confluence-writer

# 조회 후 저장
confluence-reader → 분석 → confluence-writer
```

---

## [커뮤니케이션팀] 이메일 & Jira

### 역할
문서를 이메일로 변환·발송하고, Jira 티켓을 개별 생성한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| Jira 티켓 생성 | Agent: `jira-creator` | claude-sonnet-4-6 |
| MEMB Task 티켓 생성 | Skill: `/task-ticket` + Agent: `task-ticket-creator` | claude-sonnet-4-6 |

### 트리거 키워드
Jira, 티켓, 이슈, 등록, 만들어줘, MEMB, Task 티켓

### 세부 역량

#### Jira 티켓 개별 생성 (`/jira` 또는 `jira-creator` agent)
- **입력**: 자연어 티켓 요청 (참조 티켓 TM-XXXX/PSN-XXX 언급 가능)
- **처리**: 생성 목록 표 → 사용자 컨펌 → Python 스크립트 생성·실행
- **출력**: `scripts/create_jira_{이니셔티브명}_{YYYYMMDD}.py` + Jira 티켓 URL 목록
- **주의**: 티켓 생성은 되돌리기 어려우므로 반드시 사전 컨펌

#### MEMB Task 티켓 생성 (`/task-ticket` 또는 `task-ticket-creator` agent)
- **입력**: 대화 내용(슬랙/회의 내용 붙여넣기) 또는 작업 설명 텍스트
- **처리**: 내용 분석 → 제목·본문·기한·우선순위 제안 → 사용자 컨펌 → 생성
- **출력**: `scripts/create_memb_task_{YYYYMMDD}_{slug}.py` + MEMB 티켓 URL
- **프로젝트**: MEMB 고정
- **이슈 유형**: Task (단건 또는 복수 지원)
- **특징**: 배경·작업내용·AC 구조화, 날짜 힌트 자동 변환, 컨펌 전 절대 생성하지 않음

> 이 팀의 Jira는 소규모 개별 티켓 생성에 특화.

---

## [미팅팀] 회의 관리

### 역할
회의 전·후 관리를 담당. 회의 맥락을 수집하고, Confluence 회의록을 작성·업로드하며, Google Calendar에 요약을 등록한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| 회의록 작성 + Confluence 업로드 | Skill: `/meeting` | claude-sonnet-4-6 |
| 회의록 + 캘린더 등록 | Skill: `/meeting --calendar` | claude-sonnet-4-6 |
| 회의록 AI 작성 | Skill: `/meeting` 내장 (self-contained) | claude-sonnet-4-6 |

### 트리거 키워드
회의록, 미팅, 미팅 정리, 회의 준비, 회의 기록, 회의 요약, 캘린더 등록, 일정 업데이트

### 세부 역량

#### 회의록 작성 (`/meeting`)
- **입력**: 회의 노트 파일(`--input`, `input/meetings/` 권장) / Confluence URL(`--confluence`) / Initiative(`--initiative`)
- **출력**: `output/meetings/meeting_draft_{YYYYMMDD}_{slug}.md` + Confluence 페이지
- **업로드 대상**: Core Customer Space / `[MATCH 미팅 회의록]` 하위
- **페이지 제목 형식**: `{YYYY년 MM월 DD일} {회의 제목}`
- **주의**: 업로드 전 반드시 미리보기 + 사용자 승인
- **실행**: `.claude/skills/meeting/SKILL.md` 워크플로우 (자체 완결)

#### Google Calendar 등록 (`/meeting --calendar`)
- **조건**: 위 회의록 작성 후 자동 연계 또는 `--calendar-only`로 단독 실행
- **이벤트 탐색**: 날짜 + 키워드 검색 → 복수 매칭 시 목록 선택
- **삽입 포맷**:
  ```
  [회의 요약 — PM Studio]
  📋 목적 / ✅ 결정 사항 / 📌 Action Item / 🔗 Confluence URL
  ```
- **환경변수**: `GOOGLE_CLIENT_SECRETS_PATH`, `GOOGLE_CALENDAR_ID`
- **미설정 시**: STUB 모드 (요약 텍스트만 출력)

### 팀 내 표준 파이프라인

```
# 회의록 작성 + Confluence 업로드
/meeting --input notes.txt --initiative TM-2055

# 회의록 + 캘린더 등록 한 번에
/meeting --input notes.txt --title "Auxia 정기 미팅" --calendar

# 회의록 업로드 후 Jira 코멘트 반영 (PGM 연동)
/meeting → /pgm --weekly {Confluence URL}
```

### 설정 필요 항목

`config/spaces.json`의 `core_customer` 섹션:
- `space_key`: Core Customer Space의 실제 키
- `meeting_parent_id`: `[MATCH 미팅 회의록]` 페이지 ID

---

## [회고팀] 작업 캘린더

### 역할
특정 날짜의 시간대별 작업 내역을 캘린더 파일(CSV/ICS)로 변환한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| 작업 캘린더 생성 (일별 CSV+ICS) | Agent: `calendar-agent-system/CLAUDE.md` | **Haiku** |

### 트리거 키워드
**오늘/어제/특정 날짜 업무 정리, 타임블럭, 캘린더 파일, CSV, ICS, 일정 생성**

### 세부 역량

#### 작업 캘린더 생성 (`/calendar`)
- **입력**: `--date YYYY-MM-DD` (기본: 어제)
- **수집**: `output/logs/staff_sessions.jsonl` (status=completed 필터) + Confluence 최근 수정 문서
- **처리**: 30분 단위 floor → 같은 블럭 병합 → 간략 제목 + 상세 본문 생성
- **출력**: `calendar-agent-system/output/staff_calendar_{YYYYMMDD}.csv` + `.ics`
- **규칙**: 시작 시간 :00/:30, 30분/60분 단위, [업무] 접두사 자동 포함
- **CLAUDE.md**: `calendar-agent-system/CLAUDE.md`

---

## 팀간 의존 관계

```
디스커버리팀
    └──► 기획팀 (Discovery 결과 → PRD 입력)
              └──► 기획팀 (PRD → Red Team 자동 → Phase 4.5 재검증 루프)

지식팀
    ├──► 기획팀 (Confluence 검색 → PRD 입력)
    └──► (모든 팀의 산출물 → Confluence 저장)

Cross-team Registry (output/_registry.json)
    ├── 기획팀 → 등록: prd, prd-v2, prd-v3, redteam, two-pager
    ├── PGM팀 → 등록: flash
    ├── 디스커버리팀 → 등록: discovery
    └── 다른 팀 → 조회하여 최신 산출물 자동 연결
        예: /red 실행 시 prd-v2 자동 조회
            /report 실행 시 flash 자동 조회
```

---

## 멀티에이전트 조율 패턴 적용 현황

> 참고: [Multi-Agent Coordination Patterns](https://claude.com/blog/multi-agent-coordination-patterns)

| 패턴 | 적용 위치 | 상세 |
|------|---------|------|
| **Generator-Verifier** | 기획팀 `/prd` | Phase 5(보강) → Phase 4.5(재검증) 루프, 최대 2회 |
| **Generator-Verifier** | 기획팀 `/two-pager` | two-pager-writer → two-pager-reviewer 내부 루프 |
| **Orchestrator-Subagent** | 비서실장 `/staff` | 모든 요청을 팀으로 분배 |
| **Agent Teams (병렬)** | PGM팀 `/pgm --full` | Step 2(Flash+회의록 분석), Step 3(publisher+minutes) 병렬 |
| **Agent Teams (병렬)** | 디스커버리팀 `/discovery` | Phase 1 시장분석 + 사용자 시뮬레이터 병렬 실행 예정 |
| **Shared State** | Cross-team Registry | `output/_registry.json` — 팀 간 산출물 공유 |
| **Message Bus (경량)** | 모든 스킬 완료 후 | `CONVENTIONS.md §7` 기준 next_actions 힌트 제공 |

---

---

## [데이터팀] Databricks 탐색 · 쿼리 · 분석

### 역할
Databricks Unity Catalog를 탐색하고, SQL을 실행하며, 데이터 기반 인사이트를 생성한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| 데이터 탐색 · 쿼리 · 분석 오케스트레이터 | Skill: `/databricks` | claude-sonnet-4-6 |
| Unity Catalog 구조 탐색 | Agent: `schema-explorer` (databricks-agent-system 내) | claude-haiku-4-5 |
| SQL 생성 · 실행 | Agent: `query-builder` (databricks-agent-system 내) | claude-sonnet-4-6 |
| 데이터 분석 · 인사이트 | Agent: `data-analyst` (databricks-agent-system 내) | claude-sonnet-4-6 |

### 트리거 키워드
Databricks, 데이터 탐색, 쿼리, SQL, Unity Catalog, 테이블 구조, 데이터 분석, KPI 조회,
DAU, MAU, 지표 조회, 코호트, 트렌드 분석, 데이터 확인

### 세부 역량

#### Unity Catalog 탐색 (`/databricks --explore`)
- **입력**: 탐색 대상 (없으면 전체 카탈로그)
- **출력**: `databricks-agent-system/output/explore_{YYYYMMDD}_{target}.md`
- **특징**: 카탈로그 → 스키마 → 테이블 계층 탐색, PM 관점 유용 테이블 식별

#### SQL 쿼리 실행 (`/databricks --query`)
- **입력**: 자연어 질문 또는 SQL 직접 입력
- **출력**: `databricks-agent-system/output/query_{YYYYMMDD}_{slug}.md`
- **안전 규칙**: SELECT만 허용, 1000행 LIMIT 자동 적용
- **특징**: 자연어 → SQL 자동 변환, 실행 전 SQL 미리보기

#### 데이터 분석 리포트 (`/databricks --analyze`)
- **입력**: 테이블명 + 분석 주제
- **출력**: `databricks-agent-system/output/analyze_{YYYYMMDD}_{주제}.md`
- **특징**: 자동 쿼리 3~5개 생성·실행, WoW/MoM 트렌드, 의사결정 제안
- **이니셔티브 연결**: `--initiative TM-XXXX` 옵션으로 목표 지표 연계

### 연결 설정 필요 (최초 1회)
`.env`에 `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_WAREHOUSE_ID` 추가
→ `databricks-agent-system/CLAUDE.md` §Step 0 참조

### 팀 내 표준 파이프라인
```
/databricks --explore               → 탐색 후 분석 대상 테이블 파악
/databricks --analyze {table} "주제" → 자동 분석 리포트
→ (선택) 인사이트 결과 → /prd 입력으로 활용
```

---

## [분석팀] 데이터 분석 인사이트

### 역할
사용자가 입력한 데이터(CSV/JSON 등)를 분석 유형에 따라 자동 분기하여 인사이트 리포트를 생성한다.
전처리·집계는 Haiku, 인사이트 도출은 Sonnet으로 역할을 분리한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| 분석 오케스트레이터 | Skill: `/analyst` | claude-haiku-4-5-20251001 |
| 데이터 전처리·집계 | Agent: `data-preprocessor` (analyst-agent-system 내) | claude-haiku-4-5-20251001 |
| 데이터 품질 검증·유형 감지 | Agent: `data-validator` (analyst-agent-system 내) | claude-haiku-4-5-20251001 |
| 시계열 트렌드 분석 | Agent: `trend-analyst` (analyst-agent-system 내) | claude-sonnet-4-6 |
| 세그먼트 비교 분석 | Agent: `segment-analyst` (analyst-agent-system 내) | claude-sonnet-4-6 |
| 퍼널 전환 분석 | Agent: `funnel-analyst` (analyst-agent-system 내) | claude-sonnet-4-6 |
| 코호트 리텐션 분석 | Agent: `cohort-analyst` (analyst-agent-system 내) | claude-sonnet-4-6 |
| A/B 테스트 평가 | Agent: `ab-test-analyst` (analyst-agent-system 내) | claude-sonnet-4-6 |
| **Root Cause 진단** | Skill: `/analyst --type diagnose` | claude-sonnet-4-6 |
| 통합 인사이트 생성 | Agent: `insight-synthesizer` (analyst-agent-system 내) | claude-sonnet-4-6 |

### 트리거 키워드
데이터 분석, 인사이트 도출, 트렌드 분석, 세그먼트 분석, 퍼널 분석, 코호트, 리텐션,
A/B 테스트, 실험 결과, CSV 분석, 지표 분석, DAU 트렌드, 전환율 분석,
**지표 하락, 이상 감지, 원인 분석, 왜 떨어졌나, Root Cause, 성과 이상, 급락, 급등**

### 세부 역량

#### 시계열 트렌드 분석 (`/analyst --type trend`)
- **입력**: 날짜 + 지표 컬럼이 있는 CSV
- **분석**: WoW/MoM 변화율, 고점/저점, 급등·급락 감지, 요일 패턴
- **출력**: `analyst-agent-system/output/analysis_trend_{YYYYMMDD}_{주제}.md`

#### 세그먼트 분석 (`/analyst --type segment`)
- **입력**: 그룹(카테고리) + 지표 컬럼이 있는 CSV
- **분석**: Star/Growth/Risk/Dormant 세그먼트 분류, 전략 제안
- **출력**: `analyst-agent-system/output/analysis_segment_{YYYYMMDD}_{주제}.md`

#### 퍼널 전환 분석 (`/analyst --type funnel`)
- **입력**: 단계 + 사용자 수 컬럼이 있는 CSV
- **분석**: 단계별 전환율, Critical Drop 탐지, 임팩트 시뮬레이션
- **출력**: `analyst-agent-system/output/analysis_funnel_{YYYYMMDD}_{주제}.md`

#### 코호트 리텐션 분석 (`/analyst --type cohort`)
- **입력**: 코호트 + 경과 기간 + 리텐션율 컬럼이 있는 CSV
- **분석**: 리텐션 매트릭스, Plateau 시점, 코호트별 비교
- **출력**: `analyst-agent-system/output/analysis_cohort_{YYYYMMDD}_{주제}.md`

#### A/B 테스트 평가 (`/analyst --type ab-test`)
- **입력**: 그룹(대조군/실험군) + 지표 컬럼이 있는 CSV
- **분석**: 지표 비교, 통계적 유의성 평가, 롤아웃 권고
- **출력**: `analyst-agent-system/output/analysis_abtest_{YYYYMMDD}_{주제}.md`

#### 자동 유형 감지 (`/analyst --type auto` 또는 생략)
- 데이터 구조를 보고 위 5가지 유형 중 자동 분기
- 감지 불가 시 `--type` 명시 요청

#### Root Cause 진단 (`/analyst --type diagnose`)
- **입력**: 이상 현상 설명 텍스트 또는 관련 지표 CSV
- **분석**: 증상 정의 → 패턴 분류 → 가설 3개 생성 → 검증 → 진단 보고 5단계
- **출력**: `analyst-agent-system/output/analysis_diagnose_{YYYYMMDD}_{주제}.md`
- **사용 예**: 지표 하락, 캠페인 성과 이상, 전환율 급변 원인 추적

### 팀 내 표준 파이프라인
```
데이터 파일 → input/ 폴더에 저장
→ /analyst --file input/파일명.csv --topic "분석 주제"
→ data-preprocessor (Haiku) → data-validator (Haiku)
→ 전문 분석 에이전트 (Sonnet) → insight-synthesizer (Sonnet)
→ output/ 리포트 생성

# 지표 이상 감지 시
→ /analyst --type diagnose --topic "왜 CTR이 떨어졌나"
→ 5단계 Root Cause 분석 → 권고 액션
```

---

## [협업팀] Slack 대화 조회 · 챗봇

### 역할
Slack 채널의 대화를 수집·요약하고, 결정 사항과 Action Item을 추출한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| Slack 조회 · 요약 오케스트레이터 | Skill: `/slack` | claude-sonnet-4-6 |
| 메시지 수집 | Agent: `slack-reader` (slack-agent-system 내) | claude-haiku-4-5 |
| 대화 요약 · AI 분석 | Agent: `conversation-summarizer` (slack-agent-system 내) | claude-sonnet-4-6 |

### 트리거 키워드
Slack, 슬랙, 채널 대화, 오늘 대화, 이번 주 대화, 결정 사항, Action Item, 슬랙 요약, 챗봇

### 세부 역량

#### 오늘 대화 조회 (`/slack --today [#채널]`)
- **입력**: 채널명 (없으면 기본 채널)
- **출력**: `slack-agent-system/output/slack_{YYYYMMDD}_{channel}_today.md`
- **특징**: 스레드 포함 수집, 결정사항·Action Item 자동 추출

#### 이번 주 대화 조회 (`/slack --week [#채널]`)
- **입력**: 채널명 (없으면 기본 채널)
- **출력**: `slack-agent-system/output/slack_{YYYYMMDD}_{channel}_week.md`
- **특징**: 월요일부터 현재까지, 주요 주제별 클러스터링

#### 키워드 검색 (`/slack --search "[키워드]" [#채널]`)
- **입력**: 검색 키워드 + 채널명
- **출력**: 검색 결과 목록 (최근 30일)

#### 메시지 발송 (`/slack --send [#채널] "[메시지]"`)
- **주의**: 발송 전 반드시 컨펌. 되돌리기 불가.

### /pgm 파이프라인 연계
- `/slack --week #match-pm` 결과 → `pgm-agent-system/output/slack_summary_{YYYYMMDD}.txt` 보완
- Flash Report 보완 자료로 활용 가능

### 연결 설정 필요 (최초 1회)
`.env`에 `SLACK_BOT_TOKEN` 추가, Bot을 채널에 초대
→ `slack-agent-system/CLAUDE.md` §Step 0 참조

---

## [디자인팀] Figma 화면 분석 · 설계서 생성

### 역할
Figma 파일을 분석하여 화면 설계서·UX 스펙·PRD 초안을 생성하고, 디자인과 기획을 연결한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| Figma 분석 오케스트레이터 | Skill: `/figma` | claude-sonnet-4-6 |
| Figma 파일 수집 | Agent: `figma-reader` → `figma-agent-system/.claude/agents/figma-reader/AGENT.md` | claude-haiku-4-5 |
| 화면 구조 분석 | Agent: `screen-analyst` → `figma-agent-system/.claude/agents/screen-analyst/AGENT.md` | claude-sonnet-4-6 |
| 화면 설계서 작성 | Agent: `spec-writer` → `figma-agent-system/.claude/agents/spec-writer/AGENT.md` | claude-sonnet-4-6 |

### 트리거 키워드
Figma, 피그마, 화면 분석, 화면 설계서, 스펙 문서, 디자인 분석, UX 카피, 프레임 분석,
화면 비교, Before/After, 컴포넌트 분석, 디자인 → PRD

### 세부 역량

#### 화면 구조 분석 (`/figma [URL]`)
- **입력**: Figma URL (파일 또는 특정 프레임)
- **출력**: `figma-agent-system/output/figma_analyze_{YYYYMMDD}_{주제}.md`
- **특징**: 페이지·프레임 목록, 사용자 플로우 추론, PM 체크리스트

#### 화면 설계서 생성 (`/figma [URL] --spec`)
- **입력**: Figma URL
- **출력**: `figma-agent-system/output/figma_spec_{YYYYMMDD}_{주제}.md`
- **특징**: 화면별 요소·인터랙션·상태·엣지케이스 문서화, Confluence 저장 연계

#### Figma → PRD 초안 (`/figma [URL] --prd`)
- **입력**: Figma URL
- **출력**: `prd-agent-system/output/prd_{YYYYMMDD}_{주제}.md`
- **특징**: 화면 분석 결과를 Rough Note로 변환 → 일반 PRD 파이프라인 실행
- **의존**: 기획팀 `/prd` 스킬과 자동 연계

#### 디자인 비교 (`/figma [URL1] --compare [URL2]`)
- **입력**: 두 Figma URL (이전/이후)
- **출력**: `figma-agent-system/output/figma_compare_{YYYYMMDD}_{주제}.md`
- **특징**: 추가/삭제/변경 화면 목록, 카피 변경 사항

#### UX 카피 추출 (`/figma [URL] --copy`)
- **입력**: Figma URL
- **출력**: `figma-agent-system/output/figma_copy_{YYYYMMDD}_{주제}.md`
- **특징**: 모든 텍스트 레이어 수집, 페이지·프레임별 정리

### 연결 설정 필요 (최초 1회)
`.env`에 `FIGMA_ACCESS_TOKEN` 추가
→ `figma-agent-system/CLAUDE.md` §Step 0 참조

### 팀 내 표준 파이프라인
```
/figma [URL]          → 화면 구조 파악
/figma [URL] --spec   → 설계서 생성 → Confluence 저장
/figma [URL] --prd    → PRD 초안 → /red → /epic
```

### 팀간 의존 관계
- `/figma --prd` 실행 시 → 기획팀 `/prd` 스킬 연계
- 화면 설계서 완성 후 → 지식팀 `confluence-writer` 저장

---

## [전략팀] 전략 자문 · 논의

### 역할
PM의 전략적 고민과 의사결정을 함께 논의한다.
Lenny's Podcast, Braze Docs, Garry Tan ETHOS를 레퍼런스로 삼아 근거 있는 전략 조언을 제공한다.

### 팀원 구성
| 역할 | 호출 방법 | 모델 |
|------|----------|------|
| 전략 자문 · 논의 | Skill: `/strategy` | claude-sonnet-4-6 |

### 트리거 키워드
전략, 방향성, 포지셔닝, 우선순위, 트레이드오프, 로드맵, 의사결정, CEP, Customer Engagement,
브레이즈, Braze, 리텐션, 성장 전략, GTM 전략, 제품 철학, 경쟁 전략, 논의, 고민, 어떻게 생각해,
**AI 개발 전략, 빌드 vs 벤더, AI 툴링 도입, 엔지니어링 생산성, 소수 팀 출시**

### 세부 역량

#### 전략 논의 (`/strategy`)
- **입력**: 전략적 질문 또는 고민 텍스트
- **출력**: 대화형 전략 논의 (필요 시 `output/strategy/` 저장)
- **지식 소스 1 — Lenny's Podcast**: `https://github.com/chatprd/lennys-podcast-transcripts`
  - 일반 전략, 로드맵, 리텐션, 성장, 조직, PM 방법론
- **지식 소스 2 — Braze Docs**: `https://github.com/braze-inc/braze-docs/tree/develop/_docs/_user_guide`
  - CEP / Customer Engagement Platform 관련 질문에 특화
- **지식 소스 3 — Garry Tan ETHOS**: `https://raw.githubusercontent.com/garrytan/gstack/main/ETHOS.md`
  - AI 기반 개발 전략, 소수 팀 고속 출시, 빌드 vs 벤더 의사결정, 빌더 마인드셋
- **분류 로직**:
  - CEP·Braze 관련 → Braze Docs 우선 탐색
  - AI 개발·엔지니어링 생산성 관련 → Garry Tan ETHOS 탐색
  - 일반 전략 → Lenny's Podcast 탐색
  - 복합 주제 → 해당 소스 모두 참조
- **특징**: 일방적 답변보다 "같이 생각해보는" 대화체, 구체적 선택지 제시
- **이니셔티브 연동**: `--initiative TM-XXXX` 옵션으로 컨텍스트 보강
- **실행**: `.claude/skills/strategy/SKILL.md` 워크플로우 따름

### 팀 내 표준 파이프라인
```
/strategy "CEP 로드맵 우선순위 어떻게 가져가야 해?"
/strategy --initiative TM-2061 "이 기능의 차별화 포인트는?"
/strategy "브레이즈는 Canvas를 어떻게 설계했어?"    → Braze Docs 자동 참조
/strategy "AI 툴링 도입 시 인소싱 vs SaaS 어떻게 봐야 해?" → Garry Tan ETHOS 자동 참조
```

### 팀간 의존 관계
- 전략 논의 결과 → 기획팀 `/prd` 입력으로 활용
- 전략 논의 결과 → 마케팅팀 `/gtm` 포지셔닝에 활용

---

## [마케팅운영팀] 앱푸시 캠페인 자동화

### 역할
마케팅 구좌관리 요청(비제스트 RAW)에서 소재를 선별하고, LLM으로 메시지를 생성하여
캠페인메타엔진 운영 시트 형식으로 출력.

### 트리거
- "[앱푸시 발송 운영] 시트에서 소재 선별해줘"
- "비제스트 RAW 기반으로 캠페인메타엔진 시트 채워줘"
- "앱푸시 메시지 자동 생성해줘"
- `/push-campaign`

### 입력
- `match-push-agent-system/input/bizest_raw.csv` — 비제스트 RAW (필수)
- `match-push-agent-system/input/brand_list.csv` — 브랜드 목록 (필수)
- `--date YYYY-MM-DD` — 발송일 (선택, 기본: 내일)

### 출력
- `match-push-agent-system/output/campaign_meta_{YYYYMMDD}_{HHmmss}.csv`
- 캠페인메타엔진 운영 시트 컬럼 형식

### 실행
```
/push-campaign
/push-campaign --date 2026-05-01
```

### 특징
- **완전 독립 패키지**: 마케팅팀에 독립 전달 가능
- **Pipeline 1**: 소재 선별 (취소/중복/미오픈 필터)
- **Pipeline 2**: Rule-based 컬럼 + LLM 메시지 (V1 혜택강조 / V2 브랜드감성) 생성
- **향후 확장**: Google Sheets 연동 (현재 파일 기반)
- **에이전트 디렉터리**: `match-push-agent-system/`

---

## 새 팀 추가 방법

현재 CAPABILITY_MAP에 없는 역량이 필요할 때:

1. `.claude/agents/{팀명}/AGENT.md` 생성 (서브에이전트)
   또는 `.claude/skills/{스킬명}/SKILL.md` 생성 (스킬)
2. 이 파일 해당 섹션에 팀 추가
3. `CLAUDE.md`의 라우팅 테이블에 행 추가

**참조 템플릿**: `input/initiatives/_template/` 구조 참고
