# Phase 4.5: Critical 항목 재검증 (Generator-Verifier 루프)

Phase 5 보강 완료 직후 자동 실행한다. Critical 항목이 실제로 해소되었는지 확인하는
**Generator-Verifier 패턴의 Verifier 단계**다.

최대 2회 루프를 허용한다:
```
Phase 4 → Phase 5 (1회차 → _v2.md)
       → Phase 4.5 (1회차 검증)
           ├─ 통과 → Confluence 업로드
           └─ 미해소 → Phase 5 (2회차 → _v3.md)
                    → Phase 4.5 (2회차 검증) → 강제 통과 후 보고
```

---

## 재검증 절차

1. `output/redteam_{YYYYMMDD}_{주제}.md`에서 **Critical** 항목 전체 목록 추출
2. `output/prd_{YYYYMMDD}_{주제}_v2.md` (2회차는 `_v3.md`)를 전문 검토
3. 각 Critical 항목에 대해 아래 기준으로 판정:

| 판정 | 기준 |
|------|------|
| ✅ RESOLVED | 해당 Critical 질문에 대한 명확한 답변이 PRD 본문에 추가됨 (수치·조건·처리 방안 포함) |
| ⚠️ PARTIAL | 답변이 시도되었으나 구체성 부족 (수치 없음, 조건 불명확, 예시만 존재) |
| ❌ UNRESOLVED | `[!COMMENT]` 코멘트만 삽입되고 실제 내용은 미작성 상태 |

---

## 루프 판단 기준

| 상황 | 처리 |
|------|------|
| UNRESOLVED = 0 이고 PARTIAL ≤ 2 | **통과** → Confluence 업로드 진행 |
| UNRESOLVED > 0 또는 PARTIAL > 2 (1회차) | Phase 5 **재실행** → 2회차 진입 |
| UNRESOLVED > 0 또는 PARTIAL > 2 (2회차) | **강제 통과** → 미해소 항목 목록을 사용자에게 보고 후 업로드 |

> **이유**: 무한 루프 방지. 2회차 이후에도 미해소 항목은 사용자가 직접 판단해야 하는 정보 공백(데이터 부재·정책 미결)일 가능성이 높다.

---

## 재검증 출력 형식

```
[Phase 4.5 재검증] {N}회차
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Critical 항목 재검증: {RESOLVED_COUNT}/{TOTAL_COUNT} 해소

✅ RESOLVED ({n}개):
  - [C-001] {질문 요약} → {어느 섹션에서 어떻게 해소됐는지 1줄}

⚠️ PARTIAL ({n}개):
  - [C-003] {질문 요약} → {어느 부분이 아직 부족한지}

❌ UNRESOLVED ({n}개):
  - [C-005] {질문 요약} → {아직 미처리 상태}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
판정: {통과 | Phase 5 2회차 진행 | 강제 통과 (미해소 {n}개 사용자 확인 필요)}
```

---

## 재보강 시 버전 관리

| 회차 | Phase 5 입력 | 출력 파일 | Confluence 업로드 기준 |
|------|------------|---------|----------------------|
| 1회차 | `prd_{날짜}_{주제}.md` | `_v2.md` | _v2.md |
| 2회차 (재보강) | `_v2.md` + Phase 4.5 미해소 목록 | `_v3.md` | _v3.md |

Phase 5 2회차 호출 시, 미해소 항목 목록을 **추가 입력**으로 제공한다:

```
Task: 아래 PRD의 미해소 Critical 항목을 집중 보강해줘.
대상 파일: output/prd_{날짜}_{주제}_v2.md
출력 파일: output/prd_{날짜}_{주제}_v3.md

[미해소 Critical 항목]
{Phase 4.5 UNRESOLVED/PARTIAL 목록 전문}

기존 RESOLVED 항목은 건드리지 말고, 미해소 항목만 집중 보강할 것.
```

---

## 완료 기준

- 1회차 통과 또는 2회차 강제 통과 후 → `[Phase 4.5 완료]` 선언
- Confluence 업로드 단계로 진행
