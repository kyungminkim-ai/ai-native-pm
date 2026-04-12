# Phase 5: Red Team 기반 PRD 보강 (생략 불가)

Phase 4 완료 직후, Red Team 결과를 반영하여 원본 PRD를 보강한다.

---

## 보강 절차

1. `output/redteam_{YYYYMMDD}_{주제}.md`에서 **Critical** 항목을 모두 추출
2. 각 Critical 질문을 원본 PRD `output/prd_{YYYYMMDD}_{주제}.md`의 관련 섹션에 대입
3. 아래 기준으로 처리:

| 상황 | 처리 방법 |
|------|----------|
| 답변 가능 (데이터·논리 확보) | 해당 섹션 직접 보강하여 재작성 |
| 판단 필요 (작성자만 알 수 있는 정보) | 해당 위치에 코멘트 삽입 (아래 형식) |
| 범위 외 (이번 스코프에서 다루지 않는 사항) | Open Questions 섹션에 추가 |

---

## 보강 코멘트 형식

**Critical:**
```markdown
> [!COMMENT] **Red Team 보강 필요** _(Critical)_
> 질문: {Red Team 원문 질문}
> 현재 상태: 이 섹션에서 해당 질문에 대한 답이 없습니다.
> 보강 방향: {어떤 내용을 추가하면 좋은지 구체적 가이드}
> 예시: "{작성자가 채워야 할 내용의 예시 문장}"
```

**Important:**
```markdown
> [!COMMENT] **Red Team 보강 권장** _(Important)_
> 질문: {Red Team 원문 질문}
> 현재 상태: ...
> 보강 방향: ...
```

---

## 보강 완료 기준

- Critical 항목 전체 처리 (보강 또는 코멘트 삽입)
- Important 항목 50% 이상 처리
- 보강된 파일은 `output/prd_{YYYYMMDD}_{주제}_v2.md`로 저장

## 다음 단계

Phase 5 완료 즉시 **Phase 4.5 (Critical 항목 재검증)** 를 자동 실행한다.
→ `.claude/rules/phase45-reverify.md` 참조

Phase 4.5에서 미해소 항목이 있으면 Phase 5를 재실행 (최대 2회차, 출력: `_v3.md`).
Phase 4.5에서 통과하면 Confluence 업로드로 진행한다.
