---
description: PRD·기획안에 대한 Red Team 검증, 가정 도전 질문 생성, 스코프 방향(확장/축소/유지) 결정을 수행하는 검증 에이전트
---

# /red — Red Team Validator 에이전트

## 모델

`claude-sonnet-4-6`

## 사용법

```
/red [PRD 파일 경로] [--scope expand|selective|hold|reduce]
```

### `--scope` 옵션 (Scope Calibration)

Red Team 검증 시 **스코프 방향성**을 함께 검토한다. 기본값은 `hold`.

| 모드 | 의미 | 주요 질문 |
|------|------|---------|
| `expand` | 이 PRD, 더 크게 가도 되지 않나? | 10배 임팩트를 낼 확장 방향은? 빠진 사용자 세그먼트는? |
| `selective` | 기본 유지, 고가치 확장 포인트 발굴 | 2x 노력으로 추가할 수 있는 기능은? 포기한 것 중 재고 가능한 건? |
| `hold` | 현재 스코프에서 완성도 극대화 (기본값) | 논리 빈틈, 엣지케이스, 미결 가정은? |
| `reduce` | 과설계 여부 검토, 핵심만 남기기 | MVP 없이도 되는 기능은? 단계 분리 가능한 범위는? |

scope 결과는 Red Team 질문지 마지막에 **Scope Calibration** 섹션으로 별도 출력한다.

## 실행 규칙

1. `prd-agent-system/.claude/agents/red-team-validator/AGENT.md`를 읽어 에이전트 역할과 실행 순서를 파악한다.
2. 사용자가 제공한 args를 파싱하여 PRD 입력 방식과 scope 모드를 결정한다:
   - **Confluence 파일 경로가 지정된 경우**: 해당 파일을 직접 읽어 마크다운으로 변환한 뒤 `prd-agent-system/.claude/agents/red-team-validator/input/`에 저장하고 검증을 진행한다.
   - **경로가 없는 경우**: `confluence-reader` 서브에이전트를 호출하여 관련 PRD를 검색·취득한 뒤 동일 `input/` 폴더에 저장한다. 검색 대상 키워드는 사용자 입력에서 추출하거나, 없으면 사용자에게 주제를 확인한다.
   - **`input/` 폴더에 이미 파일이 있는 경우**: 해당 파일을 재사용하고 사용자에게 어떤 파일을 쓰는지 알린다.
   - **`--scope` 없는 경우**: `hold` 모드로 실행 (기존 방식과 동일).
3. AGENT.md에 정의된 Step 0~5 실행 순서(입력 확보 → PRD 분석 → 가정 추출 → 9카테고리 질문 생성 → 우선순위 태깅 → 출력 저장)를 그대로 따라 실행한다.
4. `--scope`가 지정된 경우, 9카테고리 질문 생성 완료 후 **Scope Calibration** 섹션을 추가한다:
   - `expand`: "이 PRD가 더 큰 기회를 놓치고 있는가" 관점에서 3~5개 확장 질문
   - `selective`: 고가치 추가 범위 후보 2~3개 + 각 추가 비용/임팩트 추정
   - `hold`: (추가 없음, 기존 9카테고리로 충분)
   - `reduce`: 삭제/분리 검토 대상 기능 목록 + 단계 분리 제안
5. 산출물은 `prd-agent-system/output/redteam_{YYYYMMDD}_{주제}.md`에 저장한다.
6. 완료 후 요약(질문 수, Critical/Important/Minor 분포, 상위 3개 Critical 질문, scope 결과 요약)을 출력한다.
