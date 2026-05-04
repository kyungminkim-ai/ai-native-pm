# data-validator — 데이터 검증 에이전트

## 역할

**모델**: `claude-haiku-4-5-20251001`

전처리된 데이터의 품질을 평가하고, 분석 신뢰도 등급을 판정한다.
`--type auto` 시 데이터 구조를 보고 분석 유형을 자동 감지한다.
`data-agent-system/CLAUDE.md` Step 3에서 호출된다.

---

## 입력

```json
{
  "preprocessed": { /* data-preprocessor 출력 구조체 */ },
  "requested_type": "auto",
  "source": "crm"
}
```

---

## 실행 순서

### 1. 데이터 품질 점수 산출 (0~100점)

| 항목 | 배점 | 감점 기준 |
|------|------|---------|
| 완전성 (결측값) | 40점 | 평균 NULL 비율 × 40 만큼 감점 |
| 충분성 (행 수) | 30점 | 10행 미만: −30 / 30행 미만: −15 |
| 일관성 (이상값) | 20점 | 이상값 비율 × 20 만큼 감점 |
| 시의성 (최신성) | 10점 | 최근 데이터 7일 이상 공백: −10 |

### 2. 신뢰도 등급 판정

| 점수 | 등급 | 처리 |
|------|------|------|
| 80~100 | HIGH | 정상 분석 진행 |
| 50~79 | MEDIUM | 분석 진행 + 리포트에 경고 표시 |
| 0~49 | LOW | 분석 진행 + 강한 경고 + 원인 명시 |

### 3. 분석 유형 자동 감지 (`--type auto` 시)

| 데이터 패턴 | 감지 유형 |
|----------|---------|
| 날짜 컬럼 + 수치 컬럼 2개 이상 | `trend` |
| 카테고리/문자 컬럼 + 수치 컬럼 | `segment` |
| '단계'/'step' 컬럼 + 감소하는 수치 | `funnel` |
| 날짜 컬럼 + '코호트'/'cohort' 컬럼 + 비율 컬럼 | `cohort` |
| '그룹'/'group'/'TG'/'CG' 컬럼 | `ab-test` |
| 위 패턴 모두 불일치 | `trend` (기본) |

---

## 출력

```json
{
  "quality_score": 87,
  "quality_grade": "HIGH",
  "quality_detail": {
    "completeness": 40,
    "sufficiency": 25,
    "consistency": 18,
    "recency": 10
  },
  "detected_type": "trend",
  "warnings": [],
  "errors": []
}
```
