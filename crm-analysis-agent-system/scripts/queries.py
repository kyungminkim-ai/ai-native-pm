#!/usr/bin/env python3
"""
CRM Analysis Agent — 쿼리 명세 모음
전광판 지표(A~Z)를 파라미터화하여 Databricks client.py로 실행한다.

사용법:
  python3 queries.py --metric A --start-date 2025-01-01 --end-date 2025-04-29
  python3 queries.py --metric Z --start-date 2025-04-01
  python3 queries.py --metric C --segment visit_frequency
  python3 queries.py --metric D --granularity weekly
  python3 queries.py --list
"""

import argparse
import subprocess
import sys
import json
from datetime import date, timedelta
from pathlib import Path

# ─── 날짜 기본값 ──────────────────────────────────────────────

def today_kst() -> str:
    return date.today().isoformat()

def default_start() -> str:
    return "2025-01-01"

# ─── 쿼리 빌더 ────────────────────────────────────────────────

def build_query(metric: str, start_date: str, end_date: str,
                granularity: str = "daily", segment: str = None) -> str:

    date_trunc = {
        "daily":   "base_date",
        "weekly":  "DATE_TRUNC('week', base_date)",
        "monthly": "DATE_TRUNC('month', base_date)",
    }.get(granularity, "base_date")

    queries = {

        # ── A: CRM 발송 성과 (비용·발송수·클릭수·CTR) ─────────────────
        "A": f"""
WITH crm_costs AS (
  SELECT
    channel
    , start_date
    , IF(end_date IS NOT NULL, end_date,
        DATE(CURRENT_TIMESTAMP + INTERVAL '+9' HOUR)) AS end_date
    , unit_price_ex_vat
  FROM team.marketing.musinsa_crm_channel_cost
)
SELECT
  {date_trunc if granularity == 'daily' else
   f"DATE_TRUNC('{granularity}', TO_DATE(partition_date, 'yyyyMMdd'))"}
                                                    AS base_date
  , ccl.channel
  , SUM(ccl.send_count)                             AS send_count
  , SUM(ccl.click_count)                            AS click_count
  , CAST(SUM(ccl.send_count * cc.unit_price_ex_vat) AS BIGINT)
                                                    AS send_costs
  , ROUND(SUM(ccl.click_count)
      / NULLIF(SUM(ccl.send_count), 0) * 100, 2)   AS ctr_pct
FROM team.marketing.musinsa_crm_campaign_list_daily AS ccl
LEFT JOIN crm_costs AS cc
  ON cc.channel = ccl.channel
  AND TO_DATE(ccl.partition_date, 'yyyyMMdd')
      BETWEEN cc.start_date AND cc.end_date
WHERE ccl.channel NOT IN ('FEED', 'CRM')
  AND TO_DATE(ccl.partition_date, 'yyyyMMdd')
      BETWEEN DATE('{start_date}') AND DATE('{end_date}')
GROUP BY ALL
ORDER BY 1 DESC, 2
""",

        # ── B: CRM 리인게이지 세션 유입 ─────────────────────────────────
        "B": f"""
WITH ad_code_channel AS (
  SELECT
    ad_code
    , MAX(channel) AS channel
    , MAX(ad_name)  AS ad_name
  FROM team.marketing.musinsa_crm_campaign_list_daily
  WHERE channel NOT IN ('FEED', 'CRM')
  GROUP BY ALL
)
SELECT
  {"DATE_TRUNC('" + granularity + "', vp.date)" if granularity != 'daily' else "vp.date"}
                                                    AS base_date
  , acc.channel
  , SUM(vp.count_sessions)                          AS count_sessions
  , SUM(vp.count_users)                             AS count_users_reengage
FROM team.marketing.metric_visit_purpose_sessions AS vp
JOIN ad_code_channel AS acc
  ON acc.ad_code = vp.visit_purpose_depth2
WHERE vp.visit_purpose_depth1 = 'reengage'
  AND vp.date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
GROUP BY ALL
ORDER BY 1 DESC, 2
""",

        # ── C: 마케팅 수신 동의 유저 모수 ──────────────────────────────
        "C": f"""
SELECT
  {"DATE_TRUNC('" + granularity + "', partition_date)" if granularity != 'daily' else "partition_date"}
                                                         AS base_date
  {", " + segment if segment else ""}
  , SUM(total_user)                                      AS total_user
  , SUM(allow_marketing_event_push_user)                 AS allow_apppush_user
  , SUM(allow_marketing_coupon_push_user)                AS allow_coupon_push_user
  , SUM(allow_sms_user)                                  AS allow_sms_user
  , SUM(allow_email_user)                                AS allow_email_user
  , ROUND(SUM(allow_marketing_event_push_user)
      / NULLIF(SUM(total_user), 0) * 100, 2)             AS apppush_consent_rate_pct
  , ROUND(SUM(allow_sms_user)
      / NULLIF(SUM(total_user), 0) * 100, 2)             AS sms_consent_rate_pct
  , ROUND(SUM(allow_email_user)
      / NULLIF(SUM(total_user), 0) * 100, 2)             AS email_consent_rate_pct
FROM team.marketing.metric_musinsa_marketing_ad_allow_user
WHERE partition_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
GROUP BY ALL
ORDER BY 1 DESC{", 2" if segment else ""}
""",

        # ── D: 앱푸시 발송 현황 ─────────────────────────────────────────
        "D": f"""
SELECT
  {"DATE_TRUNC('" + granularity + "', TO_DATE(partition_date, 'yyyyMMdd'))" if granularity != 'daily' else "TO_DATE(partition_date, 'yyyyMMdd')"}
                                                    AS base_date
  , channel
  , category
  , COUNT(*)                                        AS count_push_logs
  , COUNT(DISTINCT member_uid)                      AS count_push_user
  , ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT member_uid), 0), 2)
                                                    AS push_per_user
FROM team.marketing.musinsa_app_push_send_logs
WHERE TO_DATE(partition_date, 'yyyyMMdd')
      BETWEEN DATE('{start_date}') AND DATE('{end_date}')
GROUP BY ALL
ORDER BY 1 DESC, 4 DESC
""",

        # ── Z: 전광판 통합 뷰 (일별 스냅샷) ─────────────────────────────
        "Z": f"""
WITH ad_code_channel AS (
  SELECT
    ad_code
    , MAX(channel) AS channel
  FROM team.marketing.musinsa_crm_campaign_list_daily
  WHERE channel NOT IN ('FEED', 'CRM')
  GROUP BY ALL
)
, session_data AS (
  SELECT
    vp.date                AS base_date
    , SUM(count_sessions)  AS count_sessions
    , SUM(count_users)     AS count_users_reengage
  FROM team.marketing.metric_visit_purpose_sessions AS vp
  JOIN ad_code_channel AS acc ON acc.ad_code = vp.visit_purpose_depth2
  WHERE vp.visit_purpose_depth1 = 'reengage'
  GROUP BY ALL
)
, crm_costs AS (
  SELECT
    channel
    , start_date
    , IF(end_date IS NOT NULL, end_date,
        DATE(CURRENT_TIMESTAMP + INTERVAL '+9' HOUR)) AS end_date
    , unit_price_ex_vat
  FROM team.marketing.musinsa_crm_channel_cost
)
, sendclick_data AS (
  SELECT
    TO_DATE(partition_date, 'yyyyMMdd')                               AS base_date
    , CAST(SUM(ccl.send_count * cc.unit_price_ex_vat) AS BIGINT)      AS send_costs
    , SUM(send_count)                                                 AS send_count
    , SUM(click_count)                                                AS click_count
  FROM team.marketing.musinsa_crm_campaign_list_daily AS ccl
  LEFT JOIN crm_costs AS cc
    ON cc.channel = ccl.channel
    AND TO_DATE(ccl.partition_date, 'yyyyMMdd') BETWEEN cc.start_date AND cc.end_date
  WHERE ccl.channel NOT IN ('FEED', 'CRM')
  GROUP BY ALL
)
, allow_ad AS (
  SELECT
    partition_date                                AS base_date
    , SUM(total_user)                             AS total_user
    , SUM(allow_marketing_event_push_user)        AS allow_apppush_user
    , SUM(allow_sms_user)                         AS allow_sms_user
    , SUM(allow_email_user)                       AS allow_email_user
  FROM team.marketing.metric_musinsa_marketing_ad_allow_user
  GROUP BY ALL
)
, push_agg AS (
  SELECT
    TO_DATE(partition_date, 'yyyyMMdd')               AS base_date
    , COUNT(*)                                        AS count_push_logs
    , COUNT(DISTINCT member_uid)                      AS count_push_user
    , ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT member_uid), 0), 2)
                                                      AS push_per_user
  FROM team.marketing.musinsa_app_push_send_logs
  GROUP BY ALL
)
SELECT
  COALESCE(scd.base_date, sd.base_date)              AS base_date

  -- A. CRM 발송 성과
  , COALESCE(scd.send_costs, 0)                      AS send_costs
  , COALESCE(scd.send_count, 0)                      AS send_count
  , COALESCE(scd.click_count, 0)                     AS click_count
  , ROUND(COALESCE(scd.click_count, 0)
      / NULLIF(scd.send_count, 0) * 100, 2)          AS ctr_pct

  -- B. 세션 유입
  , COALESCE(sd.count_sessions, 0)                   AS count_sessions
  , COALESCE(sd.count_users_reengage, 0)             AS count_users_reengage
  , ROUND(COALESCE(sd.count_sessions, 0)
      / NULLIF(scd.send_count, 0) * 100, 2)          AS str_pct

  -- C. 수신 동의 모수
  , aa.total_user
  , aa.allow_apppush_user
  , aa.allow_sms_user
  , aa.allow_email_user
  , ROUND(aa.allow_apppush_user
      / NULLIF(aa.total_user, 0) * 100, 2)           AS apppush_consent_rate_pct
  , ROUND(aa.allow_sms_user
      / NULLIF(aa.total_user, 0) * 100, 2)           AS sms_consent_rate_pct
  , ROUND(aa.allow_email_user
      / NULLIF(aa.total_user, 0) * 100, 2)           AS email_consent_rate_pct

  -- D. 앱푸시 발송 현황
  , ppu.count_push_logs
  , ppu.count_push_user
  , ppu.push_per_user

FROM sendclick_data AS scd
FULL JOIN session_data AS sd ON sd.base_date = scd.base_date
LEFT JOIN allow_ad AS aa
  ON aa.base_date = COALESCE(scd.base_date, sd.base_date)
LEFT JOIN push_agg AS ppu
  ON ppu.base_date = COALESCE(scd.base_date, sd.base_date)
WHERE COALESCE(scd.base_date, sd.base_date)
      BETWEEN DATE('{start_date}') AND DATE('{end_date}')
ORDER BY 1 DESC
""",
    }

    return queries.get(metric.upper(), "").strip()


# ─── 쿼리 목록 출력 ───────────────────────────────────────────

METRIC_DESC = {
    "A": "CRM 발송 성과 — 채널별 발송수·클릭수·비용·CTR",
    "B": "CRM 세션 유입 — 리인게이지 세션수·유저수",
    "C": "수신 동의 모수 — 전체/앱푸시/SMS/이메일 동의 유저 및 동의율",
    "D": "앱푸시 발송 현황 — 채널·카테고리별 발송 로그·유저수·유저당 발송수",
    "Z": "전광판 통합 뷰 — A+B+C+D 전 지표 일별 스냅샷",
}


# ─── 실행 ─────────────────────────────────────────────────────

def run_via_client(sql: str) -> dict:
    client_path = Path(__file__).parents[1].parent / "databricks-agent-system" / "scripts" / "client.py"
    result = subprocess.run(
        [sys.executable, str(client_path), "--execute", sql],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return {"error": result.stderr or result.stdout}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw": result.stdout}


def main():
    parser = argparse.ArgumentParser(description="CRM Analysis 쿼리 실행")
    parser.add_argument("--metric", choices=["A","B","C","D","Z","a","b","c","d","z"],
                        help="실행할 지표 쿼리 (A/B/C/D/Z)")
    parser.add_argument("--start-date", default=default_start(), dest="start_date")
    parser.add_argument("--end-date",   default=today_kst(),     dest="end_date")
    parser.add_argument("--granularity", choices=["daily","weekly","monthly"], default="daily")
    parser.add_argument("--segment", choices=["active_status","visit_frequency","age_gender"],
                        help="C 지표용 세그먼트 분리")
    parser.add_argument("--print-sql", action="store_true", help="SQL만 출력 (실행 안 함)")
    parser.add_argument("--list", action="store_true", help="지표 목록 출력")
    args = parser.parse_args()

    if args.list:
        print("\n[CRM Analysis] 지표 목록\n")
        for k, v in METRIC_DESC.items():
            print(f"  {k}: {v}")
        print()
        return

    if not args.metric:
        parser.print_help()
        sys.exit(1)

    sql = build_query(
        metric=args.metric,
        start_date=args.start_date,
        end_date=args.end_date,
        granularity=args.granularity,
        segment=args.segment,
    )

    if not sql:
        print(f"[ERROR] 지원하지 않는 metric: {args.metric}")
        sys.exit(1)

    if args.print_sql:
        print(sql)
        return

    print(f"[쿼리 실행] metric={args.metric.upper()}, "
          f"기간={args.start_date}~{args.end_date}, "
          f"granularity={args.granularity}")
    print("─" * 60)
    result = run_via_client(sql)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
