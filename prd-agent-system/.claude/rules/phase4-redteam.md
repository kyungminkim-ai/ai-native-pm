# Phase 4: Red Team Validation (생략 불가)

Phase 3 완료 직후 `red-team-validator` 서브에이전트를 호출한다.

에이전트 스펙: `prd-agent-system/.claude/agents/red-team-validator/AGENT.md`

---

## 호출 형식

```
Task: 아래 PRD를 비판적으로 검토하여 Red Team 검증 질문지를 생성해줘.
에이전트: prd-agent-system/.claude/agents/red-team-validator/AGENT.md

입력 PRD: output/prd_{YYYYMMDD}_{주제}.md
출력 파일: output/redteam_{YYYYMMDD}_{주제}.md

PRD를 옹호하거나 설명하지 말고, 오직 공격하고 의심하는 질문만 생성할 것.
```

---

## 완료 기준

- 질문 총 수 ≥ 30개 → Phase 4 완료, Phase 5로 진행
- 질문 총 수 < 30개 → 미달 카테고리 식별 후 재생성 요청

## 카테고리

A. 문제 정의 / B. 메트릭 / C. 사용자 멘탈모델 / D. 기능 요구사항
E. UX 플로우 / F. 시스템 정책 / G. 엣지케이스 / H. 실행 계획 / I. Open Questions

각 카테고리 최소 3개.

---

## PRD 유형별 검증 가중치

입력 PRD 유형을 CLAUDE.md 1-A 판별 기준으로 감지한 후, 아래 가중치를 적용한다.

| PRD 유형 | 집중 카테고리 (최소 5개) | 추가 검증 포인트 |
|---------|----------------------|----------------|
| **기능 PRD** | D. 기능 요구사항 / B. 메트릭 / G. 엣지케이스 | 비즈니스 로직 예외 커버리지, AC 수치 구체성, 로깅 이벤트 누락 여부 |
| **플랫폼/API PRD** | F. 시스템 정책 / G. 엣지케이스 / H. 실행 계획 | 하위 호환성(Backward Compatibility), Deprecation 정책, 버저닝 전략, Rate Limit, 외부 팀 선행 작업 |
| **데이터 PRD** | G. 엣지케이스 / H. 실행 계획 / F. 시스템 정책 | 데이터 유실 방지, SLA 정의(신선도·가용성·정합성), CDC/마이그레이션 플랜, 롤백 시나리오 |

**플랫폼/API PRD 전용 추가 질문 (필수 포함):**
- 이 API가 변경될 때 기존 클라이언트는 어떤 영향을 받는가? Deprecation 공지 방법과 기간은?
- 버저닝 전략(/v1/, 헤더 기반 등)이 정의되지 않으면 어떤 문제가 발생하는가?
- Rate Limit 초과 시 클라이언트의 Retry 전략은 정의되었는가?

**데이터 PRD 전용 추가 질문 (필수 포함):**
- 파이프라인 장애 시 데이터 유실 범위와 복구 절차는 정의되었는가?
- SLA(신선도, 가용성) 위반 시 알림 및 에스컬레이션 경로는 있는가?
- CDC에서 배치 업로드로 전환하는 경우 히스토리 데이터 이전 계획은 있는가?
