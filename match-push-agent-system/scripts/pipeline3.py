"""Pipeline 3 — 검수 검증 (Validation QA).

Pipeline 2 결과물에 대해 발송 전 문제가 될 수 있는 항목을 객관적으로 검증한다.
행을 제거하지 않고 이슈를 플래그로 표시하여 담당자가 최종 판단하도록 한다.
"""
import re
import logging
from typing import Optional
import pandas as pd
from config import (
    TITLE_MIN_LEN, TITLE_MAX_LEN, UNSUBSCRIBE_TEXT,
    AD_CODE_PREFIX, CONFIDENCE_THRESHOLD,
    CONTENTS_V1_MIN_LEN, CONTENTS_V1_MAX_LEN,
    CONTENTS_V2_MIN_LEN, CONTENTS_V2_MAX_LEN,
    CONTENTS_V3_MIN_LEN, CONTENTS_V3_MAX_LEN,
)
from rules import lookup_brand_names

logger = logging.getLogger(__name__)


def _check_row(row: pd.Series, seen_ad_codes: set, brand_df: Optional[pd.DataFrame] = None) -> tuple:
    """단일 행에 대해 검증 이슈 목록과 brand_nm_verified를 반환한다."""
    issues = []

    title       = str(row.get("title", "") or "")
    contents    = str(row.get("contents", "") or "")
    contents_v1 = str(row.get("contents_v1", "") or "")
    contents_v2 = str(row.get("contents_v2", "") or "")
    contents_v3 = str(row.get("contents_v3", "") or "")
    land_url    = str(row.get("landing_url", "") or "")
    push_url    = str(row.get("push_url", "") or "")
    ad_code     = str(row.get("ad_code", "") or "")
    brand_id    = str(row.get("brand_id", "") or "")
    conf_v1     = row.get("confidence_v1")
    conf_v2     = row.get("confidence_v2")
    brand_nm_verified = ""

    # ── 1. 필수 필드 누락 ────────────────────────────────────────────────
    if not title:
        issues.append("title_missing")
    if not contents_v1:
        issues.append("contents_v1_missing")
    if not contents_v2:
        issues.append("contents_v2_missing")
    if not contents_v3:
        issues.append("contents_v3_missing")
    if not contents:
        issues.append("contents_missing")
    if not land_url:
        issues.append("landing_url_missing")
    if not ad_code:
        issues.append("ad_code_missing")

    # ── 2. title 길이 범위 ───────────────────────────────────────────────
    if title and not (TITLE_MIN_LEN <= len(title) <= TITLE_MAX_LEN):
        issues.append(f"title_length_{len(title)}chars(expected {TITLE_MIN_LEN}-{TITLE_MAX_LEN})")

    # ── 2b. 본문 길이 범위 (수신거부·접두어 제외 순수 본문 기준) ─────────
    def _body_len(text: str) -> int:
        return len(text.replace("(광고) ", "", 1).split(UNSUBSCRIBE_TEXT)[0].strip())

    if contents_v1:
        bl = _body_len(contents_v1)
        if not (CONTENTS_V1_MIN_LEN <= bl <= CONTENTS_V1_MAX_LEN):
            issues.append(f"v1_length_{bl}chars(expected {CONTENTS_V1_MIN_LEN}-{CONTENTS_V1_MAX_LEN})")
    if contents_v2:
        bl = _body_len(contents_v2)
        if not (CONTENTS_V2_MIN_LEN <= bl <= CONTENTS_V2_MAX_LEN):
            issues.append(f"v2_length_{bl}chars(expected {CONTENTS_V2_MIN_LEN}-{CONTENTS_V2_MAX_LEN})")
    if contents_v3:
        bl = _body_len(contents_v3)
        if not (CONTENTS_V3_MIN_LEN <= bl <= CONTENTS_V3_MAX_LEN):
            issues.append(f"v3_length_{bl}chars(expected {CONTENTS_V3_MIN_LEN}-{CONTENTS_V3_MAX_LEN})")

    # ── 3. (광고) 접두어 — contents, V1, V2, V3 각각 검사 ──────────────
    if contents and not contents.startswith("(광고)"):
        issues.append("missing_(광고)_prefix")
    if contents_v1 and not contents_v1.startswith("(광고)"):
        issues.append("missing_(광고)_prefix_v1")
    if contents_v2 and not contents_v2.startswith("(광고)"):
        issues.append("missing_(광고)_prefix_v2")
    if contents_v3 and not contents_v3.startswith("(광고)"):
        issues.append("missing_(광고)_prefix_v3")

    # ── 4. 수신거부 문구 — contents, V1, V2, V3 각각 검사 ──────────────
    if contents and UNSUBSCRIBE_TEXT not in contents:
        issues.append("missing_unsubscribe_text")
    if contents_v1 and UNSUBSCRIBE_TEXT not in contents_v1:
        issues.append("missing_unsubscribe_text_v1")
    if contents_v2 and UNSUBSCRIBE_TEXT not in contents_v2:
        issues.append("missing_unsubscribe_text_v2")
    if contents_v3 and UNSUBSCRIBE_TEXT not in contents_v3:
        issues.append("missing_unsubscribe_text_v3")

    # ── 5. push_url UTM 파라미터 ─────────────────────────────────────────
    if push_url and "utm_source" not in push_url:
        issues.append("push_url_missing_utm")
    if push_url and f"utm_campaign={ad_code}" not in push_url:
        issues.append("push_url_campaign_mismatch")

    # ── 6. 할인율 0% 차단 — V1, V2, V3 각각 검사 ───────────────────────
    if contents_v1 and re.search(r'\b0\s*%', contents_v1):
        issues.append("zero_percent_in_v1")
    if contents_v2 and re.search(r'\b0\s*%', contents_v2):
        issues.append("zero_percent_in_v2")
    if contents_v3 and re.search(r'\b0\s*%', contents_v3):
        issues.append("zero_percent_in_v3")

    # ── 7. landing_url https 형식 ────────────────────────────────────────
    if land_url and not land_url.startswith("https://"):
        issues.append("landing_url_not_https")

    # ── 8. ad_code 중복 ─────────────────────────────────────────────────
    if ad_code:
        if ad_code in seen_ad_codes:
            issues.append("ad_code_duplicate")
        else:
            seen_ad_codes.add(ad_code)

    # ── 9. brand_id 누락 + brand_nm_verified 수집 ────────────────────────
    if not brand_id:
        issues.append("brand_id_missing")
    elif brand_df is not None and not brand_df.empty:
        brand_nm_kr, _ = lookup_brand_names(brand_id, brand_df)
        brand_nm_verified = brand_nm_kr or brand_id

    # ── 10. LLM confidence 임계값 미달 ──────────────────────────────────
    try:
        if conf_v1 is not None and float(conf_v1) < CONFIDENCE_THRESHOLD:
            issues.append(f"low_confidence_v1({conf_v1})")
    except (ValueError, TypeError):
        pass
    try:
        if conf_v2 is not None and float(conf_v2) < CONFIDENCE_THRESHOLD:
            issues.append(f"low_confidence_v2({conf_v2})")
    except (ValueError, TypeError):
        pass

    # ── 11. title_source fallback ────────────────────────────────────────
    if str(row.get("title_source", "")) == "fallback":
        issues.append("title_source_fallback")

    # ── 12. 브랜드명 포함 여부 (V1·V2 합산 텍스트 기준) ─────────────────
    if brand_df is not None and not brand_df.empty and brand_id:
        brand_nm_kr, brand_nm_en = lookup_brand_names(brand_id, brand_df)
        if brand_nm_kr or brand_nm_en:
            search_text = (title + " " + contents_v1 + " " + contents_v2 + " " + contents_v3).lower()
            found_kr = bool(brand_nm_kr) and brand_nm_kr.lower() in search_text
            found_en = bool(brand_nm_en) and brand_nm_en.lower() in search_text
            if not (found_kr or found_en):
                issues.append(f"brand_name_not_in_message({brand_nm_kr or brand_nm_en})")

    # ── 13. 캠페인 소재 category_id 필수 ────────────────────────────────
    content_type = str(row.get("content_type", "") or "")
    category_id  = str(row.get("category_id",  "") or "")
    if content_type == "캠페인" and not category_id:
        issues.append("campaign_category_id_missing")

    return issues, brand_nm_verified


def run_pipeline3(result_df: pd.DataFrame, brand_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Pipeline 3 검수 검증 실행.

    Args:
        result_df: Pipeline 2 결과 DataFrame
        brand_df: 브랜드 목록 DataFrame (브랜드명 포함 여부 검증용)

    Returns:
        validation_notes, needs_review, error_flag 컬럼이 갱신된 DataFrame
    """
    logger.info(f"Pipeline 3 시작 — {len(result_df)}건 검증")

    seen_ad_codes: set = set()
    all_notes      = []
    all_needs      = []
    all_errors     = []
    all_brand_nms  = []

    BLOCKING_SUFFIXES = ("_missing",)

    for _, row in result_df.iterrows():
        issues, brand_nm_verified = _check_row(row, seen_ad_codes, brand_df)

        notes  = ", ".join(issues) if issues else ""
        is_blocking = any(
            any(issue.endswith(s) for s in BLOCKING_SUFFIXES)
            for issue in issues
        )

        # Pipeline 2 플래그 유지 (OR 합산)
        prev_error  = bool(row.get("error_flag",   False))
        prev_review = bool(row.get("needs_review", False))

        all_notes.append(notes)
        all_errors.append(is_blocking or prev_error)
        all_needs.append(bool(issues) or prev_review)
        all_brand_nms.append(brand_nm_verified)

    df = result_df.copy()
    df["validation_notes"]  = all_notes
    df["error_flag"]        = all_errors
    df["needs_review"]      = all_needs
    df["brand_nm_verified"] = all_brand_nms

    pass_cnt  = sum(1 for n in all_notes if not n)
    issue_cnt = sum(1 for n in all_notes if n)
    block_cnt = sum(1 for e in all_errors if e)

    logger.info(f"검증 통과: {pass_cnt}건")
    logger.info(f"이슈 발견: {issue_cnt}건 (blocking: {block_cnt}건)")

    return df
