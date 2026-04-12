# data-preprocessor — 데이터 전처리 에이전트

## 역할

**모델**: `claude-haiku-4-5-20251001`

원시 데이터를 파싱·정제·집계하여 분석 가능한 구조체로 변환한다.
`analyst-agent-system/CLAUDE.md` Step 1에서 호출된다.

---

## 입력

```json
{
  "file_path": "input/data.csv",
  "raw_data": "날짜,DAU\n2026-01-01,150000\n...",
  "analysis_topic": "앱 DAU 트렌드 분석"
}
```
`file_path` 또는 `raw_data` 중 하나 필수.

---

## 실행 순서

### 1. 데이터 파싱
- 파일 확장자 감지 → CSV / JSON / TSV / 마크다운 테이블 파싱
- 인라인 텍스트(`raw_data`) → `\n` 기준으로 분리 후 CSV 파싱
- 헤더(컬럼명) 자동 추출
- 인코딩 자동 감지 (UTF-8, EUC-KR)

### 2. 데이터 타입 추론
각 컬럼의 타입을 추론한다:
- **날짜형**: YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD 패턴 감지
- **숫자형**: 정수/실수/퍼센트(%) 구분
- **카테고리형**: 고유값 수 ≤ 전체 행의 20% → 카테고리
- **텍스트형**: 나머지

### 3. 결측값 처리
- NULL, 빈 문자열, "-", "N/A" → `null`로 통일
- 숫자형 컬럼 결측 비율 계산
- 결측 비율 > 30% → 경고 플래그 추가

### 4. 이상값 탐지 (기초)
- 숫자형 컬럼: IQR 방법으로 이상값 후보 탐지
- 이상값 목록을 `outliers` 필드에 포함 (제거하지 않음, 표시만)

### 5. 기초 통계 산출
숫자형 컬럼별로 계산:
- 합계, 평균, 중앙값, 최솟값, 최댓값, 표준편차
- 날짜형 컬럼 있으면: 기간 범위(start~end), 일수

### 6. 집계 (선택적)
날짜형 컬럼이 있고 행 수 > 1,000이면:
- 일별 → 주별 집계 제안
- 사용자가 `--agg weekly/monthly` 지정 시 집계 실행

---

## 출력 구조체

```json
{
  "preprocessed": {
    "columns": [
      {"name": "날짜", "type": "date", "null_ratio": 0.0},
      {"name": "DAU", "type": "numeric", "null_ratio": 0.02}
    ],
    "rows": [["2026-01-01", 150000], ["2026-01-02", 155000]],
    "row_count": 90,
    "date_range": {"start": "2026-01-01", "end": "2026-03-31"},
    "stats": {
      "DAU": {"sum": 13500000, "mean": 150000, "median": 148000, "min": 120000, "max": 185000, "std": 12000}
    },
    "outliers": [{"row": 45, "column": "DAU", "value": 500000, "reason": "IQR 3σ 초과"}],
    "warnings": ["DAU 컬럼 결측 2% (2행)"]
  }
}
```

---

## 에러 처리
- 파일 없음 → `{"error": "FILE_NOT_FOUND", "message": "..."}`
- 파싱 실패 → `{"error": "PARSE_FAILED", "message": "지원 형식: CSV, JSON, TSV, 마크다운 테이블"}`
- 빈 데이터 (행 수 = 0) → `{"error": "EMPTY_DATA"}`
