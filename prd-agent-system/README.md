# PRD Agent System

Rough Note 하나에서 시작해 전략 수립 → 요구사항 → UX 로직 → 예외 케이스 → 다이어그램 → Red Team 검증 → Confluence 업로드까지 자동화하는 멀티에이전트 PRD 파이프라인.

---

## 전체 워크플로우

```
입력: Rough Note / TM-XXXX / Confluence URL
       │
       ▼
┌──────────────────────────────────────────────────┐
│ [Phase 0] 가정 검증 (조건부)                        │  phase0-validation.md
│   gstack 7개 질문 + 스코프 모드 선택                 │
│   EXPANSION / SELECTIVE / HOLD / REDUCTION        │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│ [Phase 0.5] 의도 구조화 (조건부)                    │  phase2-agents.md §0.5
│   기능 유형 / 핵심 행동 / 완료 기준 / 제외 범위       │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│ [Phase 1] 전략 및 지표 수립                         │  phase1-strategy.md
│   Confluence 조회 → Amplitude Baseline 수집        │
│   North Star / Primary / Guardrail 지표 확정       │
└──────────────────────┬───────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
┌─────────────┐ ┌────────────┐ ┌────────────────────┐
│ [Phase 2a]  │ │ [Phase 2b] │ │   [Phase 2c]       │
│ requirement │ │    ux-     │ │  edge-case-analyst  │
│   -writer   │ │  logic-    │ │                    │
│             │ │  analyst   │ │  EX-NNN 5관점 도출  │
│ P0/P1 요구사항│ │            │ │  EX→노드 매핑 생성  │
│ AC(G/W/T)  │ │ Mermaid 플로│ │                    │
│            │ │ POL-NNN    │ │                    │
└──────┬──────┘ └─────┬──────┘ └────────┬───────────┘
       └──────────────┴─────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│ [Phase 2.5] diagram-generator                    │  phase25-diagrams.md
│   Mermaid → HTML 렌더링                            │
│   EX-NNN → Mermaid 에러 노드 1:1 매핑 검증         │
│   output/diagrams/*.html                          │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│ [Phase 3] 통합 + Self-Review                      │  phase3-self-review.md
│   PRD 초안 작성 (prd_template.md 기준)             │
│   LLM 12개 항목 체크리스트                          │
│   prd_lint.py 자동 검증 (구조적 무결성)              │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│ [Phase 4] Red Team 검증                           │  phase4-redteam.md
│   30개+ 비판 질문 / PRD 유형별 가중치 적용           │
│   기능PRD: 비즈니스 로직 집중                        │
│   플랫폼PRD: 하위 호환성 집중                        │
│   데이터PRD: 데이터 유실/SLA 집중                    │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│ [Phase 5] PRD 보강                                │  phase5-reinforce.md
│   Critical 항목 → 본문 보강 또는 코멘트 삽입         │
│   output/prd_{날짜}_{주제}_v2.md 저장              │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│ [Phase 4.5] Critical 재검증                       │  phase45-reverify.md
│   Generator-Verifier 루프 (최대 2회)               │
│   RESOLVED / PARTIAL / UNRESOLVED 판정            │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
                  Confluence 업로드
              output/prd_{날짜}_{주제}_v2.md
```

> **데이터 PRD**: 파이프라인/스키마/SLA 키워드 감지 시 `data-prd.md`로 분기
> **플랫폼/API PRD**: API/엔드포인트/SDK 키워드 감지 시 `platform-prd.md` 추가 섹션 병행

---

## 컴포넌트 카탈로그

### Agents

| 에이전트 | Phase | 역할 | 입력 → 출력 |
|---------|-------|------|-----------|
| `requirement-writer` | 2a | P0/P1 요구사항 + AC(Given/When/Then) 작성 | 전략 컨텍스트 → 기능 요구사항 |
| `ux-logic-analyst` | 2b | Mermaid 플로우 + 시스템 정책(POL-NNN) | 기능 요구사항 → 플로우 차트 + 정책 |
| `edge-case-analyst` | 2c | EX-NNN 비정상 시나리오 + EX→Mermaid 노드 매핑 | 기능 요구사항 → EX 테이블 + 매핑 스펙 |
| `diagram-generator` | 2.5 | Mermaid HTML 렌더링 + EX 노드 매핑 검증 | Mermaid 코드 → output/diagrams/*.html |
| `red-team-validator` | 4 | 30개+ 비판적 검증 질문 생성 | PRD 파일 → redteam_*.md |
| `data-prd-writer` | — | 데이터 파이프라인 PRD 작성 (6섹션) | Rough Note → prd-data_*.md |
| `qa-agent` | — | QA 테스트케이스 + PM 킥오프 브리핑 | PRD 파일 → qa_testcase_*.md |

### Rules (Phase별 실행 규칙)

| 파일 | Phase | 핵심 역할 |
|------|-------|---------|
| `phase0-validation.md` | 0 | gstack 7개 가정 검증 + 스코프 모드 선택 |
| `phase1-strategy.md` | 1 | Confluence 조회, Amplitude Baseline, 지표 수립 |
| `phase2-agents.md` | 0.5 / 2A / 2B / 2C | 의도 구조화 + 3개 에이전트 호출 규약 |
| `phase25-diagrams.md` | 2.5 | diagram-generator 호출 + EX→노드 매핑 검증 |
| `phase3-self-review.md` | 3 | PRD 통합 + LLM Self-Review + prd_lint 검증 |
| `phase4-redteam.md` | 4 | Red Team 호출 + PRD 유형별 검증 가중치 |
| `phase5-reinforce.md` | 5 | Critical 항목 보강 + _v2.md 저장 |
| `phase45-reverify.md` | 4.5 | Generator-Verifier 루프 (최대 2회) |
| `data-prd.md` | — | 데이터 PRD 분기 워크플로우 |
| `platform-prd.md` | — | 플랫폼/API PRD 추가 섹션 규칙 |

### Skills

| 스킬 | 사용 시점 | 역할 |
|------|---------|------|
| `confluence-skill` | Phase 1 | Confluence 관련 문서 조회·참조 |
| `diagram-generator` | Phase 2.5 | Mermaid → HTML 렌더링 (render.py / render_html.py) |

---

## 파일 구조

```
prd-agent-system/
├── CLAUDE.md                    # 오케스트레이터 — 진입점, 하네스 운영 원칙 포함
├── README.md                    # 이 파일
├── PRD_WORKFLOW_GUIDE.md        # PRD 작성 원칙 가이드
│
├── .claude/
│   ├── agents/
│   │   ├── requirement-writer/   # Phase 2a — P0/P1 요구사항
│   │   ├── ux-logic-analyst/     # Phase 2b — Mermaid 플로우 + 정책
│   │   ├── edge-case-analyst/    # Phase 2c — EX-NNN 비정상 시나리오 [신규]
│   │   ├── diagram-generator/    # Phase 2.5 — HTML 렌더링
│   │   ├── red-team-validator/   # Phase 4 — 검증 질문
│   │   ├── data-prd-writer/      # 데이터 PRD 전용
│   │   └── qa-agent/             # QA 테스트케이스
│   │
│   ├── rules/                    # Phase별 실행 규칙 (오케스트레이터 참조)
│   │   ├── phase0-validation.md
│   │   ├── phase1-strategy.md
│   │   ├── phase2-agents.md      # Phase 0.5 + 2A + 2B + 2C 호출 규약
│   │   ├── phase25-diagrams.md
│   │   ├── phase3-self-review.md
│   │   ├── phase4-redteam.md
│   │   ├── phase5-reinforce.md
│   │   ├── phase45-reverify.md
│   │   ├── data-prd.md
│   │   └── platform-prd.md
│   │
│   └── skills/
│       ├── confluence-skill/     # Confluence 조회 규약
│       └── diagram-generator/    # 렌더링 스크립트 래퍼
│
├── references/
│   ├── prd_template.md           # PRD 작성 템플릿
│   └── metric_guide.md           # 지표 수립 가이드
│
├── scripts/
│   └── prd_lint.py               # PRD 구조 자동 검증 (Phase 3 Step 3-C)
│
└── output/                       # 모든 생성 산출물
    ├── prd_{날짜}_{주제}.md        # PRD 초안
    ├── prd_{날짜}_{주제}_v2.md    # Red Team 보강본 (최종 배포)
    ├── redteam_{날짜}_{주제}.md   # Red Team 질문지
    ├── prd-data_{날짜}_{주제}.md  # 데이터 PRD
    └── diagrams/
        ├── {주제}_{타입}.mmd
        └── {주제}_{타입}.html
```

---

## 하네스 운영 원칙

파이프라인 전체의 품질을 보장하는 6가지 내장 제어 장치.

| # | 원칙 | 어디서 | 어떻게 강제하는가 |
|---|------|--------|----------------|
| H-1 | **지표 → 로깅 AC 강제** | requirement-writer | Phase 1 지표(North Star/Primary) → AC Then 절에 이벤트 로깅 구문 포함 여부 검증. 누락 시 OQ-LOG-NNN 자동 생성 |
| H-2 | **스코프 고정** | 오케스트레이터 | Phase 0.5 "제외 범위" → Phase 2a Non-Goals 3컬럼 테이블에 100% 이식 확인. 미이식 시 재작성 |
| H-3 | **EX → Mermaid 노드 매핑** | edge-case-analyst + diagram-generator | EX-NNN 5관점 매핑 테이블 → Phase 2.5 에러 플로우 노드 1:1 연결. 누락 시 Phase 2.5 통과 차단 |
| H-4 | **prd_lint 자동 검증** | scripts/prd_lint.py | Phase 3 완료 후 Python 스크립트 강제 실행. AC 구조, EX 관점 커버리지, 금지 표현, 실행 계획 공백 등 6개 항목 코드로 검사 |
| H-5 | **Red Team 유형별 가중치** | red-team-validator | PRD 유형 자동 감지 → 기능(비즈니스 로직) / 플랫폼(하위 호환) / 데이터(SLA/유실)로 검증 포커스 전환 |
| H-6 | **Phase 간 상태 전달** | 오케스트레이터 | Phase 1 지표 목록 + Phase 0.5 의도 구조체 + Phase 2c EX 매핑을 다음 Phase 에이전트에 명시적 전달 |

---

## 빠른 시작

```
# 기본 PRD 작성
/prd [Rough Note 또는 TM-XXXX]

# 가정 검증부터 시작
/prd --validate [Rough Note]

# 데이터 파이프라인 PRD (키워드 감지 시 자동 분기)
/prd [파이프라인/스키마 설명]

# PRD 검증만
/red [PRD 파일 경로]
```

---

## 산출물 위치

| 유형 | 경로 |
|------|------|
| PRD 초안 | `output/prd_{날짜}_{주제}.md` |
| PRD 최종 (Red Team 보강) | `output/prd_{날짜}_{주제}_v2.md` |
| Red Team 질문지 | `output/redteam_{날짜}_{주제}.md` |
| 데이터 PRD | `output/prd-data_{날짜}_{주제}.md` |
| 다이어그램 | `output/diagrams/{주제}_{타입}.html` |
