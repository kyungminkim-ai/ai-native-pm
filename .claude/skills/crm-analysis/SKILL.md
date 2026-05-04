---
description: CRM 전광판 지표를 Databricks에서 조회하고 트렌드·채널 비교·발송 압력·수신 동의 모수 분석을 수행하는 CRM 분석 에이전트
---

# /crm-analysis — CRM Analysis Agent

## Model

`claude-sonnet-4-6`

## Usage

```
/crm-analysis --snapshot                          ← 어제 전광판 전체 지표 스냅샷
/crm-analysis --trend 30d                         ← 최근 30일 지표 트렌드 분석
/crm-analysis --trend 7d                          ← 최근 7일 지표 트렌드 분석
/crm-analysis --channel                           ← 채널별 발송 성과 비교
/crm-analysis --consent                           ← 수신 동의 모수 세그먼트 분석
/crm-analysis --push                              ← 앱푸시 발송 압력 분석
/crm-analysis --diagnose "CTR"                    ← CTR 이상 원인 진단
/crm-analysis --metric Z --start-date 2025-04-01  ← 커스텀 기간 통합 뷰
```

## Execution Rules

1. Read `crm-analysis-agent-system/CLAUDE.md` to load the role definition, Domain Context (metric semantics, normal ranges, seasonality, mandatory filters), and the full execution pipeline.

2. Parse args:
   - `--snapshot` → snapshot mode (auto-calculate yesterday's date)
   - `--trend [7d/30d/90d]` → trend mode (default: 30d)
   - `--channel` → channel mode
   - `--consent` → consent mode
   - `--push` → push mode
   - `--diagnose "[metric]"` → diagnose mode
   - `--metric [A-Z]` + `--start-date` + `--end-date` → custom mode
   - no args → run snapshot mode

3. Check Databricks connection:
   ```bash
   python3 databricks-agent-system/scripts/client.py --check
   ```

4. Execute the pipeline defined in `crm-analysis-agent-system/CLAUDE.md`:
   - **Step 1**: Build SQL via `scripts/queries.py` (`--print-sql` to inspect first)
   - **Step 1.5**: If any alert threshold is breached → automatically run iterative investigation queries (do NOT skip this step)
   - **Step 2**: Interpret results and generate insights (Sonnet)
   - **Step 3**: Write and save report — all content in Korean; every data point must reference its SQL

5. Output: `crm-analysis-agent-system/output/crm_analysis_{YYYYMMDD}_{mode}.md`

## Metric Categories

| ID | Category | Key Metrics |
|----|----------|-------------|
| A | CRM Send Performance | send_costs, send_count, click_count, CTR |
| B | Session Re-engagement | count_sessions, STR |
| C | Consent Audience | total_user, channel consent users, consent_rate% |
| D | App Push Volume | count_push_logs, count_push_user, push_per_user |
| Z | Unified Dashboard | All A+B+C+D metrics |

## Alert Thresholds

| Metric | Alert Condition |
|--------|----------------|
| CTR | < 0.5% |
| STR | < 1.0% |
| push_per_user | > 5 per day |
| consent_rate WoW Δ | −2%p or more |

When any alert is triggered, the agent **automatically runs Step 1.5 iterative investigation** — drilling down by channel, category, or time segment — before writing the final report.
