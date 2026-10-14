# Databricks notebook source
# MAGIC %md
# MAGIC # PN-01 — 03 결정 (고객당 상품 1개 · 메시지 · 대조군)
# MAGIC
# MAGIC | 단계 | 규칙 (설계서) |
# MAGIC |---|---|
# MAGIC | 쿨다운 | 고객 7일 1회, 같은 상품 14일 (F-11). 대조군도 같은 주기로 재진입 |
# MAGIC | 상품 선택 | 고객 해시로 규칙 배정. **R2(80%)** 의향 점수(우대 카테고리 ×1.5) → 최종가 < 8만 우선 → 시그널 횟수 → 최근 시그널 / **R0(20%)** 현행 좋아요 > 담기 > 조회 → 우대 카테고리 → 8만 미만 → 쿠폰 할인율 → 최근 |
# MAGIC | 우대 카테고리 | 여성패션·홈·풋웨어 (md_group). 위젯 `priority_md_groups_json` · `priority_md_weight` |
# MAGIC | 대조군 | `xxhash64(customer_id|experiment_id)` 기준. 2026-10-13 부터 0% (미발송 대조군 없음) |
# MAGIC | variant | P1 최종가 < 8만 / P2 ≥ 8만 · 브랜드 주문 +20% / P3 그 외 (4장) |
# MAGIC | 측정 코드 | `utm_content` = `A{yymmdd}17{문구}{규칙}{의향}` 예 `A26101317A2C` (문구 A=P1·B=P2, 규칙 0=R0·2=R2, 의향 C·D·L·S·V·W) / `utm_term` = H-01 과 같은 카테고리 코드 예 `wf` |
# MAGIC
# MAGIC 출력: `crm_price_nudge_braze_output` — as_of_date × user

# COMMAND ----------

# MAGIC %run ./pn01_00_common

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 메시지·랜딩 규약 (H-01 과 동일)

# COMMAND ----------

# H-01 03 과 같은 29CM 웹훅 페이로드 계약입니다(2026-09-03 실측).
#   1) 랜딩은 app29cm:// 딥링크  2) 본문은 "(광고) " 로 시작, 수신거부 안내로 끝
#   3) 개행은 리터럴 백슬래시+n 으로 이스케이프
PUSH_DEEPLINK_PREFIX = "app29cm://web/https%3A%2F%2Fproduct.29cm.co.kr%2Fcatalog%2F"
PRODUCT_IMAGE_BASE_URL = "https://img.29cm.co.kr"
THUMBNAIL_IMAGE_TYPE = 3
DETAIL_IMAGE_TYPE = 4

ensure_text_widget(
    "utm_campaign",
    "ALL_push_MATCH_first-buyer-price-nudge_261013",
    "utm_campaign (캠페인명)",
)
UTM_CAMPAIGN = widget("utm_campaign")

# 광고 코드(utm_content) — H-01 과 같은 마케팅 코드 체계 A + yymmdd + 발송시각 + 군 + 접미 2자리.
# 군 자리는 문구(P1 → A, P2 → B), 접미 2자리는 상품 선택 규칙(0 = R0, 2 = R2) + 의향 셀(C·D·L·S·V·W) 입니다.
# P3 는 문구 미합의로 04 가 발송하지 않습니다. 'C' 는 URL 이 비지 않게 하는 자리표시입니다.
# 발송 시각이 정해지면(O-2) '17' 만 바꾸면 됩니다.
ensure_text_widget("ad_code_template", "A{yymmdd}17{variant}{rule}{intent}", "광고 코드 템플릿")
AD_CODE_TEMPLATE = widget("ad_code_template")
AD_CODE_YYMMDD = AS_OF_DATE.replace("-", "")[2:]
VARIANT_LETTERS = {"P1": "A", "P2": "B", "P3": "C"}
RULE_DIGITS = {"R0": "0", "R2": "2"}
INTENT_CELLS = ["c", "d", "l", "s", "v", "w"]
AD_CODE_BY_KEY = {
    f"{variant}|{rule}|{intent}": AD_CODE_TEMPLATE.format(
        yymmdd=AD_CODE_YYMMDD, variant=letter, rule=digit, intent=intent.upper()
    )
    for variant, letter in VARIANT_LETTERS.items()
    for rule, digit in RULE_DIGITS.items()
    for intent in INTENT_CELLS
}
if "{rule}" in AD_CODE_TEMPLATE and "{intent}" in AD_CODE_TEMPLATE:
    if len(set(AD_CODE_BY_KEY.values())) != len(AD_CODE_BY_KEY):
        raise ValueError(f"광고코드가 문구·규칙·의향을 구분하지 못합니다: {AD_CODE_TEMPLATE}")
AD_CODE_SQL_MAP = "MAP(" + ", ".join(
    f"'{key}', '{code}'" for key, code in AD_CODE_BY_KEY.items()
) + ")"

# P3 제목은 마케팅 확정 전 초안입니다(O-1).
ensure_text_widget("p3_title", "보유하신 쿠폰 할인 대상이에요", "P3 제목")
P3_TITLE = widget("p3_title")

HOLDOUT_BUCKETS = int(round(HOLDOUT_RATIO * 1000))

# 상품 선택 규칙 배정 — 두 군 모두 발송합니다. R0 = 현행(좋아요 우선), 나머지 = R2(의향 점수).
ensure_text_widget("pick_rule_r0_ratio", "0.2", "현행 상품 선택 규칙(R0) 배정 비율")
PICK_RULE_R0_BUCKETS = int(round(float(widget("pick_rule_r0_ratio")) * 1000))

# 우대 카테고리 — R2 는 의향 점수에 배수를 곱하고, R0 는 같은 시그널 종류 안에서 먼저 고릅니다.
# 10/12 시뮬레이션: ×1.5 에서 여성패션·홈·풋웨어 비중 54% → 63%, 평균 의향 점수 변화 없음.
ensure_text_widget(
    "priority_md_groups_json", json.dumps(["여성패션", "홈", "풋웨어"], ensure_ascii=False), "우대 카테고리(md_group)"
)
ensure_text_widget("priority_md_weight", "1.5", "우대 카테고리 의향 점수 배수(R2)")
PRIORITY_MD_GROUPS_SQL = ", ".join(sql_string(group) for group in json.loads(widget("priority_md_groups_json")))
PRIORITY_MD_WEIGHT = float(widget("priority_md_weight"))
if not PRIORITY_MD_GROUPS_SQL or PRIORITY_MD_WEIGHT < 1:
    raise ValueError("우대 카테고리는 1개 이상, 배수는 1 이상이어야 합니다.")

# 분석용 세그먼트(audience 컬럼) — 쿠폰 셀은 최선 쿠폰 만료까지 남은 일수, 가입 셀은 가입 경과일로 나눕니다.
#   쿠폰 1 = 30일 초과(가입 쿠폰 212407 등) · 2 = 7일 이내 · 3 = 8~30일 · 0 = 만료일 없음
#   가입 n = 30일 이내 · o = 초과
COUPON_URGENT_DAYS = 7
COUPON_LONG_DAYS = 30
NEW_SIGNUP_DAYS = 30

if not spark.catalog.tableExists(OUTPUT_TABLES["candidate"]):
    raise ValueError(f"02 출력이 없습니다: {OUTPUT_TABLES['candidate']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. 쿨다운 이력
# MAGIC
# MAGIC 발송 로그에는 상품 번호가 없으므로, 과거 audience(상품 포함)와 LIVE 발송 로그를 (고객, 기준일)로 맞춰 봅니다.
# MAGIC 대조군은 발송 로그가 없으므로 audience 에 대조군으로 배정된 이력을 그대로 씁니다.

# COMMAND ----------

if spark.catalog.tableExists(OUTPUT_TABLES["audience"]) and spark.catalog.tableExists(
    OUTPUT_TABLES["delivery"]
):
    spark.sql(
        f"""
        CREATE OR REPLACE TEMP VIEW pn01_history AS
        SELECT audience.customer_id, audience.item_no, audience.as_of_date
        FROM {OUTPUT_TABLES['audience']} audience
        LEFT JOIN (
            SELECT DISTINCT customer_id, as_of_date
            FROM {OUTPUT_TABLES['delivery']}
            WHERE scenario_id = '{SCENARIO_ID}'
              AND delivery_mode = 'LIVE'
              AND delivery_status = 'ACCEPTED'
              AND requested_date >= DATE_SUB(DATE('{AS_OF_DATE}'), {ITEM_COOLDOWN_DAYS + 1})
        ) sent
            ON sent.customer_id = audience.customer_id
           AND sent.as_of_date = audience.as_of_date
        WHERE audience.as_of_date >= DATE_SUB(DATE('{AS_OF_DATE}'), {ITEM_COOLDOWN_DAYS})
          AND audience.as_of_date < DATE('{AS_OF_DATE}')
          AND audience.exclude_reason IS NULL
          AND (sent.customer_id IS NOT NULL OR (audience.is_control AND EXISTS (
              SELECT 1 FROM {OUTPUT_TABLES['delivery']} variant_sent
              WHERE variant_sent.as_of_date = audience.as_of_date
                AND variant_sent.variant = audience.variant
                AND variant_sent.scenario_id = '{SCENARIO_ID}'
                AND variant_sent.delivery_mode = 'LIVE'
                AND variant_sent.delivery_status = 'ACCEPTED'
          )))
        """
    )
else:
    spark.sql(
        "CREATE OR REPLACE TEMP VIEW pn01_history AS "
        "SELECT CAST(NULL AS STRING) AS customer_id, CAST(NULL AS BIGINT) AS item_no, "
        "CAST(NULL AS DATE) AS as_of_date WHERE 1 = 0"
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. 고객당 상품 1개 선택

# COMMAND ----------

# 카테고리 — H-01 과 같은 기준(브랜드의 md_group 태그). 상품 → 파트너 브랜드 담당 MD → md_group.
# 우대 카테고리를 상품 선택에 쓰므로 오늘 적격 후보 전체에 대해 먼저 구합니다.
spark.sql(
    f"""
    CREATE OR REPLACE TEMP VIEW pn01_item_md_group AS
    SELECT CAST(item.item_no AS BIGINT) AS item_no, MAX(CAST(mapping.md_group AS STRING)) AS md_group
    FROM {ITEM_TABLE} item
    INNER JOIN {PARTNER_BRAND_TABLE} partner
        ON item.partner_brand_no = partner.partner_brand_no
    INNER JOIN {CATEGORY_MAPPING_TABLE} mapping
        ON partner.md_admin_no = mapping.md_code
    WHERE item.item_no IN (
        SELECT item_no FROM {OUTPUT_TABLES['candidate']}
        WHERE as_of_date = DATE('{AS_OF_DATE}') AND is_eligible
    )
    GROUP BY 1
    """
)

spark.sql(
    f"""
    CREATE OR REPLACE TEMP VIEW pn01_pick AS
    WITH eligible AS (
        SELECT candidate.*
        FROM {OUTPUT_TABLES['candidate']} candidate
        WHERE candidate.as_of_date = DATE('{AS_OF_DATE}')
          AND candidate.is_eligible
          -- 고객 쿨다운
          AND NOT EXISTS (
              SELECT 1 FROM pn01_history history
              WHERE history.customer_id = candidate.customer_id
                AND history.as_of_date > DATE_SUB(DATE('{AS_OF_DATE}'), {COOLDOWN_DAYS})
          )
          -- 같은 상품 쿨다운
          AND NOT EXISTS (
              SELECT 1 FROM pn01_history history
              WHERE history.customer_id = candidate.customer_id
                AND history.item_no = candidate.item_no
          )
    )
    , ruled AS (
        SELECT
            eligible.*,
            CASE
                WHEN PMOD(XXHASH64(CONCAT_WS('|', customer_id, '{EXPERIMENT_ID}', 'pick_rule')), 1000)
                     < {PICK_RULE_R0_BUCKETS} THEN 'R0'
                ELSE 'R2'
            END AS pick_rule,
            COALESCE(md.md_group IN ({PRIORITY_MD_GROUPS_SQL}), FALSE) AS is_priority_md
        FROM eligible
        LEFT JOIN pn01_item_md_group md ON md.item_no = eligible.item_no
    )
    SELECT *
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY user_no
                ORDER BY
                    -- R0: 현행 좋아요 > 담기 > 조회 (병합 전 기준을 has_like·has_cart 로 재현)
                    CASE WHEN pick_rule = 'R0' THEN
                        CASE WHEN has_like THEN 1 WHEN has_cart THEN 2 ELSE 3 END
                    ELSE 0 END,
                    -- R0: 같은 시그널 종류 안에서 우대 카테고리 먼저
                    CASE WHEN pick_rule = 'R0' AND NOT is_priority_md THEN 1 ELSE 0 END,
                    -- R2: 의향 점수 × 우대 카테고리 배수
                    CASE WHEN pick_rule = 'R2'
                         THEN -intent_score * CASE WHEN is_priority_md THEN {PRIORITY_MD_WEIGHT} ELSE 1 END
                         ELSE 0 END,
                    CASE WHEN final_price < {PRICE_EXPOSE_THRESHOLD} THEN 0 ELSE 1 END,
                    CASE WHEN pick_rule = 'R0' THEN -coupon_rate ELSE -signal_count END,
                    signal_at DESC,
                    item_no
            ) AS pick_rank
        FROM ruled
    )
    WHERE pick_rank = 1
    """
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. 브랜드 주문 추이 (P2 판정) · 이미지 · 브랜드명

# COMMAND ----------

spark.sql(
    f"""
    CREATE OR REPLACE TEMP VIEW pn01_brand_growth AS
    SELECT
        CAST(front_brand_no AS BIGINT) AS front_brand_no,
        SUM(CASE WHEN dt >= DATE_SUB(DATE('{AS_OF_DATE}'), 7) THEN order_count ELSE 0 END)
            AS orders_recent_7d,
        SUM(CASE WHEN dt < DATE_SUB(DATE('{AS_OF_DATE}'), 7) THEN order_count ELSE 0 END)
            AS orders_prev_7d
    FROM {ORDER_TABLE}
    WHERE dt >= DATE_SUB(DATE('{AS_OF_DATE}'), 14)
      AND dt < DATE('{AS_OF_DATE}')
      AND front_brand_no IN (SELECT front_brand_no FROM pn01_pick)
    GROUP BY 1
    """
)

# 대표 이미지 — H-01 02 와 같은 우선순위(정사각 썸네일 > 기타 > 상세, 세로 2배 미만, ordering_idx)
spark.sql(
    f"""
    CREATE OR REPLACE TEMP VIEW pn01_item_image AS
    SELECT item_no, product_image_url
    FROM (
        SELECT
            CAST(item_no AS BIGINT) AS item_no,
            CASE
                WHEN TRIM(image_url) LIKE 'https://%' THEN TRIM(image_url)
                WHEN TRIM(image_url) LIKE 'http://%'
                    THEN CONCAT('https://', SUBSTRING(TRIM(image_url), 8))
                WHEN TRIM(image_url) LIKE '//%' THEN CONCAT('https:', TRIM(image_url))
                WHEN TRIM(image_url) LIKE '/%'
                    THEN CONCAT('{PRODUCT_IMAGE_BASE_URL}', TRIM(image_url))
                ELSE CONCAT('{PRODUCT_IMAGE_BASE_URL}/', TRIM(image_url))
            END AS product_image_url,
            ROW_NUMBER() OVER (
                PARTITION BY item_no
                ORDER BY
                    CASE WHEN UPPER(CAST(is_deleted AS STRING)) IN ('F', 'FALSE', '0', 'N')
                         THEN 0 ELSE 1 END,
                    CASE WHEN CAST(image_type AS INT) = {THUMBNAIL_IMAGE_TYPE} THEN 0
                         WHEN CAST(image_type AS INT) = {DETAIL_IMAGE_TYPE} THEN 2
                         ELSE 1 END,
                    CASE WHEN image_width IS NULL OR image_height IS NULL THEN 1
                         WHEN CAST(image_height AS DOUBLE) <= 2 * CAST(image_width AS DOUBLE)
                             THEN 0
                         ELSE 2 END,
                    COALESCE(CAST(ordering_idx AS BIGINT), 2147483647),
                    CAST(item_image_no AS BIGINT) DESC
            ) AS image_rank
        FROM {ITEM_IMAGE_TABLE}
        WHERE item_no IN (SELECT item_no FROM pn01_pick)
          AND image_url IS NOT NULL
          AND TRIM(image_url) <> ''
          AND UPPER(CAST(is_deleted AS STRING)) IN ('F', 'FALSE', '0', 'N')
    )
    WHERE image_rank = 1
    """
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Audience 생성

# COMMAND ----------

audience_df = spark.sql(
    f"""
    WITH base AS (
        SELECT
            pick.*,
            brand.brand_name_kor AS brand_name,
            image.product_image_url AS image_url,
            COALESCE(
                growth.orders_prev_7d >= {BRAND_MIN_PREV_ORDERS}
                AND growth.orders_recent_7d >= growth.orders_prev_7d * {BRAND_GROWTH_RATIO},
                FALSE
            ) AS brand_growing,
            growth.orders_recent_7d,
            growth.orders_prev_7d,
            PMOD(XXHASH64(CONCAT_WS('|', pick.customer_id, '{EXPERIMENT_ID}')), 1000)
                < {HOLDOUT_BUCKETS} AS is_control,
            md.md_group,
            COALESCE(ELEMENT_AT({MD_GROUP_CODE_SQL_MAP}, md.md_group), '{MD_GROUP_CODE_FALLBACK}')
                AS md_group_code,
            CASE
                WHEN pick.coupon_end_at IS NULL THEN '0'
                WHEN DATEDIFF(pick.coupon_end_at, DATE('{AS_OF_DATE}')) <= {COUPON_URGENT_DAYS} THEN '2'
                WHEN DATEDIFF(pick.coupon_end_at, DATE('{AS_OF_DATE}')) <= {COUPON_LONG_DAYS} THEN '3'
                ELSE '1'
            END AS coupon_cell,
            CASE
                WHEN DATEDIFF(DATE('{AS_OF_DATE}'), member.insert_timestamp) <= {NEW_SIGNUP_DAYS} THEN 'n'
                ELSE 'o'
            END AS tenure_cell
        FROM pn01_pick pick
        LEFT JOIN {BRAND_TABLE} brand
            ON CAST(brand.front_brand_no AS BIGINT) = pick.front_brand_no
        LEFT JOIN pn01_item_image image ON image.item_no = pick.item_no
        LEFT JOIN pn01_brand_growth growth ON growth.front_brand_no = pick.front_brand_no
        LEFT JOIN pn01_item_md_group md ON md.item_no = pick.item_no
        LEFT JOIN {MEMBER_TABLE} member ON CAST(member.user_no AS BIGINT) = pick.user_no
    ),
    varianted AS (
        SELECT
            *,
            CASE
                WHEN final_price < {PRICE_EXPOSE_THRESHOLD} THEN 'P1'
                WHEN brand_growing THEN 'P2'
                ELSE 'P3'
            END AS variant
        FROM base
    ),
    coded AS (
        -- utm_content 는 문구·규칙·의향을 담은 광고코드, utm_term 은 H-01 과 같은 카테고리 코드입니다.
        SELECT
            *,
            ELEMENT_AT({AD_CODE_SQL_MAP}, CONCAT_WS('|', variant, pick_rule, intent_cell)) AS utm_content,
            md_group_code AS utm_term
        FROM varianted
    )
    SELECT
        '{RUN_ID}' AS run_id,
        as_of_date,
        customer_id,
        user_no,
        '{SCENARIO_ID}' AS scenario_id,
        '{EXPERIMENT_ID}' AS experiment_id,
        {sql_string(BRAZE_CAMPAIGN_ID)} AS campaign_id,
        item_no,
        item_name,
        front_brand_no AS brand_id,
        brand_name,
        option_no,
        signal_source,
        consumer_price,
        base_price,
        discount,
        final_price,
        best_coupon_no AS coupon_no,
        coupon_kind,
        coupon_rate,
        variant,
        is_control,
        pick_rule, md_group, md_group_code, is_priority_md, intent_cell, intent_score,
        coupon_cell, coupon_end_at, tenure_cell, utm_content, utm_term,
        orders_recent_7d AS brand_orders_recent_7d,
        orders_prev_7d AS brand_orders_prev_7d,
        CASE variant
            WHEN 'P1' THEN CONCAT(
                FORMAT_NUMBER(CAST(consumer_price AS BIGINT), 0), '원 → ',
                FORMAT_NUMBER(CAST(final_price AS BIGINT), 0), '원'
            )
            WHEN 'P2' THEN CONCAT('최근 ', TRIM(brand_name), ' 구매가 늘고 있어요!')
            ELSE {sql_string(P3_TITLE)}
        END AS push_title,
        CONCAT(
            '(광고) 관심 있게 보신 ', TRIM(brand_name),
            ' 아이템을 보유하신 쿠폰으로 더 저렴하게 구매할 수 있어요!',
            CHR(92), 'n', '▶️ ', TRIM(item_name),
            CHR(92), 'n', CHR(92), 'n', '※수신거부 : MY > 설정'
        ) AS push_body,
        image_url,
        CONCAT(
            '{PUSH_DEEPLINK_PREFIX}', CAST(item_no AS STRING),
            '?utm_source=push&utm_medium=retention_push',
            '&utm_campaign={UTM_CAMPAIGN}',
            '&utm_content=', utm_content,
            '&utm_term=', utm_term
        ) AS landing_url,
        CASE
            WHEN brand_name IS NULL OR TRIM(brand_name) = '' THEN 'BRAND_NAME_UNAVAILABLE'
            WHEN item_name IS NULL OR TRIM(item_name) = '' THEN 'ITEM_NAME_UNAVAILABLE'
            WHEN image_url IS NULL OR image_url NOT LIKE 'https://%' THEN 'IMAGE_URL_UNAVAILABLE'
            ELSE NULL
        END AS exclude_reason,
        CURRENT_TIMESTAMP() AS created_at,
        'pn01-v1' AS payload_version
    FROM coded
    """
)

# 검사는 저장 후 테이블에서 합니다. 저장 전에 하면 결정 계산 전체가 검사마다 한 번씩 더 돕니다.
# 검사에 실패하면 Job 이 멈춰 04 가 돌지 않습니다.
write_daily_partition(audience_df, OUTPUT_TABLES["audience"])
audience_saved = spark.table(OUTPUT_TABLES["audience"]).filter(
    F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE))
)
assert_unique(audience_saved, ["as_of_date", "customer_id"], "crm_price_nudge_braze_output")
assert_no_nulls(
    audience_saved,
    ["customer_id", "item_no", "variant", "final_price", "consumer_price", "landing_url", "utm_term"],
    "crm_price_nudge_braze_output",
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. QA

# COMMAND ----------

audience_today = spark.table(OUTPUT_TABLES["audience"]).filter(
    F.col("as_of_date") == F.to_date(F.lit(AS_OF_DATE))
)
display(
    audience_today.groupBy("is_control", "variant", "exclude_reason")
    .agg(F.count("*").alias("customers"))
    .orderBy("is_control", "variant")
)
# 광고코드 × 카테고리 발송 규모 — 클릭·주문 집계의 분모. 우대 카테고리 비중도 함께 봅니다.
display(
    audience_today.filter(F.col("exclude_reason").isNull())
    .groupBy("utm_content", "utm_term", "is_priority_md")
    .agg(F.count("*").alias("customers"))
    .orderBy(F.desc("customers"))
)
display(
    audience_today.filter(F.col("exclude_reason").isNull())
    .select("customer_id", "variant", "push_title", "push_body", "item_no",
            "consumer_price", "final_price", "coupon_rate", "landing_url", "image_url")
    .limit(50)
)
