# Databricks notebook source
# MAGIC %md
# MAGIC # PN-01 — 01 대상 (Eligibility & Signal)
# MAGIC
# MAGIC | 조건 | 규칙 (설계서 F-1 · F-2) |
# MAGIC |---|---|
# MAGIC | 생애 미구매 | `29cm_mart_order` 전 기간에 취소되지 않은 주문이 없음 |
# MAGIC | 회원 상태 | 탈퇴 아님 · 개인정보 동의 · 푸시 수신 동의 · 29CM 앱 유효 기기 보유 (시그널 수집 전에 먼저 거름) |
# MAGIC | 관심 시그널 | 좋아요(30일, `t_heart` PRT) · 담기(7일, 미삭제·미주문) · PDP 조회(7일) |
# MAGIC
# MAGIC 출력
# MAGIC - `crm_price_nudge_signal_daily` — as_of_date × user × item (02 입력)
# MAGIC - `crm_price_nudge_eligibility_daily` — as_of_date × user (QA·모수 추적)

# COMMAND ----------

# MAGIC %run ./pn01_00_common

# COMMAND ----------

NOW_SQL = kst_now_literal()
VIEW_START = AS_OF_DATE_VALUE - timedelta(days=VIEW_LOOKBACK_DAYS)
print({"now": NOW_SQL, "view_start": str(VIEW_START)})

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 관심 시그널
# MAGIC
# MAGIC `src_rank` 1=좋아요, 2=담기, 3=조회. 같은 상품에 여러 시그널이 있으면 **의향 점수(`intent_score`)가 가장 높은 시그널** 하나로 합칩니다.
# MAGIC 점수는 시그널 종류 × 경과일별 9/23 미발송 코호트의 7일 내 해당 상품 구매율(%)입니다. 담기는 어느 경과일이든 좋아요·조회보다 높으므로
# MAGIC 담기가 있으면 항상 담기 행이 남고, 담은 옵션이 02 로 넘어가 **그 옵션**의 재고·가격으로 판정됩니다.
# MAGIC 시그널은 푸시 동의 ∧ 29CM 앱 유효 기기 ∧ **생애 미구매** 고객(`pn01_target_user`)만 모읍니다. 기기가 없으면 14일 실수신율이 0.8% 였습니다(2026-10-12 실측).
# MAGIC 구매자를 시그널 병합 **전에** 거릅니다. 병합 후에 거르면 쌍의 98%(2,396만 중 2,349만)를 묶고 버리게 됩니다(2026-10-13 실측).

# COMMAND ----------

spark.sql(
    f"""
    CREATE OR REPLACE TEMP VIEW pn01_reachable_user AS
    SELECT DISTINCT CAST(member.user_no AS BIGINT) AS user_no
    FROM {MEMBER_TABLE} member
    INNER JOIN {DEVICE_TABLE} device
        ON device.user_no = member.user_no
    WHERE UPPER(CAST(member.is_deleted AS STRING)) IN ('F', 'FALSE', '0', 'N')
      AND UPPER(CAST(member.is_personal_info_agree AS STRING)) IN ('T', 'TRUE', '1', 'Y')
      AND UPPER(CAST(member.is_receive_push AS STRING)) IN ('T', 'TRUE', '1', 'Y')
      -- is_push_allow 는 실제 수신과 맞지 않아 쓰지 않습니다('F' 의 87% 가 실수신).
      AND device.is_deleted = 'F'
      AND device.app_kind = '29CM'
      AND device.token_status = 'VALID'
    """
)

# 생애 미구매 — H-01 과 같은 구매 기준: 수량 > 0, 취소 아님.
spark.sql(
    f"""
    CREATE OR REPLACE TEMP VIEW pn01_target_user AS
    SELECT reachable.user_no
    FROM pn01_reachable_user reachable
    LEFT ANTI JOIN (
        SELECT DISTINCT CAST(user_no AS BIGINT) AS user_no
        FROM {ORDER_TABLE}
        WHERE dt >= DATE('2010-01-01')
          AND COALESCE(CAST(order_count AS DOUBLE), 0D) > 0D
          AND CAST(order_item_cancel_status_code AS INT) = 0
    ) buyer
        ON buyer.user_no = reachable.user_no
    """
)

spark.sql(
    f"""
    CREATE OR REPLACE TEMP VIEW pn01_signal_raw AS
    SELECT
        CAST(user_no AS BIGINT) AS user_no,
        CAST(service_no AS BIGINT) AS item_no,
        CAST(NULL AS BIGINT) AS option_no,
        1 AS src_rank,
        insert_timestamp AS signal_at
    FROM {HEART_TABLE}
    WHERE heart_type = 'PRT'
      AND insert_timestamp >= {NOW_SQL} - INTERVAL {LIKE_LOOKBACK_DAYS} DAYS
      AND user_no IS NOT NULL
      AND user_no IN (SELECT user_no FROM pn01_target_user)
    UNION ALL
    SELECT
        CAST(user_no AS BIGINT),
        CAST(item_no AS BIGINT),
        CAST(option_no AS BIGINT),
        2,
        insert_timestamp
    FROM {CART_TABLE}
    WHERE insert_timestamp >= {NOW_SQL} - INTERVAL {CART_LOOKBACK_DAYS} DAYS
      AND user_no IS NOT NULL
      AND is_deleted = 'F'
      AND is_order_check = 'F'
      AND user_no IN (SELECT user_no FROM pn01_target_user)
    UNION ALL
    SELECT
        CAST(user_id AS BIGINT),
        CAST(item_no AS BIGINT),
        CAST(NULL AS BIGINT),
        3,
        CAST(event_timestamp AS TIMESTAMP)
    FROM {EVENT_TABLE}
    WHERE partition_date >= DATE('{VIEW_START:%Y-%m-%d}')
      AND partition_date < DATE('{AS_OF_DATE}')
      -- PDP 조회 한정. 이 필터가 없으면 전체 이벤트를 스캔합니다(H-01 실측 29배).
      AND event_name = 'view_page'
      AND page_name = 'item_detail'
      AND user_id > 0
      AND item_no IS NOT NULL
      AND user_id IN (SELECT user_no FROM pn01_target_user)
    """
)

# 상품당 1행: 의향 점수가 가장 높은 시그널, 같은 점수면 최근 시그널.
# 담기 옵션은 그 담기 행의 옵션을 그대로 씁니다(여러 옵션을 담았으면 최근 것).
# intent_cell — utm_term 세그먼트 첫 글자. c 담기 0~1일 · d 담기 2~7일 · l 좋아요 0~7일 · s 좋아요 8~30일
#               · v 조회 1일(마트가 D-1 이라 최소 1일) · w 조회 2~7일
spark.sql(
    f"""
    CREATE OR REPLACE TEMP VIEW pn01_signal AS
    SELECT user_no, item_no, option_no, src_rank, signal_at, signal_count,
           has_like, has_cart, intent_score, intent_cell
    FROM (
        SELECT
            *,
            COUNT(*) OVER (PARTITION BY user_no, item_no) AS signal_count,
            MAX(src_rank = 1) OVER (PARTITION BY user_no, item_no) AS has_like,
            MAX(src_rank = 2) OVER (PARTITION BY user_no, item_no) AS has_cart,
            ROW_NUMBER() OVER (
                PARTITION BY user_no, item_no
                ORDER BY intent_score DESC, signal_at DESC, option_no DESC
            ) AS rn
        FROM (
            SELECT
                *,
                CAST(CASE
                    WHEN src_rank = 2 THEN CASE WHEN age_days <= 1 THEN 4.3
                                                WHEN age_days <= 3 THEN 2.5 ELSE 1.3 END
                    WHEN src_rank = 1 THEN CASE WHEN age_days <= 1 THEN 0.7
                                                WHEN age_days <= 3 THEN 0.57
                                                WHEN age_days <= 7 THEN 0.33 ELSE 0.11 END
                    ELSE CASE WHEN age_days <= 1 THEN 0.43
                              WHEN age_days <= 3 THEN 0.18 ELSE 0.08 END
                END AS DOUBLE) AS intent_score,
                CASE
                    WHEN src_rank = 2 THEN CASE WHEN age_days <= 1 THEN 'c' ELSE 'd' END
                    WHEN src_rank = 1 THEN CASE WHEN age_days <= 7 THEN 'l' ELSE 's' END
                    ELSE CASE WHEN age_days <= 1 THEN 'v' ELSE 'w' END
                END AS intent_cell
            FROM (
                SELECT *, DATEDIFF(DATE('{AS_OF_DATE}'), signal_at) AS age_days
                FROM pn01_signal_raw
                WHERE item_no IS NOT NULL
            )
        )
    )
    WHERE rn = 1
    """
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. 생애 미구매 · 푸시 동의
# MAGIC
# MAGIC 1 의 `pn01_target_user` 에서 이미 거릅니다(동의 ∧ 29CM 앱 유효 기기 ∧ 생애 미구매). 그래서 eligibility 테이블에는
# MAGIC 시그널이 있는 대상 고객만 남고 `exclude_reason` 은 비어 있습니다. 2026-10-13 부터 '이미 구매'·'푸시 미동의' 사유 행은 쌓지 않습니다.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. 저장

# COMMAND ----------

# signal 을 한 번만 계산해 저장하고, 중복 검사와 eligibility 는 저장된 테이블에서 읽습니다.
# 임시 뷰는 캐시되지 않아 액션마다 원천부터 다시 계산합니다(2026-10-13: 액션 4회에 17분).
signal_df = spark.sql(
    f"""
    SELECT
        DATE('{AS_OF_DATE}') AS as_of_date,
        '{RUN_ID}' AS run_id,
        CAST(signal.user_no AS STRING) AS customer_id,
        signal.user_no,
        signal.item_no,
        signal.option_no,
        signal.src_rank,
        CASE signal.src_rank WHEN 1 THEN 'like' WHEN 2 THEN 'cart' ELSE 'view' END
            AS signal_source,
        signal.signal_at,
        signal.signal_count,
        signal.has_like,
        signal.has_cart,
        signal.intent_score,
        signal.intent_cell
    FROM pn01_signal signal
    """
)
write_daily_partition(signal_df, OUTPUT_TABLES["signal"])
signal_saved = spark.table(OUTPUT_TABLES["signal"]).filter(
    F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE))
)
assert_unique(signal_saved, ["as_of_date", "user_no", "item_no"], "crm_price_nudge_signal_daily")
signal_saved.createOrReplaceTempView("pn01_signal_saved")

eligibility_df = spark.sql(
    f"""
    SELECT
        DATE('{AS_OF_DATE}') AS as_of_date,
        '{RUN_ID}' AS run_id,
        CAST(user_no AS STRING) AS customer_id,
        user_no,
        COUNT(*) AS signal_item_count,
        TRUE AS push_consent,
        TRUE AS is_active_member,
        FALSE AS is_buyer,
        CAST(NULL AS STRING) AS exclude_reason,
        CURRENT_TIMESTAMP() AS created_at
    FROM pn01_signal_saved
    GROUP BY user_no
    """
)
write_daily_partition(eligibility_df, OUTPUT_TABLES["eligibility"])
assert_unique(
    spark.table(OUTPUT_TABLES["eligibility"]).filter(F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE))),
    ["as_of_date", "user_no"],
    "crm_price_nudge_eligibility_daily",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. QA — 모수 퍼널

# COMMAND ----------

display(
    spark.table(OUTPUT_TABLES["eligibility"])
    .filter(F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE)))
    .groupBy("exclude_reason")
    .agg(F.count("*").alias("users"))
    .orderBy(F.desc("users"))
)
display(
    spark.table(OUTPUT_TABLES["signal"])
    .filter(F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE)))
    .groupBy("signal_source", "intent_cell")
    .agg(F.count("*").alias("pairs"), F.countDistinct("user_no").alias("users"))
    .orderBy("intent_cell")
)
