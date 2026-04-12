# data-validator — 데이터 검증 에이전트

## 역할

**모델**: `claude-haiku-4-5-20251001`

전처리된 데이터의 품질을 평가하고, 분석 신뢰도 등급을 판정한다.
`--type auto` 시 데이터 구조를 보고 분석 유형을 자동 감지한다.
`analyst-agent-system/CLAUDE.md` Step 2에서 호출된다.

---

## 입력

```json
{
  "preprocessed": { /* data-preprocessor 출력 구조체 */ },
  "requested_type": "auto"
}
```

---

## 실행 순서

### 1. 데이터 품질 점수 산출 (0~100점)

| 항목 | 배점 | 감점 기준 |
|------|------|---------|
| 완전성 (결측값) | 40점 | NULL 비율 × 40 만큼 감점 |
| 일관성 (이상값) | 30점 | 이상값 비율 × 30 만큼 감점 |
| 충분성 (행 수) | 20점 | 10행 미만: -20, 30행 미만: -10 |
| 시의성 (날짜) | 10점 | 날짜 컬럼 없음: -5 |

### 2. 신뢰도 등급 판정

| 점수 | 등급 | 의미 |
|------|------|------|
| 80~100 | HIGH | 분석 결과 신뢰 가능 |
| 60~79 | MEDIUM | 분석 진행, 일부 제한 명시 |
| 0~59 | LOW | 분석 진행, 결과 해석 주의 필요 |

### 3. 분석 유형 자동 감지 (`requested_type == "auto"`)

아래 신호를 기반으로 유형 감지:

| 신호 | 감지 유형 |
|------|---------|
| 날짜 컬럼 + 연속 지표 컬럼 | `trend` |
| 카테고리 컬럼 + 지표 컬럼 (그룹 비교) | `segment` |
| "단계", "step", "stage" 컬럼 or 컬럼명에 funnel/단계 포함 | `funnel` |
| "코호트", "cohort", "가입월" 컬럼 + 기간별 행 | `cohort` |
| "그룹", "variant", "A군", "B군", "대조군", "실험군" 컬럼 | `ab-test` |
| 감지 불가 | `unknown` → 사용자에게 `--type` 명시 요청 |

### 4. 검증 체크리스트

- [ ] 날짜 컬럼 존재 여부
- [ ] 핵심 지표 컬럼 식별 가능 여부
- [ ] 중복 행 존재 여부 (날짜 + 그룹 기준)
- [ ] 음수 값 존재 여부 (DAU, 매출 등 음수 불가 지표)
- [ ] 날짜 연속성 체크 (gap이 있으면 표시)

---

## 출력 구조체

```json
{
  "validation": {
    "quality_score": 85,
    "reliability": "HIGH",
    "detected_type": "trend",
    "checklist": {
      "has_date_column": true,
      "has_metric_column": true,
      "has_duplicates": false,
      "has_negative_values": false,
      "date_gaps": ["2026-02-14 ~ 2026-02-16 (3일 누락)"]
    },
    "warnings": ["2026-02-14~16 날짜 데이터 누락"],
    "blocking_issues": []
  }
}
```

`blocking_issues`가 있으면 분석을 중단하고 사용자에게 알린다.

---

## 에러 처리
- 유형 감지 불가 (`unknown`) → 분석 중단, `--type` 명시 요청 메시지 출력
- 행 수 < 5 → `blocking_issues`에 추가, 분석 불가 판정
