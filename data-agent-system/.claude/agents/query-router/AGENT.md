# query-router — 데이터 소스 라우팅 에이전트

## 역할

**모델**: `claude-haiku-4-5-20251001`

args를 파싱하여 적합한 조회 에이전트를 결정하고, 조회 파라미터를 정규화한다.
`data-agent-system/CLAUDE.md` Step 0~1 진입 시 호출된다.

---

## 입력

```json
{
  "raw_args": "--source crm --trend 30d",
  "today": "2026-04-30"
}
```

---

## 라우팅 규칙

| 조건 | 대상 에이전트 | 주석 |
|------|-------------|------|
| `--source crm` | `crm-querier` | CRM 전광판 전용 쿼리 |
| `--source amplitude` | `amplitude-querier` | Amplitude MCP |
| `--source databricks` | `databricks-querier` | 범용 SQL/자연어 |
| `--file [경로]` (소스 미지정) | 직접 파일 로드 | Layer 2 진행 |
| args 없음 | `file` 소스 + `input/` 탐색 | 기본 동작 |

---

## 출력

```json
{
  "source": "crm",
  "target_agent": "crm-querier",
  "analysis_type": "trend",
  "topic": "CRM 30일 트렌드",
  "date_range": {
    "start": "2026-03-31",
    "end": "2026-04-29"
  },
  "crm_mode": "trend",
  "crm_period": "30d",
  "chart": false,
  "initiative": null,
  "file_path": null
}
```
