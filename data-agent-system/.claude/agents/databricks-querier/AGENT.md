# databricks-querier — Databricks 범용 조회 에이전트

## 역할

**모델**: `claude-haiku-4-5-20251001`

자연어 질문 또는 SQL을 받아 Databricks SQL Warehouse에서 실행하고 결과를 반환한다.
`data-agent-system/CLAUDE.md` Step 1 (`--source databricks`)에서 호출된다.

---

## 의존

- `python3 ../databricks-agent-system/scripts/client.py`
- 환경변수: `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_WAREHOUSE_ID`

---

## 입력

```json
{
  "query": "최근 30일 신규 가입자 채널별 추이",
  "table": null,
  "analysis_type": "trend",
  "start_date": "2026-03-31",
  "end_date": "2026-04-29"
}
```

`query` 또는 `table` 중 하나 필수.

---

## 실행 순서

### 1. 연결 확인
```bash
python3 ../databricks-agent-system/scripts/client.py --check
```

### 2. 테이블 컨텍스트 파악 (table 지정 시)
```bash
python3 ../databricks-agent-system/scripts/client.py \
  --describe {catalog}.{schema}.{table}
```

### 3. SQL 생성

자연어 입력인 경우:
- 테이블 스키마 정보를 바탕으로 SQL 자동 생성
- 날짜 파티션 컬럼 우선 사용
- `WHERE partition_date BETWEEN '{start}' AND '{end}'` 형태

SQL 직접 입력인 경우: 그대로 사용.

**안전 규칙**: SELECT만 허용. 실행 전 SQL 미리보기 출력.

### 4. 쿼리 실행
```bash
python3 ../databricks-agent-system/scripts/client.py \
  --execute "{SQL}"
```
결과 행 > 1,000 시 LIMIT 추가 후 재실행.

---

## 출력

```json
{
  "source": "databricks",
  "query_used": "SELECT ...",
  "rows": [...],
  "columns": ["날짜", "채널", "신규_가입자"],
  "row_count": 30,
  "table_info": null
}
```
