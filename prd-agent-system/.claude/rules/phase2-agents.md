# Phase 2: 서브 에이전트 호출 규약

## Phase 0.5: 의도 구조화 (Intent Structuring)

### 실행 조건

| 조건 | 판단 |
|------|------|
| Rough Note가 서술형 문장 위주 | 자동 실행 |
| "~하면 좋겠다" "~같은 기능" 수준 | 자동 실행 (Phase 0과 함께) |
| TM-XXXX 있어도 완료 판단 기준 불명확 | 자동 실행 |
| Rough Note에 수치/상태/조건이 이미 명확 | 생략 가능 |

### 출력 형식 (Phase 2 에이전트 입력 스펙으로 사용)

```
[의도 구조화 결과]
─────────────────────────────────────────────
기능 유형:        {신규 기능 / 기존 기능 개선 / 정책 변경 / 플랫폼/API}
주요 행위자:      {사용자 유형 — 예: 비로그인 / 마케터 / 개발자 / 관리자}
핵심 행동:        {사용자가 하는 것 — 동사 중심}
시스템 책임:      {시스템이 반드시 해야 하는 것 — 결과 상태 중심}
완료 판단 기준:   {어떤 수치/상태가 되면 "완성"인가 — 수치·화면·데이터 포함}
제외 범위:        {이번 스코프에서 다루지 않는 것 — 명시적 열거}
미결 전제:        {PRD 작성 전 반드시 결정되어야 하는 것}
─────────────────────────────────────────────
```

---

## [플랫폼 PRD] 신규 환경 확인 게이트

**PRD 유형이 플랫폼/API인 경우에만** requirement-writer 호출 전 아래 사항을 확인한다.
미확인 항목은 Open Questions에 기록 후 진행.

```
[플랫폼 PRD 환경 게이트]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ 신규 워크스페이스 / 환경 구성 필요 여부
  → Yes: 인프라 선행 작업 목록 7-4에 먼저 작성
□ AWS 크로스 계정 네트워크 연동 필요 여부
  → Yes: IAM Role 위임 + Security Group 허용 CIDR 확인 필요 명시
□ 외부 플랫폼 어댑터 연동 여부 (Braze, Amplitude 등)
  → Yes: 외부 API 스펙 + 인증 방식 확정 후 착수 명시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ 확인 완료 후 requirement-writer 호출
```

---

## Phase 2-A: requirement-writer 호출

Phase 1 완료 후 첫 번째로 호출. **반드시 순차 실행 (ux-logic-analyst보다 먼저).**

```
Task: 아래 전략 컨텍스트와 의도 구조체를 바탕으로 기능 요구사항을 작성해줘.
에이전트: prd-agent-system/.claude/agents/requirement-writer/AGENT.md

작성 규칙:
- 서브시스템 그룹 [A][B][C] 방식으로 묶어 작성 (3개 이상 요구사항이 같은 기능 영역이면 그룹화)
- 각 요구사항에 Input / Output / 비즈니스 규칙 / 시스템 인터페이스 포함
- AC는 반드시 Given/When/Then 형식 (단일 문장 금지)
- P0/P1/P2/비개발 태그 부여
- "엔지니어와 협의", "TBD", "추후 결정" 표현 금지
- 절대 구현 방법(How) 포함하지 말 것. 기능의 존재(What)만 명세
- Non-Goals(Out of Scope) 작성 시 Phase 0 Q2 답변(현재 대안)을 각 항목의 '현재 운영 대안' 컬럼에 연결할 것
  ※ Phase 0를 건너뛴 경우: "{현재 방법 확인 필요}"로 표기

--- 전략 컨텍스트 ---
{Phase 1 결과: 기능 배경, 목표, 지표, Rough Note 요약}

--- Phase 0 Q2 답변 (현재 대안 / Status Quo) ---
{Phase 0 Q2 답변 전문 — 없으면 "Phase 0 미실행"으로 표기}

--- 의도 구조체 (Phase 0.5 결과) ---
{의도 구조화 결과 전문 — 완료 판단 기준, 제외 범위 포함}
```

---

## Phase 2-B: ux-logic-analyst 호출

requirement-writer **완료 후** 호출. **UX 플로우 + 시스템 정책만 담당. EX 시나리오는 Phase 2C.**

```
Task: 아래 기능 요구사항을 바탕으로 Mermaid.js 플로우와 시스템 정책을 작성해줘.
에이전트: prd-agent-system/.claude/agents/ux-logic-analyst/AGENT.md

작성 규칙:
- P0 기능 하나당 최소 1개 Mermaid 차트 (정상/예외 플로우 별도 차트), 최소 2개 정책
- diagram-generator 스킬로 Mermaid 코드 문법을 반드시 검증할 것
- 플로우 테이블 (No. / 시점 / 작업 / 상세 내용) 함께 작성
- 비정상 시나리오(EX-NNN)는 작성하지 말 것 → Phase 2C에서 처리

--- 기능 요구사항 ---
{requirement-writer 반환 결과 전문}
```

---

## Phase 2-C: edge-case-analyst 호출

ux-logic-analyst **완료 후** 호출. requirement-writer 산출물 기반으로 비정상 시나리오 전담.

```
Task: 아래 기능 요구사항을 바탕으로 비정상 시나리오(EX-NNN), EX→Mermaid 노드 매핑,
      FR-EX 크로스레퍼런스를 도출해줘.
에이전트: prd-agent-system/.claude/agents/edge-case-analyst/AGENT.md

작성 규칙:
- 5가지 관점(INPUT/AUTH/SYS/BIZ/RACE) 각 1개 이상, 전체 최소 5개
- 각 EX를 EXCEPTIONAL(시스템 결함) / PREDICTABLE(비즈니스 예상 결과)로 분류
  · EXCEPTIONAL → ERROR_LOG + 알람 ✅ 필수
  · PREDICTABLE → DROP_BIZ_LOG 또는 WARN_LOG, 알람은 임계값 기반(⚠️) 또는 불필요(❌)
- BIZ 관점 PREDICTABLE 중 파이프라인 말단에서 Drop 확정되는 케이스 → Validate First 가능성 검토
- EX→Mermaid 노드 매핑 테이블 함께 생성 (Phase 2.5 diagram-generator에 전달)
- FR-EX 크로스레퍼런스 테이블 생성 (Phase 3 Step 3-A에서 `관련 EX` 컬럼 병합에 사용)
- "엔지니어 판단", "알아서 처리", "추후 논의", "오류 로그" (PREDICTABLE에 단독 기재) 표현 절대 금지

--- 기능 요구사항 ---
{requirement-writer 반환 결과 전문}

--- Phase 1 지표 목록 ---
{North Star + Primary 지표}
```
