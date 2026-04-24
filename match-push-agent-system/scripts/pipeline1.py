"""Pipeline 1 — 소재 선별 로직."""
import logging
from typing import Set, Tuple
import pandas as pd
from config import CAMPAIGN_META_SYNC_PATH, AD_STATUS_COLUMN
from rules import is_cancelled, is_in_send_window, is_already_selected, make_sheet_key, validate_landing_url
from run_logger import (
    REASON_CANCELLED, REASON_ALREADY_SELECTED,
    REASON_ALREADY_PROC, REASON_URL_ALREADY_SENT,
    REASON_CAMPAIGN_META_REGISTERED, REASON_SHEET_DUPLICATE,
    REASON_LANDING_NOT_OPEN, REASON_LANDING_OPEN,
)

logger = logging.getLogger(__name__)


def load_campaign_meta_urls() -> Set[str]:
    """캠페인메타엔진 시트(campaign_meta_sync.csv)에 등록된 landing_url set 로드.

    이 파일이 중복 방지의 유일한 기준이다. processed_urls.csv 등 내부 로그 파일은
    기록 목적으로만 사용하며 선별 판단에 사용하지 않는다.
    """
    try:
        df = pd.read_csv(CAMPAIGN_META_SYNC_PATH, dtype=str)
        urls = set(df["landing_url"].dropna().str.strip().tolist())
        logger.info(f"캠페인메타엔진 동기 URL 로드: {len(urls)}건 ({CAMPAIGN_META_SYNC_PATH})")
        return urls
    except FileNotFoundError:
        logger.info(f"캠페인메타엔진 동기 파일 없음: {CAMPAIGN_META_SYNC_PATH} — 중복 URL 없음으로 처리")
        return set()


def load_sheet_keys(sheet_df: pd.DataFrame, send_dt: str) -> Set[str]:
    if sheet_df is None or sheet_df.empty:
        return set()
    keys = (
        sheet_df.get("landing_url", pd.Series(dtype=str)).fillna("").astype(str)
        + "|"
        + sheet_df.get("brand_id", pd.Series(dtype=str)).fillna("").astype(str)
        + "|"
        + send_dt
    )
    return set(keys.tolist())


def apply_selection(
    df: pd.DataFrame,
    send_dt: str,
    campaign_meta_urls: Set[str],
    sheet_keys: Set[str],
    extra_processed_ids: Set[str] = None,
    extra_processed_urls: Set[str] = None,
) -> pd.DataFrame:
    """각 행에 selected, selection_reason, rejection_reason, rejection_detail 컬럼을 추가.

    중복 판단 우선순위:
      1. 취소 여부
      2. 선정 여부 (광고진행 계열)
      3. 캠페인메타엔진 등록 URL (campaign_meta_sync.csv)
      4. 동일 실행 내 id/URL 중복 (기간·주간 배치 전용)
      5. 시트 기반 당일 중복
      6. 발송 윈도우 (D-1 10:00 ~ D-0 10:00)
      7. 랜딩 URL 유효성
    """
    eff_intra_ids  = extra_processed_ids  or set()
    eff_intra_urls = extra_processed_urls or set()

    results = []

    for _, row in df.iterrows():
        row_id    = str(row.get("id", ""))
        team_name = str(row.get("register_team_name", "") or "")
        remarks   = str(row.get("remarks", "") or "")
        release   = row.get("release_start_date_time")
        brand_id  = str(row.get("sourceBrandId", "") or "")
        url       = str(row.get("landing_url", "") or "").strip()
        ad_status = row.get(AD_STATUS_COLUMN)
        sheet_key = make_sheet_key(url, brand_id, send_dt)

        # 조건 1: 취소 여부
        if is_cancelled(remarks):
            results.append({
                "selected": False,
                "selection_reason": None,
                "rejection_reason": REASON_CANCELLED,
                "rejection_detail": f"remarks={remarks[:80]}",
            })
            continue

        # 조건 2: 선정 여부 = 광고진행 계열
        if is_already_selected(ad_status):
            results.append({
                "selected": False,
                "selection_reason": None,
                "rejection_reason": REASON_ALREADY_SELECTED,
                "rejection_detail": f"ad_status={str(ad_status)[:40]}",
            })
            continue

        # 조건 3: 캠페인메타엔진 등록 URL (유일한 크로스세션 중복 기준)
        if url and url in campaign_meta_urls:
            results.append({
                "selected": False,
                "selection_reason": None,
                "rejection_reason": REASON_CAMPAIGN_META_REGISTERED,
                "rejection_detail": f"url={url[:120]}",
            })
            continue

        # 조건 4-1: 동일 실행 내 id 중복 (기간/주간 배치 전용)
        if row_id in eff_intra_ids:
            results.append({
                "selected": False,
                "selection_reason": None,
                "rejection_reason": REASON_ALREADY_PROC,
                "rejection_detail": f"id={row_id}",
            })
            continue

        # 조건 4-2: 동일 실행 내 URL 중복 (기간/주간 배치 전용)
        if url and url in eff_intra_urls:
            results.append({
                "selected": False,
                "selection_reason": None,
                "rejection_reason": REASON_URL_ALREADY_SENT,
                "rejection_detail": f"url={url[:120]}",
            })
            continue

        # 조건 5: 시트 기반 당일 중복
        if sheet_key in sheet_keys:
            results.append({
                "selected": False,
                "selection_reason": None,
                "rejection_reason": REASON_SHEET_DUPLICATE,
                "rejection_detail": f"key={sheet_key[:120]}",
            })
            continue

        # 조건 6: 발송 윈도우 (D-1 10:00 ~ D-0 10:00)
        if not is_in_send_window(release, send_dt):
            results.append({
                "selected": False,
                "selection_reason": None,
                "rejection_reason": REASON_LANDING_NOT_OPEN,
                "rejection_detail": f"release={str(release)[:30]}",
            })
            continue

        # 조건 7: 랜딩 URL 유효성 검증 (윈도우 통과 후 추가)
        url_reason = validate_landing_url(url)
        if url_reason:
            results.append({
                "selected": False,
                "selection_reason": None,
                "rejection_reason": url_reason,
                "rejection_detail": f"url={url[:120]}",
            })
        else:
            results.append({
                "selected": True,
                "selection_reason": REASON_LANDING_OPEN,
                "rejection_reason": None,
                "rejection_detail": None,
            })

    return pd.concat([df, pd.DataFrame(results, index=df.index)], axis=1)


def run_pipeline1(
    raw_df: pd.DataFrame,
    send_dt: str,
    campaign_meta_urls: Set[str] = None,
    sheet_df: pd.DataFrame = None,
    extra_processed_ids: Set[str] = None,
    extra_processed_urls: Set[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """소재 선별 실행.

    Args:
        campaign_meta_urls:   캠페인메타엔진 시트에 이미 등록된 URL set.
                              None이면 campaign_meta_sync.csv에서 자동 로드.
        extra_processed_ids:  기간/주간 배치 실행 시 이전 날 선별된 id set.
        extra_processed_urls: 기간/주간 배치 실행 시 이전 날 선별된 url set.
    Returns:
        (selected_df, rejected_df)
    """
    logger.info(f"Pipeline 1 시작 — send_dt={send_dt}, 전체={len(raw_df)}건")

    if campaign_meta_urls is None:
        campaign_meta_urls = load_campaign_meta_urls()

    sheet_keys = load_sheet_keys(sheet_df, send_dt)

    result_df = apply_selection(
        raw_df, send_dt, campaign_meta_urls, sheet_keys,
        extra_processed_ids, extra_processed_urls,
    )

    selected_mask = result_df["selected"] == True
    selected_df   = result_df[selected_mask].copy().reset_index(drop=True)
    rejected_df   = result_df[~selected_mask].copy().reset_index(drop=True)

    logger.info(f"선별: {len(selected_df)}건 / 탈락: {len(rejected_df)}건")
    if len(rejected_df):
        reason_counts = rejected_df["rejection_reason"].value_counts()
        for reason, cnt in reason_counts.items():
            logger.info(f"  탈락 사유 [{reason}]: {cnt}건")

    return selected_df, rejected_df
