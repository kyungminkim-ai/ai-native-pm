# Databricks notebook source
# MAGIC %md
# MAGIC # PN-01 — 04 Braze 발송
# MAGIC
# MAGIC H-01 `04_h01_braze_delivery` 의 발송·로그·멱등 로직을 그대로 옮기고, **발송 직전 재검증(F-9)** 을 추가했습니다.
# MAGIC
# MAGIC | 재검증 | 처리 |
# MAGIC |---|---|
# MAGIC | 푸시 동의 · 첫구매 발생 | 동의 철회 / 발송 전 구매 시 제외 |
# MAGIC | 재고 · 보유쿠폰 · 15% | 02 와 **같은 함수**로 지금 시각 기준 재계산. 조건 이탈 시 제외 (`RECHECK_*`) |
# MAGIC | 최종가 변동 | P1 은 새 가격으로 제목을 다시 만듭니다. 8만 원 경계를 넘으면 variant 가 바뀌므로 제외 |
# MAGIC
# MAGIC 모드: 상수 `DELIVERY_MODE` — `LIVE`(운영 Job) / `TEST`(내부 수신자) / `PREVIEW`(API 미호출). 위젯을 두지 않습니다. Campaign ID 는 00 의 상수(47a43974) 하나만 씁니다.
# MAGIC
# MAGIC 재실행: 같은 날 다시 돌리면 대상 전원에게 다시 호출합니다. 중복 수신은 Braze 캠페인 재수신(re-eligibility) 설정이 거릅니다(2026-10-13 결정).
# MAGIC LIVE 발송이 끝나면 모수 퍼널과 접수 결과를 Slack #match-29cm-앱푸시-운영 으로 보냅니다. 03 audience 가 0명이면 Braze 를 호출하지 않고 중단 알림을 보냅니다.

# COMMAND ----------

# MAGIC %run ./pn01_00_common

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 전달 설정

# COMMAND ----------

import hashlib
import re
import time
import unicodedata
from collections import Counter
from itertools import cycle, islice
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BRAZE_REST_ENDPOINT = "https://rest.iad-03.braze.com"
# H-01 04 와 같은 Databricks Secret을 LIVE/TEST에서 읽습니다.
BRAZE_API_KEY = None  # LIVE/TEST 시 Databricks Secret에서 읽음

# 매일 도는 운영 Job 이라 LIVE 를 상수로 둡니다. TEST·PREVIEW 는 이 값을 코드에서 바꿔 수동 실행할 때만 씁니다.
DELIVERY_MODE = "LIVE"
ALLOWED_DELIVERY_MODES = ["PREVIEW", "TEST", "LIVE"]
if DELIVERY_MODE not in ALLOWED_DELIVERY_MODES:
    raise ValueError(f"DELIVERY_MODE 값이 올바르지 않습니다: {DELIVERY_MODE}")

TEST_EXTERNAL_USER_IDS = [
    "4957000", "6115809", "1511054", "5142088", "219322", "3111529", "2231443",
    "2851411", "1430504", "4381168", "9160019", "5668211", "510231", "113217", "7068864",
]
BRAZE_BATCH_SIZE = 50  # Braze 요청당 수신자 수
MAX_RETRIES = 5  # API 최대 재시도
DAILY_SEND_LIMIT = 50000  # 일일 발송 모수 상한 (0=무제한)
INCLUDE_P3 = False  # P3 문구 미확정(O-1)
if BRAZE_BATCH_SIZE < 1 or BRAZE_BATCH_SIZE > 50:
    raise ValueError("Braze 요청당 수신자는 1~50명이어야 합니다.")

if not spark.catalog.tableExists(OUTPUT_TABLES["audience"]):
    raise ValueError(f"Audience Output이 없습니다: {OUTPUT_TABLES['audience']}")

# LIVE 는 이 시각(KST) 이후에만 시작합니다. 일찍 시작하면 구매·쿠폰·재고 재검증이 17:20 발송 시점보다 낡습니다.
LIVE_EARLIEST_START = (16, 30)

# Slack — PN-01 전용 Incoming Webhook. 보낼 채널은 Webhook 을 만들 때 정해지므로 SLACK_CHANNEL_NAME 은 로그 표시용입니다.
# 평문 금지: 시크릿에서만 읽습니다. LIVE 만 보내고, 그 외 모드는 payload 를 출력합니다.
# 2026-10-14 — 환경변수(SLACK_WEBHOOK_SALES_APPPUSH)를 먼저 읽던 방식은 다른 리포트용 Webhook 이 쓰여
# 다른 채널로 갔습니다. 환경변수는 읽지 않습니다.
SLACK_WEBHOOK_SECRET = ("kyungmin_inbox_report", "slack_webhook_pn01_apppush")
SLACK_CHANNEL_NAME = "#match-29cm-앱푸시-운영"
SLACK_MAX_RETRY = 2
WEEKDAY_KO = "월화수목금토일"


def _cell(text):
    return {"type": "raw_text", "text": text}


def _bold(text):
    return {"type": "rich_text", "elements": [{"type": "rich_text_section", "elements": [
        {"type": "text", "text": text, "style": {"bold": True}}]}]}


def _table(header, rows):
    return {
        "type": "table",
        "column_settings": [{"align": "left", "is_wrapped": True}] + [{"align": "right"}] * (len(header) - 1),
        "rows": [[_bold(h) for h in header]] + rows,
    }


def _section(text):
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def _context(text):
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": text}]}


def table_as_code(block):
    """table block 을 고정폭 코드블록 section 으로 바꾼다. 한글은 2칸으로 센다(Inbox 리포트와 동일)."""
    def txt(c):
        return c.get("text") or "".join(e["text"] for e in c["elements"][0]["elements"])
    def width(s):
        return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)
    rows = [[txt(c) for c in r] for r in block["rows"]]
    ws = [max(width(r[i]) for r in rows) for i in range(len(rows[0]))]
    lines = ["  ".join(c + " " * (ws[i] - width(c)) if i == 0 else " " * (ws[i] - width(c)) + c
                       for i, c in enumerate(r)) for r in rows]
    return {"type": "section", "text": {"type": "mrkdwn", "text": "```" + "\n".join(lines) + "```"}}


def webhook_post(url, payload, fallback=True):
    """성공은 HTTP 200 + 본문 'ok'. 429 는 Retry-After 대기 후 재시도, table 이 거부되면 코드블록 표로 1회 재발송."""
    for attempt in range(SLACK_MAX_RETRY + 1):
        res = requests.post(url, headers={"Content-Type": "application/json; charset=utf-8"},
                            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), timeout=10)
        if res.status_code == 429 and attempt < SLACK_MAX_RETRY:
            time.sleep(int(res.headers.get("Retry-After", "5")))
            continue
        break
    if res.status_code == 200 and res.text.strip() == "ok":
        print(f"[Slack] {SLACK_CHANNEL_NAME} 전송 OK")
        return
    if fallback and "invalid_blocks" in res.text and any(b["type"] == "table" for b in payload["blocks"]):
        print("[Slack] table block 거부 — 코드블록 표로 다시 보냅니다.")
        return webhook_post(url, {**payload, "blocks": [table_as_code(b) if b["type"] == "table" else b
                                                        for b in payload["blocks"]]}, fallback=False)
    raise RuntimeError(f"Slack 발송 실패 HTTP {res.status_code}: {res.text[:200]}")


def slack_notify(payload) -> None:
    """알림 실패가 발송 결과(로그·Job 성공 여부)를 바꾸지 않게 예외를 삼킵니다."""
    if DELIVERY_MODE != "LIVE":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    try:
        url = dbutils.secrets.get(scope=SLACK_WEBHOOK_SECRET[0], key=SLACK_WEBHOOK_SECRET[1]).strip()
        webhook_post(url, payload)
    except RuntimeError as exc:
        print(f"[Slack] {exc}")
    except Exception as exc:
        # 예외 메시지는 찍지 않습니다 — requests 오류 문구에 Webhook URL 이 들어갈 수 있습니다.
        print(f"[Slack] 알림 실패: {type(exc).__name__}")


def fail_live(reason: str) -> None:
    """LIVE 가 Braze 호출 전에 멈출 때 Slack 으로 알리고 중단합니다."""
    slack_notify({
        "text": f"[PN-01] {AS_OF_DATE} 발송 중단",
        "blocks": [
            _section(f":rotating_light: *PN-01 가격 넛징 발송 중단* ({AS_OF_DATE})\n• 사유: {reason}\n"
                     "• Braze 를 호출하기 전에 멈췄습니다. 17:30 KST 전에 Job 을 다시 실행하면 발송됩니다."),
            _context(f"Campaign `{BRAZE_CAMPAIGN_ID}` · run `{RUN_ID}`"),
        ],
    })
    raise RuntimeError(reason)


if DELIVERY_MODE == "LIVE":
    started_at = datetime.now(KST)
    if (started_at.hour, started_at.minute) < LIVE_EARLIEST_START:
        fail_live(
            f"LIVE 시작 시각 {started_at:%H:%M} — {LIVE_EARLIEST_START[0]:02d}:{LIVE_EARLIEST_START[1]:02d} KST "
            "이후에 시작해야 합니다(재검증이 발송 시점보다 낡음)."
        )

print(
    json.dumps(
        {
            "delivery_mode": DELIVERY_MODE,
            "campaign_id": BRAZE_CAMPAIGN_ID,
            "as_of_date": AS_OF_DATE,
            "daily_send_limit": DAILY_SEND_LIMIT,
        },
        ensure_ascii=False,
        indent=2,
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. 발송 직전 재검증 (F-9)

# COMMAND ----------

spark.table(OUTPUT_TABLES["audience"]).filter(
    (F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE)))
    & (F.col("is_control") == F.lit(False))
    & F.col("exclude_reason").isNull()
).createOrReplaceTempView("pn01_delivery_candidate")

# 03 이 오늘 audience 를 만들지 못했으면 Braze 를 호출하지 않고 멈춥니다. 2026-10-14 에는 01~03 이 다른 날짜로
# 저장돼 0명인 채로 "접수 0명" 정상 알림이 나갔습니다.
if DELIVERY_MODE == "LIVE" and spark.table("pn01_delivery_candidate").limit(1).count() == 0:
    latest_audience_date = (
        spark.table(OUTPUT_TABLES["audience"]).agg(F.max("as_of_date").alias("d")).collect()[0]["d"]
    )
    fail_live(
        f"03 audience 에 {AS_OF_DATE} 발송 대상이 없습니다(가장 최근 audience 날짜: {latest_audience_date}). "
        "01~03 이 오늘 정상 완료됐는지 확인하세요."
    )

# 담기 시그널만 담은 옵션을 넘기고, 좋아요·조회는 지금 판매 가능한 최저가 옵션으로 다시 고릅니다(02 와 같은 규칙).
spark.sql(
    """
    CREATE OR REPLACE TEMP VIEW pn01_recheck_input AS
    SELECT
        user_no,
        item_no,
        CASE WHEN signal_source = 'cart' THEN option_no ELSE NULL END AS option_no
    FROM pn01_delivery_candidate
    """
)
RECHECK_NOW_SQL = kst_now_literal()
create_price_candidate_view("pn01_recheck_input", "pn01_repriced", RECHECK_NOW_SQL)

preflight_df = spark.sql(
    f"""
    WITH member_status AS (
        SELECT
            CAST(user_no AS BIGINT) AS user_no,
            CASE
                WHEN UPPER(CAST(is_deleted AS STRING)) IN ('F', 'FALSE', '0', 'N')
                 AND UPPER(CAST(is_personal_info_agree AS STRING)) IN ('T', 'TRUE', '1', 'Y')
                 AND UPPER(CAST(is_receive_push AS STRING)) IN ('T', 'TRUE', '1', 'Y')
                    THEN TRUE ELSE FALSE
            END AS can_receive_push
        FROM {MEMBER_TABLE}
        WHERE user_no IN (SELECT user_no FROM pn01_delivery_candidate)
    ),
    purchased_now AS (
        -- CDC 주문 원천으로 당일 결제도 재확인합니다.
        SELECT DISTINCT CAST(user_no AS BIGINT) AS user_no
        FROM `29cm`.`orders`.`t_order`
        WHERE pay_timestamp >= DATE_SUB(DATE('{AS_OF_DATE}'), 2)
          AND UPPER(CAST(is_pay AS STRING)) IN ('T', 'TRUE', '1', 'Y')
          AND UPPER(CAST(is_cancel AS STRING)) IN ('F', 'FALSE', '0', 'N')
          AND UPPER(CAST(is_deleted AS STRING)) IN ('F', 'FALSE', '0', 'N')
          AND user_no IN (SELECT user_no FROM pn01_delivery_candidate)
    )
    SELECT
        candidate.*,
        repriced.final_price AS recheck_final_price,
        repriced.consumer_price AS recheck_consumer_price,
        repriced.coupon_no AS recheck_coupon_no,
        repriced.coupon_rate AS recheck_coupon_rate,
        repriced.remaining_qty AS recheck_remaining_qty,
        CASE
            WHEN NOT {str(INCLUDE_P3).upper()} AND candidate.variant = 'P3' THEN 'P3_COPY_UNAPPROVED'
            WHEN INSTR(candidate.push_title, CHR(34)) > 0 OR INSTR(candidate.push_body, CHR(34)) > 0
              OR INSTR(candidate.item_name, CHR(92)) > 0 OR INSTR(candidate.brand_name, CHR(92)) > 0
              OR INSTR(candidate.item_name, CHR(10)) > 0 OR INSTR(candidate.brand_name, CHR(10)) > 0
              OR INSTR(candidate.item_name, CHR(13)) > 0 OR INSTR(candidate.brand_name, CHR(13)) > 0
                THEN 'UNSAFE_WEBHOOK_JSON'
            WHEN COALESCE(member.can_receive_push, FALSE) = FALSE THEN 'NO_PUSH_CONSENT'
            WHEN purchase.user_no IS NOT NULL THEN 'PURCHASED_BEFORE_SEND'
            WHEN repriced.user_no IS NULL THEN 'RECHECK_NOT_FOUND'
            WHEN repriced.exclude_reason IS NOT NULL
                THEN CONCAT('RECHECK_', repriced.exclude_reason)
            WHEN (repriced.final_price < {PRICE_EXPOSE_THRESHOLD}) <> (candidate.variant = 'P1')
                THEN 'VARIANT_CHANGED_BEFORE_SEND'
            ELSE NULL
        END AS preflight_exclude_reason,
        COALESCE(
            repriced.final_price <> candidate.final_price
                OR repriced.consumer_price <> candidate.consumer_price,
            FALSE
        ) AS price_changed,
        {RECHECK_NOW_SQL} AS rechecked_at
    FROM pn01_delivery_candidate candidate
    LEFT JOIN member_status member ON member.user_no = candidate.user_no
    LEFT JOIN purchased_now purchase ON purchase.user_no = candidate.user_no
    LEFT JOIN pn01_repriced repriced
        ON repriced.user_no = candidate.user_no
       AND repriced.item_no = candidate.item_no
    """
)

# 가격이 바뀐 P1 은 새 가격으로 제목을 다시 만듭니다. 발송 값은 모두 recheck_* 기준입니다.
preflight_df = (
    preflight_df.withColumn(
        "push_title",
        F.when(
            (F.col("variant") == "P1") & F.col("price_changed"),
            F.concat(
                F.format_number(F.col("recheck_consumer_price").cast("bigint"), 0),
                F.lit("원 → "),
                F.format_number(F.col("recheck_final_price").cast("bigint"), 0),
                F.lit("원"),
            ),
        ).otherwise(F.col("push_title")),
    )
    .withColumn("final_price", F.coalesce(F.col("recheck_final_price"), F.col("final_price")))
    .withColumn(
        "consumer_price", F.coalesce(F.col("recheck_consumer_price"), F.col("consumer_price"))
    )
    .withColumn("coupon_no", F.coalesce(F.col("recheck_coupon_no"), F.col("coupon_no")))
    .withColumn("coupon_rate", F.coalesce(F.col("recheck_coupon_rate"), F.col("coupon_rate")))
    .withColumn("delivery_mode", F.lit(DELIVERY_MODE))
)

# 재검증 결과는 Guardrail(가격 불일치·skip 사유) 추적용으로 매일 저장합니다.
write_daily_partition(preflight_df, OUTPUT_TABLES["preflight"])
preflight_df = spark.table(OUTPUT_TABLES["preflight"]).filter(F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE)))

display(
    preflight_df.groupBy("preflight_exclude_reason", "price_changed")
    .agg(F.count("*").alias("customers"))
    .orderBy(F.desc("customers"))
)

sendable_df = preflight_df.filter(F.col("preflight_exclude_reason").isNull())

# 일일 상한 — 해시 순서로 자릅니다. 같은 날 재실행해도 남는 사람이 바뀌지 않습니다.
if DAILY_SEND_LIMIT > 0:
    sendable_total = sendable_df.count()
    if sendable_total > DAILY_SEND_LIMIT:
        sendable_df = (
            sendable_df.withColumn(
                "_send_order",
                F.pmod(F.xxhash64(F.concat_ws("|", "customer_id", "experiment_id")), F.lit(1000000)),
            )
            .orderBy("_send_order", "customer_id")
            .limit(DAILY_SEND_LIMIT)
            .drop("_send_order")
        )
    print(f"sendable={sendable_total:,}, limit={DAILY_SEND_LIMIT:,}")

# Slack 결과 메시지 — 01 대상부터 Braze 접수까지 퍼널 표 1개, 문구별 표 1개. PREVIEW 는 Braze 접수 칸을 비웁니다.
REASON_LABELS = {
    "P3_COPY_UNAPPROVED": "P3 문구 미승인", "PURCHASED_BEFORE_SEND": "발송 전 구매",
    "NO_PUSH_CONSENT": "동의 철회", "VARIANT_CHANGED_BEFORE_SEND": "8만 경계 이동",
}


def variant_counts(df) -> dict:
    return {row["variant"]: row["count"] for row in df.groupBy("variant").count().collect()}


def build_result_payload(requested_by_variant, accepted_by_variant=None, failed=0, requested_times=()):
    today = F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE))
    eligibility_users = spark.table(OUTPUT_TABLES["eligibility"]).filter(today).count()
    candidate_users = (
        spark.table(OUTPUT_TABLES["candidate"]).filter(today & F.col("is_eligible")).select("user_no").distinct().count()
    )
    audience = variant_counts(spark.table("pn01_delivery_candidate"))
    passed = variant_counts(preflight_df.filter(F.col("preflight_exclude_reason").isNull()))
    excluded = {
        row["preflight_exclude_reason"]: row["count"]
        for row in preflight_df.filter(F.col("preflight_exclude_reason").isNotNull())
        .groupBy("preflight_exclude_reason").count().collect()
    }
    sent = accepted_by_variant is not None
    requested = sum(requested_by_variant.values())
    accepted = sum(accepted_by_variant.values()) if sent else None
    top_reasons = sorted(excluded.items(), key=lambda kv: -kv[1])[:3]

    def num(value):
        return "—" if value is None else f"{value:,}"

    funnel = [
        ("01 대상", eligibility_users, "생애 미구매 · 푸시 도달 가능 · 시그널 보유"),
        ("02 적격", candidate_users, "재고 · 보유쿠폰 15% 이상"),
        ("03 audience", sum(audience.values()), "고객당 상품 1개 · 쿨다운 통과"),
        ("04 재검증 제외", sum(excluded.values()),
         " · ".join(f"{REASON_LABELS.get(k, k)} {v:,}" for k, v in top_reasons) or "—"),
        ("04 발송 가능", sum(passed.values()), "발송 직전 재검증 통과"),
        ("발송 요청", requested, f"일일 상한 {DAILY_SEND_LIMIT:,}" if DAILY_SEND_LIMIT > 0 else "상한 없음"),
        ("Braze 접수", accepted, f"실패 {failed:,}" if sent else "PREVIEW — 호출 안 함"),
    ]
    funnel_table = _table(["단계", "고객", "비고"], [[_cell(s), _cell(num(n)), _cell(note)] for s, n, note in funnel])
    funnel_table["column_settings"][2] = {"align": "left", "is_wrapped": True}
    variant_rows = [
        [_cell(label), _cell(num(audience.get(v, 0) if v else sum(audience.values()))),
         _cell(num(passed.get(v, 0) if v else sum(passed.values()))),
         _cell(num(requested_by_variant.get(v, 0) if v else requested)),
         _cell(num((accepted_by_variant.get(v, 0) if v else accepted) if sent else None))]
        for label, v in [("P1 가격 노출", "P1"), ("P2 브랜드 성장", "P2"), ("P3 일반", "P3"), ("합계", None)]
    ]
    if sent:
        headline = f"{'⚠️' if failed or requested == 0 else '✅'} *Braze 접수 {accepted:,}명* / 요청 {requested:,}명 · 실패 {failed:,}명"
    else:
        headline = f":eyes: *{DELIVERY_MODE}* — Braze 를 호출하지 않았습니다. 발송 예정 {requested:,}명"
    notes = ["접수 = Braze API 수락 기준(재수신·빈도 설정으로 실제 도달은 더 적을 수 있음)"]
    if requested_times:
        notes.append(f"요청 {min(requested_times):%H:%M:%S}~{max(requested_times):%H:%M:%S} KST")
    notes.append(f"Campaign `{BRAZE_CAMPAIGN_ID}` · run `{RUN_ID}`")
    day = f"{AS_OF_DATE_VALUE:%m/%d}({WEEKDAY_KO[AS_OF_DATE_VALUE.weekday()]})"
    return {
        "text": f"[PN-01] {AS_OF_DATE} {DELIVERY_MODE} — 요청 {requested:,}명" + (f" · 접수 {accepted:,}명" if sent else ""),
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"📲 PN-01 관심상품 가격 넛징 · {day}", "emoji": True}},
            _section(headline),
            funnel_table,
            # Slack 은 메시지당 table block 을 1개만 받으므로 문구별 표는 코드블록 표로 보냅니다.
            table_as_code(_table(["문구", "audience", "발송 가능", "발송 요청", "Braze 접수"], variant_rows)),
            _context(" · ".join(notes)),
        ],
    }


if DELIVERY_MODE == "PREVIEW":
    # Slack 으로 보내지 않고 payload 를 출력합니다. Block Kit Builder 에 blocks 를 붙여 형식을 확인할 수 있습니다.
    slack_notify(build_result_payload(variant_counts(sendable_df)))
    display(
        sendable_df.select(
            "customer_id", "variant", "push_title", "push_body", "item_no",
            "consumer_price", "final_price", "coupon_rate", "image_url", "landing_url",
        ).limit(100)
    )
    preview_message = (
        f"PREVIEW 완료: sendable={sendable_df.count():,}, "
        f"excluded={preflight_df.filter(F.col('preflight_exclude_reason').isNotNull()).count():,}"
    )
    print(preview_message)
    dbutils.notebook.exit(preview_message)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. API 사전 검사

# COMMAND ----------

BRAZE_API_KEY = dbutils.secrets.get(scope="marketing_automation", key="braze_29cm")
if not BRAZE_API_KEY.strip():
    raise ValueError("Braze REST API Key가 비어 있습니다.")
if DELIVERY_MODE == "TEST" and not TEST_EXTERNAL_USER_IDS:
    raise ValueError("TEST 모드에는 test_external_user_ids_json이 필요합니다.")

BRAZE_SEND_ENDPOINT = f"{BRAZE_REST_ENDPOINT}/campaigns/trigger/send"
BRAZE_HEADERS = {
    "Authorization": f"Bearer {BRAZE_API_KEY}",
    "Content-Type": "application/json",
}

# H-01 과 공용 로그 테이블. 없을 때만 H-01 과 같은 스키마로 만듭니다.
spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {OUTPUT_TABLES['delivery']} (
        delivery_key STRING, run_id STRING, as_of_date DATE, requested_date DATE,
        customer_id STRING, external_user_id STRING, scenario_id STRING,
        experiment_id STRING, campaign_id STRING, variant STRING, delivery_mode STRING,
        requested_at TIMESTAMP, http_status INT, dispatch_id STRING,
        delivery_status STRING, error_code STRING, error_message STRING,
        retry_count INT, payload_version STRING
    )
    USING DELTA
    PARTITIONED BY (requested_date)
    """
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. 발송 대상과 멱등키

# COMMAND ----------

live_delivery_df = sendable_df.withColumn(
    "delivery_key",
    F.sha2(
        F.concat_ws(
            "|",
            F.col("experiment_id"),
            F.col("customer_id"),
            F.col("scenario_id"),
            F.col("as_of_date").cast("string"),
        ),
        256,
    ),
)
# 발송 로그로 대상을 거르지 않습니다. 같은 날 재실행 시 중복 수신은 Braze 재수신 설정이 거릅니다.


def row_to_record(row, external_user_id: str, delivery_key: str) -> dict:
    return {
        "delivery_key": delivery_key,
        "customer_id": str(row["customer_id"]),
        "external_user_id": str(external_user_id),
        "scenario_id": str(row["scenario_id"]),
        "experiment_id": str(row["experiment_id"]),
        "variant": str(row["variant"]),
        "payload_version": str(row["payload_version"]),
        "trigger_properties": {
            "campaign_name": f"{SCENARIO_ID} 관심상품 보유쿠폰 가격 넛징",
            "scenario_id": str(row["scenario_id"]),
            "experiment_id": str(row["experiment_id"]),
            "variant": str(row["variant"]),
            "signal_source": str(row["signal_source"]),
            "brand_id": None if row["brand_id"] is None else str(row["brand_id"]),
            "brand_name": row["brand_name"],
            "product_id": str(row["item_no"]),
            "product_name": str(row["item_name"]),
            "consumer_price": int(row["consumer_price"]),
            "final_price": int(row["final_price"]),
            "coupon_no": None if row["coupon_no"] is None else str(row["coupon_no"]),
            "coupon_rate": round(float(row["coupon_rate"]), 4),
            "title": str(row["push_title"]),
            "contents": str(row["push_body"]),
            "image_url": str(row["image_url"]),
            "landing_url": str(row["landing_url"]),
            # 29CM Braze 템플릿의 기존 키와 호환되도록 별칭을 함께 보냅니다(H-01 과 동일).
            "img_url": str(row["image_url"]),
            "urll": str(row["landing_url"]),
        },
    }


if DELIVERY_MODE == "TEST":
    sample_rows = sendable_df.orderBy("customer_id").limit(
        max(len(TEST_EXTERNAL_USER_IDS), 1)
    ).collect()
    if not sample_rows:
        raise ValueError("TEST 발송에 사용할 Audience 샘플이 없습니다.")

    delivery_records = []
    for test_user_id, source_row in zip(
        TEST_EXTERNAL_USER_IDS,
        islice(cycle(sample_rows), len(TEST_EXTERNAL_USER_IDS)),
    ):
        raw_key = "|".join(
            ["TEST", EXPERIMENT_ID, str(test_user_id), str(source_row["customer_id"]), AS_OF_DATE]
        )
        delivery_records.append(
            row_to_record(
                source_row,
                external_user_id=str(test_user_id),
                delivery_key=hashlib.sha256(raw_key.encode("utf-8")).hexdigest(),
            )
        )

    print(
        json.dumps(
            {
                "test_recipient_count": len(delivery_records),
                "sample_records": [r["trigger_properties"] for r in delivery_records[:3]],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
else:
    delivery_records = [
        row_to_record(row, external_user_id=str(row["customer_id"]), delivery_key=str(row["delivery_key"]))
        # 2026-10-14 빈승혁: toLocalIterator 는 표준 모드(Spark Connect)에서 느려 collect 로 한 번에 받음 (H-01 과 동일)
        for row in live_delivery_df.collect()
    ]

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Braze 배치 발송 (H-01 과 동일)

# COMMAND ----------

DELIVERY_LOG_SCHEMA = T.StructType(
    [
        T.StructField("delivery_key", T.StringType(), False),
        T.StructField("run_id", T.StringType(), False),
        T.StructField("as_of_date", T.DateType(), False),
        T.StructField("requested_date", T.DateType(), False),
        T.StructField("customer_id", T.StringType(), False),
        T.StructField("external_user_id", T.StringType(), False),
        T.StructField("scenario_id", T.StringType(), False),
        T.StructField("experiment_id", T.StringType(), False),
        T.StructField("campaign_id", T.StringType(), False),
        T.StructField("variant", T.StringType(), False),
        T.StructField("delivery_mode", T.StringType(), False),
        T.StructField("requested_at", T.TimestampType(), False),
        T.StructField("http_status", T.IntegerType(), True),
        T.StructField("dispatch_id", T.StringType(), True),
        T.StructField("delivery_status", T.StringType(), False),
        T.StructField("error_code", T.StringType(), True),
        T.StructField("error_message", T.StringType(), True),
        T.StructField("retry_count", T.IntegerType(), False),
        T.StructField("payload_version", T.StringType(), False),
    ]
)


def chunked(records, size: int):
    batch = []
    for record in records:
        batch.append(record)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def request_braze(batch: list[dict]) -> tuple[int | None, dict, int, str | None]:
    payload = {
        "campaign_id": BRAZE_CAMPAIGN_ID,
        "recipients": [
            {"external_user_id": r["external_user_id"], "trigger_properties": r["trigger_properties"]}
            for r in batch
        ],
    }
    last_error = None
    for attempt in range(MAX_RETRIES):
        if DELIVERY_MODE == "LIVE" and datetime.now(KST) >= window_end:
            return None, {}, attempt, "SEND_WINDOW_CLOSED"
        try:
            response = requests.post(BRAZE_SEND_ENDPOINT, headers=BRAZE_HEADERS, json=payload, timeout=30)
            try:
                response_body = response.json()
            except ValueError:
                response_body = {"raw_response": response.text[:1000]}
            if not isinstance(response_body, dict):
                response_body = {"raw_response": str(response_body)[:1000]}

            if 200 <= response.status_code < 300:
                return response.status_code, response_body, attempt, None
            if (response.status_code == 429 or response.status_code >= 500) and attempt + 1 < MAX_RETRIES:
                retry_after = int(response.headers.get("Retry-After", 2**attempt)) if response.status_code == 429 else 2**attempt
                time.sleep(min(max(retry_after, 1), 60))
                last_error = json.dumps(response_body, ensure_ascii=False)[:1000]
                continue
            return (
                response.status_code,
                response_body,
                attempt,
                json.dumps(response_body, ensure_ascii=False)[:1000],
            )
        except requests.RequestException as exc:
            # 타임아웃은 Braze 가 이미 처리했을 수 있어 재시도가 중복 호출이 될 수 있습니다. 중복 수신은 Braze 재수신 설정이 거릅니다.
            last_error = str(exc)[:1000]
            if attempt + 1 < MAX_RETRIES:
                time.sleep(min(2**attempt, 30))
                continue
            return None, {}, attempt, last_error
    return None, {}, MAX_RETRIES, last_error


def delivery_log_rows(batch, status_code, response_body, retry_count, error_message, requested_at, status):
    dispatch_id = response_body.get("dispatch_id") if response_body else None
    return [
        (
            r["delivery_key"], RUN_ID, AS_OF_DATE_VALUE, requested_at.date(), r["customer_id"],
            r["external_user_id"], r["scenario_id"], r["experiment_id"], BRAZE_CAMPAIGN_ID,
            r["variant"], DELIVERY_MODE, requested_at, status_code, dispatch_id,
            status, None if status in ("ACCEPTED", "RESERVED") else "BRAZE_API_ERROR",
            None if status in ("ACCEPTED", "RESERVED") else error_message,
            retry_count, r["payload_version"],
        )
        for r in batch
    ]


def append_delivery_log(rows):
    if rows:
        spark.createDataFrame(rows, schema=DELIVERY_LOG_SCHEMA).write.format("delta").mode("append").saveAsTable(OUTPUT_TABLES["delivery"])


if DELIVERY_MODE == "LIVE":
    if AS_OF_DATE != datetime.now(KST).strftime("%Y-%m-%d"):
        fail_live(f"LIVE 기준일({AS_OF_DATE})이 KST 오늘과 다릅니다.")
    window_start = datetime.combine(AS_OF_DATE_VALUE, datetime.min.time(), KST).replace(hour=17, minute=20)
    window_end = window_start.replace(minute=30)
    if datetime.now(KST) >= window_end:
        fail_live("발송 시작 전 17:30 KST 마감 시각을 지났습니다.")
    while datetime.now(KST) < window_start:
        time.sleep(min(10, max(1, (window_start - datetime.now(KST)).total_seconds())))


def send_one_batch(batch_index, batch):
    if DELIVERY_MODE == "LIVE" and datetime.now(KST) >= window_end:
        return batch_index, batch, None, {}, 0, "SEND_WINDOW_CLOSED", datetime.now(KST).replace(tzinfo=None)
    status_code, response_body, retry_count, error_message = request_braze(batch)
    return batch_index, batch, status_code, response_body, retry_count, error_message, datetime.now(KST).replace(tzinfo=None)


# 발송 로그는 수신자 LOG_FLUSH_ROWS 명마다 중간 기록합니다. 도중에 노트북이 죽어도 기록된 접수는 03 쿨다운에 잡힙니다.
LOG_FLUSH_ROWS = 1000
batches = list(enumerate(chunked(delivery_records, BRAZE_BATCH_SIZE), start=1))
pending_rows = []
logged_rows = []
total_accepted = 0
total_failed = 0
with ThreadPoolExecutor(max_workers=8 if DELIVERY_MODE == "LIVE" else 1) as pool:
    futures = [pool.submit(send_one_batch, index, batch) for index, batch in batches]
    for future in as_completed(futures):
        batch_index, batch, status_code, response_body, retry_count, error_message, requested_at = future.result()
        accepted = status_code is not None and 200 <= status_code < 300 and not response_body.get("errors")
        status = "ACCEPTED" if accepted else "FAILED"
        pending_rows.extend(delivery_log_rows(batch, status_code, response_body, retry_count, error_message, requested_at, status))
        if accepted:
            total_accepted += len(batch)
        else:
            total_failed += len(batch)
        print(f"batch={batch_index}, recipients={len(batch)}, status={status_code}, retries={retry_count}")
        if len(pending_rows) >= LOG_FLUSH_ROWS:
            append_delivery_log(pending_rows)
            logged_rows.extend(pending_rows)
            pending_rows = []
append_delivery_log(pending_rows)
logged_rows.extend(pending_rows)

summary = f"{DELIVERY_MODE} 완료: accepted={total_accepted:,}, failed={total_failed:,}"
print(summary)

# LIVE 발송 결과를 Slack 으로 알립니다. 실패가 있어도 Job 을 멈추기 전에 먼저 보냅니다.


def counts_text(counts: dict) -> str:
    return " · ".join(f"{key} {value:,}" for key, value in sorted(counts.items())) or "-"


def send_delivery_slack() -> None:
    logged = [dict(zip(DELIVERY_LOG_SCHEMA.fieldNames(), row)) for row in logged_rows]
    accepted_by_variant = Counter(r["variant"] for r in logged if r["delivery_status"] == "ACCEPTED")
    print(f"accepted by variant: {counts_text(accepted_by_variant)}")
    slack_notify(build_result_payload(
        Counter(r["variant"] for r in delivery_records),
        accepted_by_variant,
        total_failed,
        [r["requested_at"] for r in logged],
    ))


if DELIVERY_MODE == "LIVE":
    try:
        send_delivery_slack()
    except Exception as exc:
        # 집계 실패가 발송 결과(로그 기록·Job 성공 여부)를 바꾸지 않게 합니다.
        print(f"[Slack] 알림 실패: {type(exc).__name__}")

if total_failed:
    raise RuntimeError(summary)
