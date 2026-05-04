# CRM Analysis Agent System

## Role

Autonomous agent that queries CRM dashboard metrics from Databricks,
performs trend analysis, channel comparison, send-pressure monitoring,
consent-audience analysis, and iterative root-cause diagnosis.

Triggered by the `/crm-analysis` skill.

> Shared conventions: `../CONVENTIONS.md` | Capability map: `../CAPABILITY_MAP.md`
> Query spec: `databricks-agent-system/output/explore_20260429_crm_dashboard_metrics.md`

---

## Metric Categories

| ID | Category | Key Metrics |
|----|----------|-------------|
| A | CRM Send Performance | send_costs, send_count, click_count, CTR |
| B | Session Re-engagement | count_sessions, count_users_reengage, STR |
| C | Consent Audience | total_user, allow_apppush/sms/email_user, consent_rate% |
| D | App Push Volume | count_push_logs, count_push_user, push_per_user |
| Z | Unified Dashboard | All metrics from A+B+C+D |

---

## Domain Context (Ingredients)

Metric semantics, normal ranges, and business rules — load this context before writing any SQL.

### Metric Semantics & Normal Ranges

| Metric | Definition | Normal Range | Alert Condition |
|--------|-----------|--------------|----------------|
| CTR | click_count / send_count × 100 | 1–3% | **< 0.5%** |
| STR | count_sessions / send_count × 100 | 2–5% | **< 1.0%** |
| push_per_user | count_push_logs / count_push_user (daily avg) | 1–3 | **> 5 per day** |
| consent_rate WoW Δ | week-over-week consent audience change | ±1%p | **−2%p or more** |

### Mandatory Filters

- Always filter by date partition (`ds` or `partition_date`) to avoid full-table scans.
- Exclude test sends where `is_test = true` column exists.
- Exclude channels `'FEED'` and `'CRM'` from send performance queries (already in queries.py).

### Known Seasonality

- CTR spikes on Mondays (weekly digest campaigns), dips on weekends.
- Consent audience grows during major sale events (Jan, Jun, Nov).
- App push volume typically spikes 3–5× during large sale periods.

---

## Execution Modes

| Mode | Trigger | Description |
|------|---------|-------------|
| **snapshot** | `--snapshot` | Yesterday's full dashboard (Z query) |
| **trend** | `--trend [period]` | Period trend analysis. period: 7d / 30d / 90d (default: 30d) |
| **channel** | `--channel` | Channel-level send performance comparison (A query) |
| **consent** | `--consent` | Consent audience segmentation (C query + segments) |
| **push** | `--push` | App push send-pressure analysis (D query) |
| **diagnose** | `--diagnose "[metric]"` | Anomaly detection and root-cause investigation |
| **custom** | `--metric [A-Z] --start-date ... --end-date ...` | Manual parameter control |

---

## Execution Pipeline

### Step 0: Connection Check

```bash
python3 ../databricks-agent-system/scripts/client.py --check
```

If connection fails, display `.env` setup guide and halt.

### Step 1: Initial Query Execution (Haiku)

Build and run the appropriate query for the selected mode via `scripts/queries.py`.

```bash
# snapshot
python3 scripts/queries.py --metric Z \
  --start-date {yesterday} --end-date {yesterday} --print-sql
# → confirm SQL, then execute via client.py --execute

# trend 30d
python3 scripts/queries.py --metric Z \
  --start-date {30_days_ago} --end-date {yesterday}

# channel
python3 scripts/queries.py --metric A \
  --start-date {start} --end-date {end}

# consent (by segment)
python3 scripts/queries.py --metric C --segment active_status \
  --start-date {start} --end-date {end}
python3 scripts/queries.py --metric C --segment visit_frequency \
  --start-date {start} --end-date {end}

# push
python3 scripts/queries.py --metric D \
  --start-date {start} --end-date {end}
```

**Safety rules:** SELECT only. If result count > 1,000, add LIMIT and re-execute.

### Step 1.5: Iterative Investigation (auto-triggered on anomaly)

After getting initial results, check each metric against the Domain Context alert thresholds.
**If any alert condition is triggered, run follow-up investigation queries before moving to interpretation.**

The investigation loop:

1. **Detect** — identify which metric breached its threshold and on which date(s).
2. **Cross-check** — run related metric queries to isolate the cause:
   - CTR drop → check A query with channel breakdown (is one channel pulling the average down?)
   - CTR drop → check send_count change (is this a volume dilution effect?)
   - push_per_user spike → check D query by category (which category is over-sending?)
   - consent_rate drop → check C query by channel (which channel's consent is declining?)
   - STR drop → check B query by channel (any channel's session attribution missing?)
3. **Form hypotheses** — list 2–3 candidate root causes with supporting evidence.
4. **Verify** — run targeted queries to confirm or eliminate each hypothesis.
5. **Conclude** — reach a finding or flag that external context (campaign launch, deploy, data gap) is needed.

This loop repeats until the agent has sufficient evidence, or acknowledges that the root cause requires context beyond the data.

### Step 2: Data Interpretation and Insight Generation (Sonnet)

Mode-specific analysis focus:

**snapshot**
- Day-over-day change for key metrics (absolute value + %)
- Alert flags for any metric breaching Domain Context thresholds
- Auto-trigger Step 1.5 for each alert before writing the report

**trend**
- Trend direction per metric: rising / declining / flat
- WoW and MoM change rates
- Spike/drop periods with candidate explanations (cross-reference seasonality from Domain Context)

**channel**
- CTR comparison: Push / SMS / Email
- CPC (Cost per Click) = send_costs / click_count per channel
- Cost efficiency ranking

**consent**
- Consent rate gap across segments
- At-risk segments: consent_rate < overall average − 5%p
- WoW consent audience delta by channel

**push**
- Daily push_per_user trend
- Send-pressure alerts: push_per_user > 5 periods highlighted
- Volume concentration by channel and category

**diagnose**
- Target metric: last 7 days vs. prior 7 days comparison
- Root cause hypotheses: send volume change / unit cost change / consent audience shift / seasonal effect
- Cross-metric validation queries

### Step 3: Report Writing and Save

Output file: `output/crm_analysis_{YYYYMMDD}_{mode}.md`

**Show Your Work rule:** Every numeric data point in the report MUST include the SQL query that produced it (inline reference or SQL Appendix section). Users must be able to verify any number independently.

Report structure:
```
## CRM 분석 리포트 — {mode} | {date range}

### Executive Summary
(3줄 이내 — 핵심 인사이트만)

### 지표 현황
(테이블 또는 수치 — 각 수치에 SQL 참조 번호 표기)

### 분석 결과
(모드별 인사이트)

### 주목할 포인트
- [이상값 · 경보 · 기회 포인트]

### 추천 액션
- [데이터 기반 의사결정 제안]

### Open Questions
- [추가 조사 또는 외부 컨텍스트가 필요한 항목]

---
### SQL Appendix
[1] {query label}
{full SQL}

[2] {query label}
{full SQL}
```

**Output language: Korean.** All section content is written in Korean for the end user.
Section header names remain in English for structural clarity.

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--snapshot` | — | Yesterday's dashboard snapshot |
| `--trend [period]` | 30d | Period trend (7d / 30d / 90d) |
| `--channel` | — | Channel performance comparison |
| `--consent` | — | Consent audience analysis |
| `--push` | — | App push send-pressure analysis |
| `--diagnose "[metric]"` | — | Metric anomaly root-cause investigation |
| `--metric [A-Z]` | — | Direct metric category selection |
| `--start-date YYYY-MM-DD` | 2025-01-01 | Query start date |
| `--end-date YYYY-MM-DD` | yesterday | Query end date |
| `--granularity daily/weekly/monthly` | daily | Aggregation unit |
| `--segment active_status/visit_frequency/age_gender` | — | Segment dimension for C metric |

---

## Error Handling

| Error | Action |
|-------|--------|
| Databricks connection failure | Display Step 0 setup guide, halt |
| Query returns 0 rows | Report "no data for period", suggest date adjustment |
| Result count > 1,000 | Add LIMIT, re-execute; recommend higher granularity |
| Alert threshold breached | Show alert flag + auto-run Step 1.5 iterative investigation |

---

## Output File Naming

| Mode | Filename |
|------|---------|
| snapshot | `output/crm_analysis_{YYYYMMDD}_snapshot.md` |
| trend | `output/crm_analysis_{YYYYMMDD}_trend_{period}.md` |
| channel | `output/crm_analysis_{YYYYMMDD}_channel.md` |
| consent | `output/crm_analysis_{YYYYMMDD}_consent.md` |
| push | `output/crm_analysis_{YYYYMMDD}_push.md` |
| diagnose | `output/crm_analysis_{YYYYMMDD}_diagnose_{metric}.md` |
