# Databricks notebook source
# MAGIC %md
# MAGIC # PN-01 공통 설정 — 관심상품 × 보유쿠폰 가격 넛징
# MAGIC
# MAGIC 01~04 가 공유하는 파라미터, 원천 테이블, 저장 유틸, 그리고
# MAGIC **최종가 계산 함수(`create_price_candidate_view`)** 를 정의합니다.
# MAGIC 02(후보 산출)와 04(발송 직전 재검증)가 같은 함수를 써서 두 시점의 판정 기준이 어긋나지 않게 합니다.
# MAGIC
# MAGIC 설계서: Confluence 652903208 (PN-01 PRD 겸 파이프라인 설계) F-1 ~ F-13
# MAGIC 저장 유틸은 H-01 `00_h01_common` 의 `write_daily_partition` / `migrate_table_schema` 를 그대로 옮겼습니다.

# COMMAND ----------

import json
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql import types as T


def ensure_text_widget(name: str, default: str, label: str | None = None) -> None:
    """Create a text widget only when it does not already exist."""
    try:
        dbutils.widgets.get(name)
    except Exception:
        dbutils.widgets.text(name, default, label or name)


def ensure_dropdown_widget(
    name: str,
    default: str,
    choices: list[str],
    label: str | None = None,
) -> None:
    try:
        dbutils.widgets.get(name)
    except Exception:
        dbutils.widgets.dropdown(name, default, choices, label or name)


def widget(name: str) -> str:
    return dbutils.widgets.get(name).strip()


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def quoted_table(catalog: str, schema: str, table: str) -> str:
    return f"`{catalog}`.`{schema}`.`{table}`"


def spark_conf_or_none(key: str) -> str | None:
    try:
        return spark.conf.get(key)
    except Exception:
        return None

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 실행 파라미터

# COMMAND ----------

KST = ZoneInfo("Asia/Seoul")
DEFAULT_AS_OF_DATE = datetime.now(KST).strftime("%Y-%m-%d")

ensure_text_widget("as_of_date", DEFAULT_AS_OF_DATE, "기준일 (KST, yyyy-MM-dd)")
ensure_text_widget("run_id", "", "재실행 추적용 Run ID")
ensure_text_widget("scenario_id", "PN-01", "시나리오 ID")
ensure_text_widget("experiment_id", "PN01_V1_2026Q3", "실험 ID")
ensure_text_widget("output_catalog", "musinsa-ml-product-ws", "Output Catalog")
ensure_text_widget("output_schema", "common", "Output Schema")

# F-2 관심 시그널 기간
ensure_text_widget("like_lookback_days", "30", "좋아요 시그널 기간(일)")
ensure_text_widget("cart_lookback_days", "7", "장바구니 시그널 기간(일)")
ensure_text_widget("view_lookback_days", "7", "PDP 조회 시그널 기간(일)")
# F-5 · F-6 · P2 판정
ensure_text_widget("min_coupon_rate", "0.15", "쿠폰 할인액 ÷ 판매가 최소값")
ensure_text_widget("price_expose_threshold", "80000", "가격 노출(P1) 최종가 상한(미만)")
ensure_text_widget("brand_growth_ratio", "1.2", "P2 브랜드 주문 증가 배수(최근7일/직전7일)")
ensure_text_widget("brand_min_prev_orders", "30", "P2 판정 최소 직전7일 주문수")
# F-11 · F-12
ensure_text_widget("cooldown_days", "7", "고객 쿨다운(일)")
ensure_text_widget("item_cooldown_days", "14", "동일 상품 재발송 금지(일)")
# 2026-10-13 — 미발송 대조군을 두지 않습니다(0). 효과는 utm_term 세그먼트·선택 규칙(R0/R2) 비교로 봅니다.
ensure_text_widget("holdout_ratio", "0", "대조군 비율")
# 운영 Braze API-triggered 캠페인. 위젯으로 받지 않습니다 — 인터랙티브 세션에 남은 옛 위젯 값이
# 01~03 에 섞여 들어간 일이 있었습니다(2026-10-13: 01~03 은 5e35e80f, 04 는 47a43974 로 실행).
BRAZE_CAMPAIGN_ID = "47a43974-b251-4253-b2d7-a5fcbbdc352b"

AS_OF_DATE = widget("as_of_date")
SCENARIO_ID = widget("scenario_id")
EXPERIMENT_ID = widget("experiment_id")
OUTPUT_CATALOG = widget("output_catalog")
OUTPUT_SCHEMA = widget("output_schema")

LIKE_LOOKBACK_DAYS = int(widget("like_lookback_days"))
CART_LOOKBACK_DAYS = int(widget("cart_lookback_days"))
VIEW_LOOKBACK_DAYS = int(widget("view_lookback_days"))
MIN_COUPON_RATE = float(widget("min_coupon_rate"))
PRICE_EXPOSE_THRESHOLD = int(widget("price_expose_threshold"))
BRAND_GROWTH_RATIO = float(widget("brand_growth_ratio"))
BRAND_MIN_PREV_ORDERS = int(widget("brand_min_prev_orders"))
COOLDOWN_DAYS = int(widget("cooldown_days"))
ITEM_COOLDOWN_DAYS = int(widget("item_cooldown_days"))
HOLDOUT_RATIO = float(widget("holdout_ratio"))

RUN_ID = (
    widget("run_id")
    or spark_conf_or_none("spark.databricks.job.runId")
    or f"manual-{datetime.now(KST).strftime('%Y%m%d%H%M%S')}"
)

try:
    AS_OF_DATE_VALUE = datetime.strptime(AS_OF_DATE, "%Y-%m-%d").date()
except ValueError as exc:
    raise ValueError("as_of_date는 yyyy-MM-dd 형식이어야 합니다.") from exc
if not 0 <= HOLDOUT_RATIO < 1:
    raise ValueError("holdout_ratio는 0 이상 1 미만이어야 합니다.")
if not 0 < MIN_COUPON_RATE < 1:
    raise ValueError("min_coupon_rate는 0과 1 사이여야 합니다.")

print(
    json.dumps(
        {
            "as_of_date": AS_OF_DATE,
            "run_id": RUN_ID,
            "scenario_id": SCENARIO_ID,
            "experiment_id": EXPERIMENT_ID,
            "output": f"{OUTPUT_CATALOG}.{OUTPUT_SCHEMA}",
            "min_coupon_rate": MIN_COUPON_RATE,
            "price_expose_threshold": PRICE_EXPOSE_THRESHOLD,
            "holdout_ratio": HOLDOUT_RATIO,
            "braze_campaign_id": BRAZE_CAMPAIGN_ID or "(미설정)",
        },
        ensure_ascii=False,
        indent=2,
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. 원천 및 Output 테이블

# COMMAND ----------

MEMBER_TABLE = "`29cm`.`member`.`t_user`"
HEART_TABLE = "`29cm`.`member`.`t_heart`"
CART_TABLE = "`29cm`.`orders`.`t_cart_item`"
EVENT_TABLE = "`team`.`tech`.`cda_29cm_snowplow_event_mart_daily`"
ORDER_TABLE = "`datamart`.`datamart`.`29cm_mart_order`"
ITEM_TABLE = "`29cm`.`item`.`t_item`"
ITEM_IMAGE_TABLE = "`29cm`.`item`.`t_item_image`"
OPTION_TABLE = "`29cm`.`item`.`t_option`"
BRAND_TABLE = "`29cm`.`item`.`t_front_brand`"
COUPON_TABLE = "`29cm`.`orders`.`t_coupon`"
COUPON_ISSUE_TABLE = "`29cm`.`orders`.`t_coupon_issue`"
COUPON_ITEM_TABLE = "`29cm`.`orders`.`t_materialized_coupon_applicable_item`"
# 2026-10-13 — 실제 수신 가능 판정(29CM 앱 유효 기기)과 카테고리(md_group, H-01 과 같은 기준)
DEVICE_TABLE = "`29cm`.`campaign`.`t_device`"
PARTNER_BRAND_TABLE = "`29cm`.`admin`.`t_partner_brand`"
CATEGORY_MAPPING_TABLE = "`gspread`.`29cm_commerce`.`md_category_mapping`"

# utm_term 첫 토큰 — H-01 00 의 MD_GROUP_CODE_MAP 과 같은 코드(wf·fw·hm …)를 씁니다.
MD_GROUP_CODE_MAP = {
    "여성잡화": "wa",
    "여성패션": "wf",
    "풋웨어": "fw",
    "홈": "hm",
    "유니섹스": "us",
    "뷰티": "bt",
    "키즈": "kd",
    "테크": "tc",
    "푸드": "fd",
    "컬처": "cl",
    "액션스포츠": "as",
    "아웃도어스포츠": "os",
    "버티컬스포츠": "vs",
    "브랜드개발사업부": "bd",
    "KAM": "kam",
}
MD_GROUP_CODE_FALLBACK = "xx"
MD_GROUP_CODE_SQL_MAP = "MAP(" + ", ".join(
    f"{sql_string(group)}, {sql_string(code)}" for group, code in MD_GROUP_CODE_MAP.items()
) + ")"

OUTPUT_TABLES = {
    "signal": quoted_table(OUTPUT_CATALOG, OUTPUT_SCHEMA, "crm_price_nudge_signal_daily"),
    "eligibility": quoted_table(
        OUTPUT_CATALOG, OUTPUT_SCHEMA, "crm_price_nudge_eligibility_daily"
    ),
    "candidate": quoted_table(
        OUTPUT_CATALOG, OUTPUT_SCHEMA, "crm_price_nudge_candidate_daily"
    ),
    "audience": quoted_table(
        OUTPUT_CATALOG, OUTPUT_SCHEMA, "crm_price_nudge_braze_output"
    ),
    "preflight": quoted_table(
        OUTPUT_CATALOG, OUTPUT_SCHEMA, "crm_price_nudge_preflight_daily"
    ),
    # H-01 과 공용인 발송 로그. 스키마를 바꾸지 않습니다(scenario_id 로 구분).
    "delivery": quoted_table(OUTPUT_CATALOG, OUTPUT_SCHEMA, "braze_delivery_log"),
}

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{OUTPUT_CATALOG}`.`{OUTPUT_SCHEMA}`")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. 시각 기준
# MAGIC
# MAGIC 29CM DB 원천(`t_cart_item`, `t_heart`, `t_coupon_issue` 등)의 timestamp 는 **KST 벽시계 값**이 저장돼 있습니다
# MAGIC (2026-09-22 실측: 최신 행 시각이 조회 시점 KST 와 일치). 클러스터 세션 타임존과 무관하게
# MAGIC 비교하려고 "지금"을 Python 에서 KST 로 만들어 리터럴로 넣습니다.

# COMMAND ----------


def kst_now_literal() -> str:
    """SQL 에 넣을 현재 KST 시각 리터럴. 04 는 발송 직전에 다시 호출합니다."""
    return f"TIMESTAMP'{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}'"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. 최종가 계산 (F-3 · F-4 · F-5 · F-7 · F-8)
# MAGIC
# MAGIC 입력 뷰 컬럼: `user_no BIGINT, item_no BIGINT, option_no BIGINT(담기만, 나머지 NULL)`
# MAGIC 출력 뷰: 입력 1행당 1행. 조건 미달이면 `exclude_reason` 이 채워집니다.
# MAGIC
# MAGIC | 판정 | 규칙 |
# MAGIC |---|---|
# MAGIC | 상품 판매 가능 | `is_deleted='F'` · `item_stock_status=1` · 판매기간 내 |
# MAGIC | 옵션 판매 가능 | `is_deleted='F'` · `is_active='T'` · `option_stock_status=1` · `limited_qty − sold_qty > 0` |
# MAGIC | 단일 상품 (`use_option='F'`) | 옵션 행이 없으므로 상품 단위 재고 `t_item.limited_qty − sold_qty > 0` 로 판정 (좋아요 표본의 18%) |
# MAGIC | 옵션 기준 | 담기 → 담은 옵션 / 좋아요·조회 → 판매 가능 옵션 중 추가금 최저 |
# MAGIC | 보유 쿠폰 | issue 미사용·기간내 × coupon 미삭제·활성·`is_use_app='T'`·kind 3/4 × 적용상품 테이블 |
# MAGIC | 쿠폰 허용 상품 | `t_item.is_coupon_allowed_in_order='T'` |
# MAGIC | 할인액 | 정률 `min(최대할인, 기준가×율)` 10원 절사 / 정액 `sale_value`. `min_pay_amount` 미달이면 0 |
# MAGIC | 최종가 | 판매가 + 옵션가 − 할인액이 가장 큰 쿠폰 1장 (합산하지 않음) |
# MAGIC
# MAGIC 옵션 코드 21·9·10 등은 판매중으로 보지 않습니다. 2026-09-22 검토에서 코드 21 옵션 62만 개가
# MAGIC 전일 주문의 1%만 차지했습니다. 할인액 10원 절사는 푸시 가격이 실제보다 싸게 나가지 않도록 하는 보수적 처리입니다.

# COMMAND ----------


def create_price_candidate_view(input_view: str, output_view: str, now_sql: str) -> None:
    spark.sql(
        f"""
        CREATE OR REPLACE TEMP VIEW {output_view} AS
        WITH sig AS (
            SELECT DISTINCT
                CAST(user_no AS BIGINT) AS user_no,
                CAST(item_no AS BIGINT) AS item_no,
                CAST(option_no AS BIGINT) AS option_no
            FROM {input_view}
        ),
        item AS (
            SELECT
                CAST(item_no AS BIGINT) AS item_no,
                item_name,
                CAST(front_brand_no AS BIGINT) AS front_brand_no,
                CAST(sell_price AS DOUBLE) AS sell_price,
                CAST(consumer_price AS DOUBLE) AS consumer_price,
                is_coupon_allowed_in_order,
                use_option,
                COALESCE(is_limited_qty, 'T') <> 'T' OR limited_qty - sold_qty > 0 AS item_qty_ok,
                CAST(limited_qty - sold_qty AS INT) AS item_remaining_qty,
                CASE
                    WHEN is_deleted = 'F'
                     AND item_stock_status = 1
                     AND (available_begin_timestamp IS NULL
                          OR available_begin_timestamp <= {now_sql})
                     AND (COALESCE(use_without_available_end_date, 'F') = 'T'
                          OR available_end_timestamp IS NULL
                          OR available_end_timestamp > {now_sql})
                    THEN TRUE ELSE FALSE
                END AS item_sellable
            FROM {ITEM_TABLE}
            WHERE item_no IN (SELECT item_no FROM sig)
        ),
        opt AS (
            SELECT
                CAST(option_no AS BIGINT) AS option_no,
                CAST(item_no AS BIGINT) AS item_no,
                COALESCE(CAST(sell_price AS DOUBLE), 0D) AS option_price,
                CAST(limited_qty - sold_qty AS INT) AS remaining_qty,
                CASE
                    WHEN is_deleted = 'F'
                     AND is_active = 'T'
                     AND option_stock_status = 1
                     AND (COALESCE(is_limited_qty, 'T') <> 'T' OR limited_qty - sold_qty > 0)
                    THEN TRUE ELSE FALSE
                END AS option_sellable
            FROM {OPTION_TABLE}
            WHERE item_no IN (SELECT item_no FROM sig)
        ),
        cheapest_sellable AS (
            SELECT item_no, option_no, option_price, remaining_qty
            FROM (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY item_no ORDER BY option_price, option_no
                    ) AS rn
                FROM opt
                WHERE option_sellable
            )
            WHERE rn = 1
        ),
        sig_option AS (
            -- 담기는 담은 옵션, 좋아요·조회는 판매 가능 옵션 중 최저가 옵션
            SELECT
                sig.user_no,
                sig.item_no,
                sig.option_no AS signal_option_no,
                COALESCE(carted.option_no, cheapest.option_no) AS option_no,
                COALESCE(carted.option_price, cheapest.option_price) AS option_price,
                COALESCE(carted.remaining_qty, cheapest.remaining_qty) AS remaining_qty,
                CASE
                    WHEN sig.option_no IS NOT NULL THEN COALESCE(carted.option_sellable, FALSE)
                    ELSE cheapest.option_no IS NOT NULL
                END AS option_sellable
            FROM sig
            LEFT JOIN opt carted
                ON sig.option_no IS NOT NULL
               AND carted.option_no = sig.option_no
               AND carted.item_no = sig.item_no
            LEFT JOIN cheapest_sellable cheapest
                ON sig.option_no IS NULL
               AND cheapest.item_no = sig.item_no
        ),
        held AS (
            SELECT
                CAST(issue.user_no AS BIGINT) AS user_no,
                CAST(coupon.coupon_no AS BIGINT) AS coupon_no,
                CAST(coupon.coupon_kind AS INT) AS coupon_kind,
                CAST(coupon.sale_type AS INT) AS sale_type,
                CAST(coupon.sale_value AS DOUBLE) AS sale_value,
                COALESCE(CAST(coupon.max_sale_price AS DOUBLE), 0D) AS max_sale_price,
                COALESCE(CAST(coupon.min_pay_amount AS DOUBLE), 0D) AS min_pay_amount,
                issue.coupon_use_end_timestamp AS coupon_end_at
            FROM {COUPON_ISSUE_TABLE} issue
            INNER JOIN {COUPON_TABLE} coupon
                ON issue.coupon_no = coupon.coupon_no
            -- t_coupon_issue 는 파티션이 없습니다. user_no 로 먼저 좁혀야 합니다.
            WHERE issue.user_no IN (SELECT user_no FROM sig)
              AND issue.is_deleted = 'F'
              AND issue.is_coupon_using = 'F'
              AND issue.coupon_use_start_timestamp <= {now_sql}
              AND issue.coupon_use_end_timestamp > {now_sql}
              AND coupon.is_deleted = 'F'
              AND COALESCE(coupon.is_disabled, FALSE) = FALSE
              AND coupon.is_use_app = 'T'
              AND coupon.coupon_kind IN (3, 4)
              AND coupon.sale_type IN (1, 2)
        ),
        applicable AS (
            SELECT DISTINCT CAST(item_no AS BIGINT) AS item_no, CAST(coupon_no AS BIGINT) AS coupon_no
            FROM {COUPON_ITEM_TABLE}
            WHERE deleted_timestamp IS NULL
              AND item_no IN (SELECT item_no FROM sig)
        ),
        priced AS (
            SELECT
                so.*,
                item.item_name,
                item.front_brand_no,
                item.sell_price,
                item.consumer_price,
                item.item_sellable,
                item.is_coupon_allowed_in_order,
                item.use_option,
                item.item_qty_ok,
                item.item_remaining_qty,
                item.sell_price + COALESCE(so.option_price, 0D) AS base_price
            FROM sig_option so
            LEFT JOIN item ON item.item_no = so.item_no
        ),
        coupon_discount AS (
            SELECT
                priced.user_no,
                priced.item_no,
                held.coupon_no,
                held.coupon_kind,
                held.coupon_end_at,
                LEAST(
                    priced.base_price,
                    CASE
                        WHEN priced.base_price < held.min_pay_amount THEN 0D
                        WHEN held.sale_type = 1 THEN FLOOR(
                            LEAST(
                                CASE WHEN held.max_sale_price > 0 THEN held.max_sale_price
                                     ELSE 1E12 END,
                                priced.base_price * held.sale_value / 100
                            ) / 10
                        ) * 10
                        ELSE held.sale_value
                    END
                ) AS discount,
                -- 15% 판정용 절사 전 할인액. 절사 후로 판정하면 200원 단위가 아닌 가격의 15% 쿠폰이 탈락한다.
                CASE
                    WHEN priced.base_price < held.min_pay_amount THEN 0D
                    WHEN held.sale_type = 1 THEN LEAST(
                        CASE WHEN held.max_sale_price > 0 THEN held.max_sale_price ELSE 1E12 END,
                        priced.base_price * held.sale_value / 100)
                    ELSE LEAST(priced.base_price, held.sale_value)
                END AS raw_discount
            FROM priced
            INNER JOIN held ON held.user_no = priced.user_no
            INNER JOIN applicable
                ON applicable.item_no = priced.item_no
               AND applicable.coupon_no = held.coupon_no
        ),
        best AS (
            SELECT
                user_no,
                item_no,
                MAX(discount) AS discount,
                MAX_BY(coupon_no, discount) AS coupon_no,
                MAX_BY(coupon_kind, discount) AS coupon_kind,
                MAX_BY(raw_discount, discount) AS raw_discount,
                MAX_BY(coupon_end_at, discount) AS coupon_end_at,
                COUNT(*) AS held_coupon_count
            FROM coupon_discount
            WHERE discount > 0
            GROUP BY user_no, item_no
        )
        SELECT
            priced.user_no,
            priced.item_no,
            priced.signal_option_no,
            priced.option_no,
            CASE WHEN priced.use_option = 'F' THEN priced.item_remaining_qty
                 ELSE priced.remaining_qty END AS remaining_qty,
            priced.item_name,
            priced.front_brand_no,
            priced.consumer_price,
            priced.sell_price,
            priced.option_price,
            priced.base_price,
            best.coupon_no,
            best.coupon_kind,
            best.coupon_end_at,
            COALESCE(best.held_coupon_count, 0) AS held_coupon_count,
            COALESCE(best.discount, 0D) AS discount,
            priced.base_price - COALESCE(best.discount, 0D) AS final_price,
            COALESCE(best.discount, 0D) / NULLIF(priced.base_price, 0D) AS coupon_rate,
            CASE
                WHEN priced.sell_price IS NULL THEN 'ITEM_NOT_FOUND'
                WHEN NOT priced.item_sellable THEN 'ITEM_NOT_SELLABLE'
                WHEN NOT (CASE WHEN priced.use_option = 'F' THEN priced.item_qty_ok
                               ELSE priced.option_sellable END) THEN 'OPTION_NOT_SELLABLE'
                WHEN COALESCE(priced.is_coupon_allowed_in_order, 'F') <> 'T'
                    THEN 'COUPON_NOT_ALLOWED_ITEM'
                WHEN priced.consumer_price IS NULL
                  OR priced.consumer_price < priced.base_price
                    THEN 'PRICE_INVERTED'
                WHEN best.coupon_no IS NULL THEN 'NO_HELD_COUPON'
                WHEN best.raw_discount / priced.base_price < {MIN_COUPON_RATE} - 1E-9
                    THEN 'COUPON_RATE_BELOW_MIN'
                ELSE NULL
            END AS exclude_reason
        FROM priced
        LEFT JOIN best
            ON best.user_no = priced.user_no
           AND best.item_no = priced.item_no
        """
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. 저장 유틸 (H-01 `00_h01_common` 에서 이식)

# COMMAND ----------


def _schema_by_name(df: DataFrame) -> dict[str, T.DataType]:
    return {field.name: field.dataType for field in df.schema.fields}


def _type_name(data_type: T.DataType) -> str:
    return data_type.simpleString().lower()


def migrate_table_schema(df: DataFrame, table_name: str) -> dict[str, Any]:
    """DataFrame 에만 있는 신규 컬럼을 대상 Delta 테이블에 추가한다 (멱등)."""
    if not spark.catalog.tableExists(table_name):
        return {"status": "table_not_found", "added_columns": []}

    table_schema = _schema_by_name(spark.table(table_name))
    data_schema = _schema_by_name(df)

    type_conflicts = [
        {
            "column": name,
            "table": _type_name(table_schema[name]),
            "data": _type_name(data_schema[name]),
        }
        for name in sorted(set(table_schema) & set(data_schema))
        if _type_name(table_schema[name]) != _type_name(data_schema[name])
    ]
    if type_conflicts:
        raise ValueError(
            f"{table_name} 타입이 충돌합니다. 수동 마이그레이션이 필요합니다: {type_conflicts}"
        )

    dropped_columns = sorted(set(table_schema) - set(data_schema))
    if dropped_columns:
        raise ValueError(
            f"{table_name} 에 있는 컬럼이 DataFrame 에 없습니다. "
            f"컬럼 삭제는 자동 처리하지 않습니다: {dropped_columns}"
        )

    missing_columns = [
        (name, data_schema[name]) for name in df.columns if name not in table_schema
    ]
    if not missing_columns:
        return {"status": "already_current", "added_columns": []}

    columns_ddl = ", ".join(
        f"`{name}` {data_type.simpleString().upper()}"
        for name, data_type in missing_columns
    )
    spark.sql(f"ALTER TABLE {table_name} ADD COLUMNS ({columns_ddl})")
    spark.catalog.refreshTable(table_name)
    return {"status": "migrated", "added_columns": [name for name, _ in missing_columns]}


def write_daily_partition(df: DataFrame, table_name: str) -> dict[str, Any]:
    """as_of_date 파티션 1개만 멱등하게 교체한다."""
    if "as_of_date" not in df.columns:
        raise ValueError(f"{table_name} 저장 대상에 as_of_date 컬럼이 없습니다.")

    if not spark.catalog.tableExists(table_name):
        (
            df.write.format("delta")
            .mode("overwrite")
            .partitionBy("as_of_date")
            .saveAsTable(table_name)
        )
        result = {"status": "created", "table": table_name, "as_of_date": AS_OF_DATE}
        print(result)
        return result

    migration = migrate_table_schema(df, table_name)
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("replaceWhere", f"as_of_date = DATE('{AS_OF_DATE}')")
        .saveAsTable(table_name)
    )
    result = {
        "status": "partition_replaced",
        "table": table_name,
        "as_of_date": AS_OF_DATE,
        "migration": migration,
    }
    print(result)
    return result


def assert_unique(df: DataFrame, keys: list[str], label: str) -> None:
    duplicates = df.groupBy(*keys).count().filter(F.col("count") > 1).limit(1).count()
    if duplicates:
        raise ValueError(f"{label} 중복 키 발견: {keys}")


def assert_no_nulls(df: DataFrame, columns: list[str], label: str) -> None:
    condition = None
    for column in columns:
        current = F.col(column).isNull()
        condition = current if condition is None else condition | current
    if condition is not None and df.filter(condition).limit(1).count():
        raise ValueError(f"{label} 필수값 null 발견: {columns}")


print("PN-01 common configuration loaded.")
