# Phase 3: 통합 및 Self-Review

## Step 3-A: PRD 초안 작성

`references/prd_template.md` 구조를 따라 Phase 1~2 결과물을 통합한다.

| Phase 결과물 | 채울 PRD 섹션 |
|------------|-------------|
| Phase 0/0.5 배경/문제 | **(1) 배경 및 문제** — Pain Point 테이블, 용어 정의, 핵심 질문 |
| Phase 1 목표 + 지표 | **(2) 목표 / Business Impact** — Scope + Metrics 테이블 (Baseline 컬럼 포함) |
| Phase 1 전략 방향 | **(3) High Level Solution** |
| Phase 2 UX 플로우 | **(4-1) User Flow** — Mermaid 차트 + 플로우 테이블 |
| Phase 2 기능 요구사항 | **(4-2) Functional Requirements** — 서브시스템 그룹 [A][B][C] 포맷 |
| Phase 2 비기능 요건 | **(4-3) Non-Functional Requirements** |
| Phase 2 시스템 정책 | **(5-1) 정책 상세** |
| Phase 2 예외 케이스 | **(5-2) Edge Cases & Error Handling** |
| 디자인 링크 | **(6) 디자인 링크** (없으면 "{미정}"으로 표기) |
| 실행 계획 | **(7) 실행 계획** — Timeline + Launch Plan + Open Questions + **작업 시 주의사항** |
| 참고 자료 | **(8) Appendix** — 참고 데이터 + 관련 문서 |

헤더 테이블(Version, 구성원, Milestone)은 알 수 있는 정보로 채우고, 미정 항목은 공란 대신 "{미정}"으로 명시.

---

## Step 3-B: Self-Review 체크리스트 (생략 불가)

| 검토 항목 | 통과 기준 |
|----------|----------|
| 구현 방법(How) 미포함 | "API", "DB", "서버", "개발" 등 기술 용어 감지 시 해당 문장 삭제 후 재작성 |
| AC 형식 준수 | 모든 요구사항의 AC가 Given/When/Then 형식인가. 단일 문장 AC 발견 시 재작성 |
| AC 구체성 | Given에 수치/상태가 포함되어 있는가. "확인 가능" 수준의 모호한 Then 재작성 |
| 비정상 시나리오 완비 | 최소 5개 EX-XXX 항목 존재, Given/When/Then 처리 방안 포함 |
| 결정 회피 표현 제거 | "엔지니어와 협의", "추후 결정", "TBD", "알아서" 감지 시 결정하거나 OQ로 이전 |
| 목표-지표 정합성 | Phase 1 비즈니스 목표와 지표가 논리적으로 연결되는가 |
| Baseline 기재 | Metrics 테이블의 Baseline 컬럼이 채워졌는가 (없으면 OQ 처리) |
| 필수 섹션 완비 | 목표/요구사항/플로우/비정상시나리오/실행계획 모두 존재하는가 |
| Mermaid 문법 유효성 | diagram-generator 스킬 검증 통과 여부 |
| Open Questions 형식 | 각 항목이 구체적 질문 형식 + 담당자 + 마감일 + 결정 시 영향 섹션 포함 |

**모든 체크 통과 후** `output/prd_{YYYYMMDD}_{주제}.md`에 저장.
