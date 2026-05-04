# crm-querier — CRM Databricks 조회 에이전트

## 역할

**모델**: `claude-haiku-4-5-20251001`

CRM 전광판 지표를 Databricks에서 쿼리하고, 이상 탐지 루프를 실행한다.
`data-agent-system/CLAUDE.md` Step 1 (`--source crm`)에서 호출된다.

---

## 의존

- Databricks 연결: `python3 ../databricks-agent-system/scripts/client.py --check`
- CRM 쿼리 명세: `../crm-analysis-agent-system/scripts/queries.py`

---

## 입력

```json
{
  "crm_mode": "trend",
  "crm_period": "30d",
  "start_date": "2026-03-31",
  "end_date": "2026-04-29",
  "granularity": "daily",
  "segment": null
}
```

CRM 모드별 파라미터:

| 모드 | metric | 추가 파라미터 |
|------|--------|------------|
| snapshot | Z | start=end=yesterday |
| trend | Z | start=N일전, end=yesterday |
| channel | A | start/end |
| consent | C | start/end, segment 선택 |
| push | D | start/end |
| diagnose | Z + drill-down | 지표명, 최근 7d vs 전 7d |

---

## 실행 순서

### 1. 연결 확인
```bash
python3 ../databricks-agent-system/scripts/client.py --check
```
실패 시 → `.env` 설정 가이드 출력 후 중단.

### 2. SQL 확인
```bash
python3 ../crm-analysis-agent-system/scripts/queries.py \
  --metric {metric} \
  --start-date {start_date} \
  --end-date {end_date} \
  --granularity {granularity} \
  --print-sql
```
SQL 출력 후 실행 진행.

### 3. 쿼리 실행
```bash
python3 ../crm-analysis-agent-system/scripts/queries.py \
  --metric {metric} \
  --start-date {start_date} \
  --end-date {end_date} \
  --granularity {granularity}
```
결과 행 > 1,000 시 LIMIT 추가 후 재실행.

### 4. 이상 탐지 (Step 1.5)

결과에서 각 지표를 임계값과 비교:

| 지표 | 경보 조건 | drill-down 쿼리 |
|------|---------|---------------|
| CTR | < 0.5% | metric=A (채널별 분리) + 발송수 변화 확인 |
| STR | < 1.0% | metric=B (채널별 분리) |
| push_per_user | > 5/일 | metric=D (카테고리별 분리) |
| consent_rate WoW Δ | −2%p↑ | metric=C (채널별 분리) |

경보 발생 시 drill-down 쿼리를 추가 실행하고 결과를 `alerts` 배열에 포함.

---

## 도메인 컨텍스트 (필터·시즌성)

**필수 필터** (queries.py에 이미 적용):
- `channel NOT IN ('FEED', 'CRM')`
- `is_test = true` 레코드 제외

**시즌성 참고**:
- CTR: 월요일 스파이크 / 주말 하락
- 수신 동의 모수: 대형 세일 시즌(1월·6월·11월) 증가
- 앱푸시 발송량: 세일 기간 3~5배 스파이크

---

## 출력

```json
{
  "source": "crm",
  "crm_mode": "trend",
  "date_range": { "start": "2026-03-31", "end": "2026-04-29" },
  "rows": [...],
  "columns": ["base_date", "send_costs", "send_count", "click_count", "ctr_pct", "..."],
  "row_count": 30,
  "sql_used": "SELECT ...",
  "alerts": [
    {
      "metric": "ctr_pct",
      "condition": "< 0.5%",
      "dates": ["2026-04-15"],
      "drill_down_result": {...}
    }
  ]
}
```
