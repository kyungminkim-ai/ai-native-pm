"""Pipeline 2 — Rule-based 메타데이터 생성 + LLM 메시지 생성."""
import logging
import pandas as pd
from config import (
    CONFIDENCE_THRESHOLD, AD_CODE_SEED_FILE, AD_CODE_PREFIX,
    CAMPAIGN_META_SYNC_PATH,
)
from rules import (
    classify_target, get_content_type, get_priority, get_category_id,
    is_title_valid, sanitize_title, generate_ad_code, build_push_url,
    append_unsubscribe, lookup_brand_name, build_category_list_str,
    build_braze_campaign_name, build_feed_url, build_webhook_contents,
    select_contents,
)
from llm_client import regenerate_title, generate_v1, generate_v2, generate_v3, set_current_row, infer_category_ids

logger = logging.getLogger(__name__)


def _base36_val(code: str) -> int:
    """APSCMCD 코드의 suffix를 Base36 정수로 변환."""
    suffix = code[len(AD_CODE_PREFIX):]
    val = 0
    for c in suffix.upper():
        val = val * 36 + int(c, 36)
    return val


def _load_last_ad_code() -> str:
    """campaign_meta_sync.csv 최댓값과 seed 파일 중 더 큰 APSCMCD 코드를 반환."""
    candidates = []

    # 1. campaign_meta_sync.csv에서 최댓값 (정식 소스)
    try:
        df = pd.read_csv(CAMPAIGN_META_SYNC_PATH, usecols=["ad_code"])
        codes = df["ad_code"].dropna()
        codes = codes[codes.str.startswith(AD_CODE_PREFIX)]
        if not codes.empty:
            candidates.append(max(codes, key=_base36_val))
    except Exception:
        pass

    # 2. seed 파일 (동일 세션 내 이전 실행 결과)
    try:
        seed = AD_CODE_SEED_FILE.read_text().strip()
        if seed.startswith(AD_CODE_PREFIX):
            candidates.append(seed)
    except FileNotFoundError:
        pass

    return max(candidates, key=_base36_val) if candidates else f"{AD_CODE_PREFIX}000"


def _save_last_ad_code(code: str) -> None:
    AD_CODE_SEED_FILE.parent.mkdir(parents=True, exist_ok=True)
    AD_CODE_SEED_FILE.write_text(code)


def _merge_category_ids(base_cat: str, llm_cats: list) -> str:
    """팀명 매핑(base_cat)과 LLM 유추(llm_cats)를 합쳐 최대 3개 반환."""
    seen = []
    if base_cat:
        seen.append(base_cat)
    for c in llm_cats:
        if c and c not in seen:
            seen.append(c)
    return ",".join(seen[:3])


def process_row(row: pd.Series, brand_df: pd.DataFrame, current_ad_code: str, category_df=None) -> dict:
    brand_id          = str(row.get("sourceBrandId", "") or "")
    promotion_content = str(row.get("promotion_content", "") or "")
    landing_url       = str(row.get("landing_url", "") or "").strip()
    original_title    = sanitize_title(str(row.get("main_title", "") or ""))
    team_name         = str(row.get("register_team_name", "") or "")
    event_name        = str(row.get("event_name", "") or "")
    img_url           = str(row.get("img_url", "") or "")
    send_dt           = str(row.get("send_dt", "") or "")
    remarks           = str(row.get("remarks", "") or "")

    # 브랜드 한국어명 조회
    brand_name = lookup_brand_name(brand_id, brand_df)

    result = {}

    # ── category_id: 팀명 매핑 + LLM 유추 ──────────────────────────────
    base_cat = get_category_id(team_name)
    cat_list_str = build_category_list_str(category_df) if category_df is not None else ""
    llm_cats = infer_category_ids(event_name, promotion_content, original_title, landing_url, cat_list_str)
    merged_category_id = _merge_category_ids(base_cat, llm_cats)

    # ── Rule-based ──────────────────────────────────────────────────────
    result["send_dt"]      = send_dt   # P1에서 각 행에 설정된 발송일 명시적 전달
    result["send_time"]    = "11:00"
    result["target"]       = classify_target(team_name, brand_id=brand_id, brand_df=brand_df)
    result["priority"]     = get_priority(team_name, landing_url)
    result["content_type"] = get_content_type(landing_url)
    result["brand_id"]     = brand_id
    result["category_id"]  = merged_category_id
    result["landing_url"]  = landing_url
    result["image_url"]    = img_url
    result["goods_id"]     = ""
    result["team_id"]      = team_name
    result["stopped"]      = ""

    # ── 광고 코드 & push_url ─────────────────────────────────────────────
    ad_code = generate_ad_code(current_ad_code)
    result["ad_code"]   = ad_code
    result["push_url"]  = build_push_url(landing_url, ad_code)

    # ── 제목 처리 ────────────────────────────────────────────────────────
    if is_title_valid(original_title):
        result["title"]        = original_title
        result["title_source"] = "original"
    else:
        regen = regenerate_title(brand_name, promotion_content, result["target"], remarks=remarks)
        if regen:
            result["title"]        = regen
            result["title_source"] = "llm"
        else:
            result["title"]        = original_title
            result["title_source"] = "fallback"

    # ── V1 BENEFIT ───────────────────────────────────────────────────────
    v1 = generate_v1(
        title=result["title"],
        brand=brand_name,
        promotion_content=promotion_content,
        content_type=result["content_type"] or "",
        target=result["target"],
        remarks=remarks,
    )
    result["contents_v1"]   = append_unsubscribe(v1["message"]) if v1["message"] else None
    result["confidence_v1"] = v1["confidence"]

    # ── V2 BRAND ─────────────────────────────────────────────────────────
    v2 = generate_v2(
        title=result["title"],
        brand=brand_name,
        promotion_content=promotion_content,
        content_type=result["content_type"] or "",
        target=result["target"],
        remarks=remarks,
    )
    result["contents_v2"]   = append_unsubscribe(v2["message"]) if v2["message"] else None
    result["confidence_v2"] = v2["confidence"]

    # ── V3 SCARCITY ───────────────────────────────────────────────────────
    v3 = generate_v3(
        title=result["title"],
        brand=brand_name,
        promotion_content=promotion_content,
        content_type=result["content_type"] or "",
        target=result["target"],
        remarks=remarks,
    )
    result["contents_v3"]   = append_unsubscribe(v3["message"]) if v3["message"] else None
    result["confidence_v3"] = v3["confidence"]

    # ── 발송 본문 자동 선택 (V1 우선 → V3 희소성 → V2 기본) ─────────────
    selected_msg, selected_src = select_contents(
        result["contents_v1"], result["contents_v2"], result["contents_v3"]
    )
    result["contents"]         = selected_msg
    result["contents_source"]  = selected_src

    # ── 자동 생성 컬럼 ────────────────────────────────────────────────────
    result["braze_campaign_name"] = build_braze_campaign_name(
        send_dt=result["send_dt"],
        send_time=result["send_time"],
        ad_code=ad_code,
        title=result["title"],
        target=result["target"],
        content_type=result["content_type"],
    )
    result["feed_url"]         = build_feed_url(landing_url, ad_code)
    result["webhook_contents"] = build_webhook_contents(result["contents"] or "")

    # ── 검수 플래그 ──────────────────────────────────────────────────────
    result["error_flag"] = (
        result["contents_v1"] is None or result["contents_v2"] is None
    )
    result["needs_review"] = result["error_flag"] or any([
        (v1["confidence"] or 0) < CONFIDENCE_THRESHOLD,
        (v2["confidence"] or 0) < CONFIDENCE_THRESHOLD,
        (v3["confidence"] or 0) < CONFIDENCE_THRESHOLD,
        result["title_source"] == "fallback",
    ])

    return result, ad_code


_VALID_TARGETS    = {"여성", "남성", "전체"}
_VALID_PRIORITIES = {1, 2, 3}
_VALID_CONTENT_TYPES = {"캠페인", "콘텐츠", "브랜드", None}


def _postprocess_columns(result: dict) -> dict:
    """Pipeline 2 출력 컬럼을 정규화·보정한다.

    각 컬럼의 허용 값 범위를 검증하고, 범위 외 값은 안전한 기본값으로 대체한다.
    title은 sanitize_title을 재확인하여 제어문자가 남아있지 않도록 한다.
    """
    result["title"] = sanitize_title(result.get("title") or "")

    if result.get("send_time") not in ("11:00",):
        result["send_time"] = "11:00"

    if result.get("target") not in _VALID_TARGETS:
        logger.debug(f"target 정규화: {result.get('target')!r} → '전체'")
        result["target"] = "전체"

    try:
        prio = int(result.get("priority", 3))
    except (TypeError, ValueError):
        prio = 3
    if prio not in _VALID_PRIORITIES:
        prio = 3
    result["priority"] = prio

    ct = result.get("content_type")
    if ct not in _VALID_CONTENT_TYPES:
        logger.debug(f"content_type 정규화: {ct!r} → None")
        result["content_type"] = None

    return result


def run_pipeline2(selected_df: pd.DataFrame, brand_df: pd.DataFrame, category_df=None) -> pd.DataFrame:
    logger.info(f"Pipeline 2 시작 — {len(selected_df)}건 처리")

    current_ad_code = _load_last_ad_code()
    rows = []
    total = len(selected_df)

    for i, (_, row) in enumerate(selected_df.iterrows(), 1):
        row_id = row.get("id", f"idx-{i}")
        set_current_row(row_id)
        logger.info(f"[{i}/{total}] id={row_id} 처리 중...")
        try:
            meta, new_ad_code = process_row(row, brand_df, current_ad_code, category_df)
            meta = _postprocess_columns(meta)
            current_ad_code = new_ad_code
            rows.append({**row.to_dict(), **meta})
        except Exception as e:
            logger.error(f"id={row_id} 처리 실패: {e}")
            rows.append({**row.to_dict(), "error_flag": True, "needs_review": True})

    _save_last_ad_code(current_ad_code)

    result_df = pd.DataFrame(rows)

    v1_ok    = result_df["contents_v1"].notna().sum() if "contents_v1" in result_df.columns else 0
    v2_ok    = result_df["contents_v2"].notna().sum() if "contents_v2" in result_df.columns else 0
    errors   = int(result_df.get("error_flag", pd.Series([False] * len(result_df))).sum())
    reviews  = int(result_df.get("needs_review", pd.Series([False] * len(result_df))).sum())

    logger.info(f"V1 생성 완료: {v1_ok}건")
    logger.info(f"V2 생성 완료: {v2_ok}건")
    logger.info(f"오류: {errors}건")
    logger.info(f"검수 필요: {reviews}건")

    return result_df
