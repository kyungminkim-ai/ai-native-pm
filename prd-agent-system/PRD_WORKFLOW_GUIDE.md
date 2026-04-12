# PRD 스킬 & 워크플로우 가이드

> 마지막 업데이트: 2026-04-12 | Generator-Verifier 루프 추가 (v3)

---

## 개요

이 문서는 pm-studio의 PRD 생성 시스템 전체 구조, 각 에이전트의 역할, 워크플로우, 그리고 **AI가 읽고 코드를 생성할 수 있는 수준의 PRD**를 만들기 위한 작성 원칙을 정리한다.

---

## 시스템 구성 요소

| 구성 요소 | 파일 위치 | 역할 |
|---------|---------|------|
| `/prd` 스킬 | `.claude/skills/prd/SKILL.md` | 진입점. Rough Note → PRD 전체 파이프라인 실행 |
| 오케스트레이터 | `prd-agent-system/CLAUDE.md` | 전체 워크플로우 조율, 에이전트 순서 관리 |
| requirement-writer | `.claude/agents/requirement-writer/AGENT.md` | P0/P1 기능 요구사항 + Given/When/Then AC 작성 |
| ux-logic-analyst | `.claude/agents/ux-logic-analyst/AGENT.md` | Mermaid 플로우, 시스템 정책, 비정상 시나리오 |
| diagram-generator | `.claude/agents/diagram-generator/AGENT.md` | Mermaid → HTML 렌더링, SVG 시각화 |
| red-team-validator | `.claude/agents/red-team-validator/AGENT.md` | 비판적 검토 질문 30개+ 생성 |
| Phase 4.5 재검증 | `.claude/rules/phase45-reverify.md` | Critical 항목 해소 여부 확인 (Generator-Verifier 루프) |
| data-prd-writer | `.claude/agents/data-prd-writer/AGENT.md` | 데이터 파이프라인 전용 PRD |
| qa-agent | `.claude/agents/qa-agent/AGENT.md` | QA 테스트케이스 + 킥오프 브리핑 문서 |
| PRD 템플릿 | `references/prd_template.md` | 최종 PRD 구조 기준 |
| 메트릭 가이드 | `references/metric_guide.md` | North Star / Primary / Guardrail 지표 수립 기준 |

---

## 전체 워크플로우

```
사용자 Rough Note
        │
        ▼
[Phase 0: Pre-PRD 가정 검증] — 선택적
   Q1. 수요 증거 → Q2. 현재 대안 → Q3. 타깃 사용자 → Q4. MVP 범위 → Q5. 핵심 전제
   트리거: --validate 플래그 | 아이디어 수준 Rough Note | 이니셔티브 ID 없는 신규 주제
        │
        ▼
[Phase 0.5: 의도 구조화] — 조건부 자동 실행
   Rough Note → 의도 구조체 변환
   출력: 기능 유형 / 행위자 / 핵심 행동 / 시스템 책임 / 완료 판단 기준 / 제외 범위 / 미결 전제
        │
        ▼
[Phase 1: 전략 및 지표 수립]
   Context Loading (Confluence) + Metric Proposal (NSM / Primary / Guardrail)
        │
        ▼
[Phase 2: 서브 에이전트 순차 호출]
   ① requirement-writer → P0/P1 요구사항 + Given/When/Then AC
   ② ux-logic-analyst   → Mermaid 플로우 + 시스템 정책 + 비정상 시나리오
        │
        ▼
[Phase 2.5: 다이어그램 렌더링]
   diagram-generator → .mmd + .html 생성
        │
        ▼
[Phase 3: 통합 및 Self-Review]
   prd_template.md 구조로 통합 → 9개 항목 Self-Review 체크리스트 통과
   저장: output/prd_{YYYYMMDD}_{주제}.md
        │
        ▼
[Phase 4: Red Team 검증]
   red-team-validator → 비판적 질문 30개+ 생성
   저장: output/redteam_{YYYYMMDD}_{주제}.md
        │
        ▼
[Phase 5: Red Team 기반 PRD 보강]
   Critical 항목 전체 처리 + Important 50% 이상 처리
   저장: output/prd_{YYYYMMDD}_{주제}_v2.md
        │
        ▼
[Phase 4.5: Critical 항목 재검증] ← Generator-Verifier 루프 Verifier 단계
   각 Critical 항목의 RESOLVED / PARTIAL / UNRESOLVED 판정
   ┌── UNRESOLVED=0, PARTIAL≤2 → 통과 (최종: _v2.md)
   └── 미해소 항목 존재 (1회차) → Phase 5 재실행
           │
           ▼ (최대 1회 재보강)
       [Phase 5 2회차] → 저장: _v3.md
           │
           ▼
       [Phase 4.5 2회차] → 강제 통과 후 미해소 항목 사용자 보고 (최종: _v3.md)
        │
        ▼
[Confluence 업로드]
   PRD 최종본 + Red Team 질문지 자동 업로드
```

### 데이터 PRD 분기

Rough Note에서 데이터 파이프라인 관련 키워드 2개 이상 감지 시 → `data-prd-writer` 직접 호출

---

## AI 최적화 PRD 작성 원칙 (v2 기준)

### 원칙 1: AC는 반드시 Given/When/Then

PRD의 수용 기준(Acceptance Criteria)은 자동화 테스트로 직접 변환 가능한 수준으로 작성한다.

**형식:**
```
AC-{NNN}:
  Given: {초기 상태 및 전제 조건 — 구체적 수치/역할/상태 포함}
  When:  {트리거가 되는 사용자 행동 또는 시스템 이벤트}
  Then:
    - {기대 결과 1 — 독립적으로 검증 가능한 단위}
    - {기대 결과 2}
```

**올바른 예시:**
```
[P0-001] 사용자가 결제를 완료하면, 시스템은 멤버십 등급을 갱신한다.
AC-001:
  Given: 사용자 누적 구매금액 95,000원(Bronze), 장바구니 상품 30,000원
  When:  PG 승인 완료
  Then:
    - 마이페이지 등급 Silver로 즉시 갱신
    - 누적 금액 125,000원 표시
    - Silver 달성 팝업 1회 노출
```

**금지 예시:**
```
❌ 수용 기준: 결제 후 마이페이지에서 확인 가능  ← 수치 없는 단일 문장
❌ 수용 기준: 엔지니어와 협의하여 처리         ← 결정 회피
```

---

### 원칙 2: 비정상 시나리오 섹션 필수 명시

정상 플로우 외 모든 예외 상황을 Given/When/Then으로 명시한다.

**형식:**
```
| ID | 유형 | Given | When | Then | 자동화 |
| ABN-001 | 시스템 오류 | 결제 진행 중 | PG 30초 초과 | "결제 내역 확인" 버튼 + 안내 메시지 | ⚠️ 수동 |
```

**5가지 도출 관점:**
1. 입력값 오류 (빈값, 형식 불일치, 허용 범위 초과)
2. 권한/인증 오류 (비로그인, 권한 부족, 차단 계정)
3. 시스템 오류 (타임아웃, 외부 API 실패)
4. 비즈니스 로직 예외 (중복 신청, 한도 초과)
5. 동시성 문제 (동시 요청, 재고 경쟁)

---

### 원칙 3: "엔지니어와 협의" 금지 표현 목록

아래 표현은 PRD 어디에도 등장할 수 없다:

| 금지 표현 | 대안 |
|---------|------|
| "엔지니어와 협의 필요" | 결정 가능한 최소 기준 직접 명시 |
| "기술적으로 가능한 범위에서" | 기능 범위를 명확히 정의 |
| "추후 결정", "TBD" (단독) | Open Questions에 구체적 질문 형식으로 이전 |
| "알아서 처리", "적절히 대응" | 시스템이 해야 하는 구체적 행동 명시 |

**Open Questions 작성 기준:**
- 구체적 질문 형식: "~를 어떻게 처리할까?" / "~의 기준값은 얼마로 할까?"
- 반드시 담당자 + 결정 마감일 + 결정 시 영향받는 AC 번호 포함

---

### 원칙 4: Self-Review 체크리스트 (9개 항목)

Phase 3 통합 완료 후 반드시 통과해야 하는 항목:

| # | 검토 항목 | 통과 기준 |
|---|---------|---------|
| 1 | 구현 방법(How) 미포함 | API/DB/서버 기술 용어 감지 시 재작성 |
| 2 | AC 형식 준수 | 모든 AC가 Given/When/Then 형식 |
| 3 | AC 구체성 | Given에 수치/상태 포함, Then이 검증 가능한 단위 |
| 4 | 비정상 시나리오 완비 | 최소 5개 ABN 항목, 모호한 처리 방안 없음 |
| 5 | 결정 회피 표현 제거 | "엔지니어 협의", "TBD" 등 없음 |
| 6 | 목표-지표 정합성 | 비즈니스 목표 ↔ 지표 논리 연결 |
| 7 | 필수 섹션 완비 | 목표/요구사항/플로우/비정상시나리오/실행계획 존재 |
| 8 | Mermaid 문법 유효성 | diagram-generator 검증 통과 |
| 9 | Open Questions 형식 | 구체적 질문 + 담당자 + 영향 섹션 포함 |

---

## Phase 0.5 — 의도 구조화 상세

### 역할

PM의 Rough Note → 에이전트가 기계적으로 처리할 수 있는 구조체로 변환.

> **핵심 질문:** "무엇을 만드는가"가 아닌 **"어떤 상태가 되면 완성인가"**

### 의도 구조체 형식

```
[의도 구조화 결과]
─────────────────────────────────────────────
기능 유형:        신규 기능 / 기존 기능 개선 / 정책 변경
주요 행위자:      사용자 유형 (예: 비로그인 사용자 / 마케터 / 관리자)
핵심 행동:        사용자가 하는 것 (동사 중심)
시스템 책임:      시스템이 반드시 해야 하는 것 (결과 상태 중심)
완료 판단 기준:   어떤 수치/상태/화면이 되면 "완성"인가
제외 범위:        이번 스코프에서 다루지 않는 것 (명시적 열거)
미결 전제:        PRD 작성 전 반드시 결정되어야 하는 것
─────────────────────────────────────────────
```

---

## 산출물 경로

| 산출물 | 경로 |
|-------|------|
| 기능 PRD | `output/prd_{YYYYMMDD}_{주제}.md` |
| 보강된 PRD (1회차) | `output/prd_{YYYYMMDD}_{주제}_v2.md` |
| 재보강된 PRD (2회차, 최종) | `output/prd_{YYYYMMDD}_{주제}_v3.md` ← Phase 4.5 미통과 시만 생성 |
| Red Team 질문지 | `output/redteam_{YYYYMMDD}_{주제}.md` |
| 데이터 PRD | `output/prd-data_{YYYYMMDD}_{주제}.md` |
| Mermaid 플로우 | `output/diagrams/{주제}_{타입}_flow.mmd` |
| HTML 렌더링 | `output/diagrams/{주제}_{타입}.html` |
| QA 테스트케이스 | `output/qa_testcase_{YYYYMMDD}_{주제}.md` |

---

## 호출 방법

```bash
# 기본 호출
/prd [Rough Note 또는 TM-XXXX]

# 가정 검증 먼저 (Phase 0 강제 실행)
/prd [Rough Note] --validate

# 비서실장을 통한 복합 파이프라인
/staff TM-XXXX PRD 써서 Red Team 검증까지 해줘
```

---

## 버전 히스토리

| 버전 | 날짜 | 변경 내용 |
|------|------|---------|
| v3 | 2026-04-12 | Phase 4.5 Generator-Verifier 재검증 루프 추가 (최대 2회 반복, _v3.md 지원) |
| v2 | 2026-04-10 | AC → Given/When/Then, 비정상 시나리오 섹션 신설, 협의 금지 표현, Phase 0.5 의도 구조화 추가 |
| v1 | 2026-02 | 초기 버전 (Phase 0~5 기본 워크플로우) |
