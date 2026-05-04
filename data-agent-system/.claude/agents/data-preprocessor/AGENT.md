# data-preprocessor — 데이터 전처리 에이전트

## 역할

**모델**: `claude-haiku-4-5-20251001`

조회 레이어에서 받은 원시 데이터를 파싱·정제·집계하여 분석 가능한 구조체로 변환한다.
`data-agent-system/CLAUDE.md` Step 2에서 호출된다.

---

## 입력

```json
{
  "raw_data": {
    "source": "crm",
    "rows": [...],
    "columns": ["base_date", "ctr_pct", "send_count"],
    "row_count": 30
  },
  "analysis_topic": "CRM 30일 트렌드",
  "analysis_type": "trend"
}
```

---

## 실행 순서

### 1. 데이터 파싱
- rows/columns 구조 → 딕셔너리 배열로 정규화
- 날짜 컬럼: `datetime` 타입으로 변환, 정렬
- 숫자 컬럼: `float`/`int` 변환, 단위 정규화 (`%` 문자 제거 등)

### 2. 결측값 처리
- NULL/빈 문자열 탐지
- 숫자 컬럼: 0 또는 전후 평균으로 대체 (결측 비율 기록)
- 날짜 컬럼: 결측 행 제거

### 3. 이상값 탐지 (기초)
- IQR 방법: Q1 − 1.5×IQR ~ Q3 + 1.5×IQR 범위 밖 값 기록
- 이상값은 제거하지 않고 플래그 처리

### 4. 집계 (analysis_type 참고)
- trend: 날짜 기준 정렬, 필요 시 일→주 집계
- segment: 세그먼트 컬럼 기준 groupby 합계·평균
- funnel: 단계 순서 정렬
- cohort: pivot (코호트 × 경과 기간 매트릭스)
- ab-test: 그룹별 분리

### 5. 기초 통계 산출
- 각 수치 컬럼별: 평균·중앙값·표준편차·최솟값·최댓값

---

## 출력

```json
{
  "records": [
    {"base_date": "2026-04-29", "ctr_pct": 1.23, "send_count": 150000},
    ...
  ],
  "columns": ["base_date", "ctr_pct", "send_count"],
  "row_count": 30,
  "date_column": "base_date",
  "numeric_columns": ["ctr_pct", "send_count"],
  "missing_rates": {"ctr_pct": 0.0, "send_count": 0.03},
  "outlier_flags": [{"row": 5, "column": "ctr_pct", "value": 0.1}],
  "stats": {
    "ctr_pct": {"mean": 1.2, "median": 1.1, "std": 0.3, "min": 0.8, "max": 1.9}
  }
}
```
