# Databricks notebook source
# MAGIC %md
# MAGIC # PN-01 — 02 후보 (관심상품 × 보유쿠폰 × 재고)
# MAGIC
# MAGIC 01 의 시그널(고객 × 상품)마다 `create_price_candidate_view` 로 재고·보유쿠폰·최종가를 판정합니다.
# MAGIC 통과 여부와 무관하게 **모든 쌍을 저장**하고 `exclude_reason` 으로 구분합니다. 모수 퍼널 QA 에 필요하기 때문입니다.
# MAGIC
# MAGIC 출력: `crm_price_nudge_candidate_daily` — as_of_date × user × item

# COMMAND ----------

# MAGIC %run ./pn01_00_common

# COMMAND ----------

if not spark.catalog.tableExists(OUTPUT_TABLES["signal"]):
    raise ValueError(f"01 출력이 없습니다: {OUTPUT_TABLES['signal']}")

signal_today = spark.table(OUTPUT_TABLES["signal"]).filter(
    F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE))
)
if signal_today.limit(1).count() == 0:
    raise ValueError(f"{AS_OF_DATE} 시그널이 0건입니다. 01 을 먼저 실행하세요.")
signal_today.createOrReplaceTempView("pn01_signal_today")

NOW_SQL = kst_now_literal()
create_price_candidate_view("pn01_signal_today", "pn01_priced", NOW_SQL)

# COMMAND ----------

candidate_df = spark.sql(
    f"""
    SELECT
        DATE('{AS_OF_DATE}') AS as_of_date,
        '{RUN_ID}' AS run_id,
        signal.customer_id,
        signal.user_no,
        signal.item_no,
        signal.src_rank,
        signal.signal_source,
        signal.signal_at,
        signal.signal_count,
        signal.has_like,
        signal.has_cart,
        signal.intent_score,
        signal.intent_cell,
        priced.signal_option_no,
        priced.option_no,
        priced.remaining_qty,
        priced.item_name,
        priced.front_brand_no,
        priced.consumer_price,
        priced.sell_price,
        priced.option_price,
        priced.base_price,
        priced.coupon_no AS best_coupon_no,
        priced.coupon_kind,
        priced.coupon_end_at,
        priced.held_coupon_count,
        priced.discount,
        priced.final_price,
        priced.coupon_rate,
        priced.exclude_reason IS NULL AS is_eligible,
        priced.exclude_reason,
        {NOW_SQL} AS priced_at
    FROM pn01_signal_today signal
    INNER JOIN pn01_priced priced
        ON priced.user_no = signal.user_no
       AND priced.item_no = signal.item_no
    """
)

# 중복 검사는 저장 후 테이블에서 합니다. 저장 전에 하면 후보 계산 전체가 한 번 더 돕니다.
write_daily_partition(candidate_df, OUTPUT_TABLES["candidate"])
assert_unique(
    spark.table(OUTPUT_TABLES["candidate"]).filter(F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE))),
    ["as_of_date", "user_no", "item_no"],
    "crm_price_nudge_candidate_daily",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## QA

# COMMAND ----------

candidate_today = spark.table(OUTPUT_TABLES["candidate"]).filter(
    F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE))
)

# 제외 사유별 쌍 수
display(
    candidate_today.groupBy("exclude_reason")
    .agg(F.count("*").alias("pairs"), F.countDistinct("user_no").alias("users"))
    .orderBy(F.desc("pairs"))
)

# 통과 고객 수와 가격 노출(P1) 가능 고객 수 — 2026-09-22 사전 산출: 33,911 / 26,475 명
display(
    candidate_today.filter("is_eligible")
    .groupBy()
    .agg(
        F.countDistinct("user_no").alias("eligible_users"),
        F.countDistinct(
            F.when(F.col("final_price") < PRICE_EXPOSE_THRESHOLD, F.col("user_no"))
        ).alias("p1_possible_users"),
        F.expr("percentile_approx(final_price, 0.5)").alias("median_final_price"),
        F.expr("percentile_approx(coupon_rate, 0.5)").alias("median_coupon_rate"),
    )
)

# 샘플: 통과 건의 가격 계산을 눈으로 확인합니다.
display(
    candidate_today.filter("is_eligible")
    .select(
        "user_no", "item_no", "signal_source", "option_no", "consumer_price",
        "sell_price", "option_price", "best_coupon_no", "coupon_kind",
        "discount", "final_price", "coupon_rate", "remaining_qty",
    )
    .limit(50)
)
