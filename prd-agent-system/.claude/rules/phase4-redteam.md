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
