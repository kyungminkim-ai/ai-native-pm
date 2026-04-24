#!/usr/bin/env python3
"""
메인 실행 스크립트 — 소재 선별 + 메시지 생성 + 검수 검증 + 캠페인메타엔진 시트 출력.

사용법:
    python3 scripts/run.py --date 2026-05-01
    python3 scripts/run.py --date 2026-05-01 --input input/my_raw.csv
    python3 scripts/run.py --stage pipeline1 --date 2026-05-01
    python3 scripts/run.py --stage pipeline2 --date 2026-05-01
"""
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# 스크립트 디렉터리를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    BIZEST_RAW_PATH, BRAND_LIST_PATH, CATEGORY_SEL_PATH, OUTPUT_DIR, DATA_DIR,
    LLM_API_AVAILABLE, get_pending_jobs_path, get_responses_path,
    PROCESSED_URLS_PATH, AD_STATUS_COLUMN,
)
from pipeline1 import load_campaign_meta_urls
import llm_client
from pipeline1 import run_pipeline1
from pipeline2 import run_pipeline2
from pipeline3 import run_pipeline3
from pipeline4 import run_pipeline4
from rules import is_title_valid, lookup_brand_name
from run_logger import RunLogger, URL_REJECTION_CODES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# 캠페인메타엔진 운영 시트 컬럼 순서 (target CSV와 동일)
OUTPUT_COLUMNS = [
    "send_dt", "send_time", "target", "priority", "ad_code",
    "content_type", "goods_id", "category_id", "brand_id", "team_id",
    "braze_campaign_name", "title", "contents", "landing_url", "image_url",
    "push_url", "feed_url", "webhook_contents", "stopped",
    # 검수용 컬럼 (담당자 검토용 — Braze 등록 시 제외)
    "[검수용] contents_v1_benefit", "[검수용] contents_v2_brand", "[검수용] contents_v3_scarcity",
    "[검수용] contents_source",
    "[검수용] brand_nm_verified",
    "[검수용] title_source", "[검수용] confidence_v1",
    "[검수용] confidence_v2", "[검수용] confidence_v3",
    "[검수용] error_flag", "[검수용] needs_review",
    "[검수용] validation_notes",
    "[검수용] review_score", "[검수용] review_verdict",
    "[검수용] review_notes", "[검수용] review_issues",
]

# pending_jobs JSON에 포함되는 LLM 작업 지침 (단일 날짜 & 범위 공통)
_PENDING_JOBS_MESSAGE_RULES = {
    "title":    "15~40자, 명사형 종결, 브랜드명+혜택 포함",
    "v1":       "(광고) 시작, 40~60자, 혜택 수치 강조, 명사형 종결",
    "v2":       "(광고) 시작, 25~45자, 브랜드 감성 표현, 수치 최소화",
    "v3":       "(광고) 시작, 30~50자, 희소성·긴급성 강조 (마감/한정수량/선착순 등), 수치 나열 금지",
    "review":   "score 1-5, verdict: pass≥3.5/warning 2.5-3.4/fail≤2.4",
    "category_codes": "소재 내용 기반 카테고리 코드 최대 3개 (없으면 빈 리스트)",
}

def _build_pending_instructions(response_filename: str) -> str:
    return (
        "각 job에 대해 title/contents_v1/contents_v2/contents_v3/review/category_codes를 생성하고 "
        f"{response_filename}으로 저장하세요. "
        "수신거부 문구는 포함하지 마세요 (Python이 별도 추가). "
        "응답 형식: {\"<id>\": {\"title\": ..., \"title_source\": \"llm\"|\"original\", "
        "\"contents\": \"(광고) ...\", \"confidence_v1\": 4.0, "
        "\"contents_v2\": \"(광고) ...\", \"confidence_v2\": 4.0, "
        "\"contents_v3\": \"(광고) ...\", \"confidence_v3\": 4.0, "
        "\"review_score\": 4.0, \"review_verdict\": \"pass\"|\"warning\"|\"fail\", "
        "\"review_notes\": \"\", \"review_issues\": [], "
        "\"category_codes\": [\"코드1\", \"코드2\"]}}"
    )


def _load_bizest_raw(path: Path) -> pd.DataFrame:
    """비제스트 RAW CSV 로드 — 2행 헤더(한국어+영문) 자동 감지.
    'Unnamed: 0' (한국어: 선정 여부) → AD_STATUS_COLUMN 으로 리네임.
    """
    df = pd.read_csv(path, dtype=str, nrows=2)
    if "id" not in df.columns and any(str(v) == "id" for v in df.iloc[0].values):
        df = pd.read_csv(path, header=1, dtype=str)
    else:
        df = pd.read_csv(path, dtype=str)
    if "id" in df.columns:
        df["id"] = df["id"].astype(str)
    # 선정 여부 컬럼 이름 정규화
    if "Unnamed: 0" in df.columns:
        df = df.rename(columns={"Unnamed: 0": AD_STATUS_COLUMN})
    return df


def load_inputs(raw_path: Path, brand_path: Path):
    if not raw_path.exists():
        logger.error(f"비제스트 RAW 파일 없음: {raw_path}")
        sys.exit(1)

    raw_df = _load_bizest_raw(raw_path)
    logger.info(f"비제스트 RAW 로드: {len(raw_df)}건 ({raw_path})")

    brand_df = pd.DataFrame()
    if brand_path.exists():
        brand_df = pd.read_csv(brand_path, dtype={"brand_id": str})
        logger.info(f"브랜드 목록 로드: {len(brand_df)}건")
    else:
        logger.warning(f"브랜드 목록 없음: {brand_path} — 브랜드명 ID로 대체")

    category_df = pd.DataFrame()
    if CATEGORY_SEL_PATH.exists():
        try:
            category_df = pd.read_csv(CATEGORY_SEL_PATH, header=1, dtype=str)
            category_df = category_df.dropna(subset=["구분", "코드"])
            logger.info(f"카테고리 목록 로드: {len(category_df)}건")
        except Exception as e:
            logger.warning(f"카테고리 목록 로드 실패: {e}")
    else:
        logger.warning(f"카테고리 목록 없음: {CATEGORY_SEL_PATH}")

    return raw_df, brand_df, category_df


def save_pipeline1(selected_df: pd.DataFrame, send_dt: str):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"pipeline1_output_{send_dt.replace('-', '')}.csv"
    selected_df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"Pipeline 1 출력 저장: {path}")
    return path


# 선별 리포트에 포함할 컬럼 (선별/탈락 모두)
_SELECTION_REPORT_COLS = [
    "send_dt", AD_STATUS_COLUMN, "id", "register_team_name", "sourceBrandId",
    "main_title", "landing_url", "release_start_date_time",
    "requested_start_date_time", "remarks",
    "selected", "selection_reason", "rejection_reason", "rejection_detail",
]

# 주단위 통합 후보군 리포트 컬럼 (윈도우 통과 전체, send_dt → 발송예정일)
_WEEKLY_REPORT_COLS = [
    "발송예정일", "id", "register_team_name", "sourceBrandId",
    "main_title", "landing_url", "release_start_date_time",
    "selected", "selection_reason", "rejection_reason", "rejection_detail",
]


def save_selection_report(
    selected_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
    send_dt: str,
) -> Path:
    """선별+윈도우탈락+URL탈락 전체를 output/selection_report_{date}.csv 로 저장.

    정렬: 통과(selected=True) → URL탈락(URL_REJECTION_CODES) → 기타 탈락
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _sort_key(row):
        if row.get("selected"):
            return 0
        if row.get("rejection_reason") in URL_REJECTION_CODES:
            return 1
        return 2

    combined = pd.concat([selected_df, rejected_df], ignore_index=True)
    combined["_sort"] = combined.apply(_sort_key, axis=1)
    combined = combined.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)

    cols = [c for c in _SELECTION_REPORT_COLS if c in combined.columns]
    path = OUTPUT_DIR / f"selection_report_{send_dt.replace('-', '')}.csv"
    combined[cols].to_csv(path, index=False, encoding="utf-8-sig")

    n_url = int(
        rejected_df["rejection_reason"].isin(URL_REJECTION_CODES).sum()
    ) if not rejected_df.empty and "rejection_reason" in rejected_df.columns else 0
    logger.info(
        f"선별 리포트 저장: {path} "
        f"(통과={len(selected_df)}, URL탈락={n_url}, 기타탈락={len(rejected_df)-n_url})"
    )
    return path


def save_weekly_report(all_candidates: list, week_start: str) -> Path:
    """주단위 후보군 리포트 — 발송 윈도우 통과 전체 (통과+URL탈락), 날짜 순 정렬."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not all_candidates:
        logger.warning("주단위 선별: 후보군 0건")
        return None

    merged = pd.concat(all_candidates, ignore_index=True)
    merged = merged.rename(columns={"send_dt": "발송예정일"})
    merged = merged.sort_values(["발송예정일", "selected"], ascending=[True, False]).reset_index(drop=True)

    cols = [c for c in _WEEKLY_REPORT_COLS if c in merged.columns]
    path = OUTPUT_DIR / f"selection_report_week_{week_start.replace('-', '')}.csv"
    merged[cols].to_csv(path, index=False, encoding="utf-8-sig")

    n_pass = int(merged["selected"].sum()) if "selected" in merged.columns else 0
    n_fail = len(merged) - n_pass
    logger.info(f"주단위 후보군 리포트 저장: {path} (통과={n_pass}건, URL탈락={n_fail}건)")
    return path


def run_weekly(week_dates: list, raw_path: Path, brand_path: Path) -> None:
    """주단위 소재 선별 — 날짜간 중복 제거 후 통합 후보군 리포트 생성."""
    raw_df_base, _, _ = load_inputs(raw_path, brand_path)
    week_start = week_dates[0]

    campaign_meta_urls = load_campaign_meta_urls()

    all_candidates = []       # 윈도우 통과 전체 (통과 + URL탈락)
    week_selected_ids:  set = set()
    week_selected_urls: set = set()

    print(f"\n{'='*60}")
    print(f"[주단위 선별] {week_dates[0]} ~ {week_dates[-1]}")
    print(f"{'='*60}\n")

    for send_dt in week_dates:
        raw_df = raw_df_base.copy()
        raw_df["send_dt"] = send_dt

        selected_df, rejected_df = run_pipeline1(
            raw_df, send_dt,
            campaign_meta_urls=campaign_meta_urls,
            extra_processed_ids=week_selected_ids,
            extra_processed_urls=week_selected_urls,
        )

        # URL 검증 탈락 항목 (윈도우 통과했으나 URL 문제)
        url_rejected_df = rejected_df[
            rejected_df["rejection_reason"].isin(URL_REJECTION_CODES)
        ].copy() if not rejected_df.empty and "rejection_reason" in rejected_df.columns else pd.DataFrame()

        n_pass = len(selected_df)
        n_url  = len(url_rejected_df)
        day_name = ["월", "화", "수", "목", "금", "토", "일"][
            datetime.strptime(send_dt, "%Y-%m-%d").weekday()
        ]
        print(f"  {send_dt} ({day_name}) → 통과 {n_pass}건 / URL탈락 {n_url}건")

        if n_pass:
            for _, r in selected_df.iterrows():
                print(f"    ✅ {r.get('register_team_name','')} | {str(r.get('main_title',''))[:30]}")
            ids  = selected_df["id"].dropna().astype(str).tolist()
            urls = selected_df["landing_url"].dropna().str.strip().tolist()
            week_selected_ids  |= set(ids)
            week_selected_urls |= set(u for u in urls if u)

        if n_url:
            for _, r in url_rejected_df.iterrows():
                print(f"    ❌ [{r.get('rejection_reason','')}] {r.get('register_team_name','')} | {str(r.get('main_title',''))[:30]}")

        # 후보군 수집 (통과 + URL탈락)
        day_candidates = []
        if n_pass:
            day_candidates.append(selected_df)
        if n_url:
            day_candidates.append(url_rejected_df)
        if day_candidates:
            all_candidates.append(pd.concat(day_candidates, ignore_index=True))

    weekly_path = save_weekly_report(all_candidates, week_start)

    total_pass  = sum(
        int(df["selected"].sum()) for df in all_candidates
        if "selected" in df.columns
    )
    total_total = sum(len(df) for df in all_candidates)
    print(f"\n{'='*60}")
    print(f"총 후보군: {total_total}건 (통과={total_pass}건 / URL탈락={total_total - total_pass}건)")
    if weekly_path:
        print(f"📁 통합 리포트: {weekly_path}")
    print(f"{'='*60}\n")


def save_processed_urls(selected_df: pd.DataFrame, send_dt: str) -> None:
    """완료된 소재의 landing_url을 processed_urls.csv에 누적 저장."""
    if "landing_url" not in selected_df.columns:
        return
    urls = selected_df["landing_url"].dropna().str.strip()
    urls = urls[urls != ""].unique()
    if len(urls) == 0:
        return

    now = datetime.now().isoformat()
    new_rows = pd.DataFrame({
        "landing_url": urls,
        "send_dt":     send_dt,
        "processed_at": now,
    })

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if PROCESSED_URLS_PATH.exists():
        existing = pd.read_csv(PROCESSED_URLS_PATH, dtype=str)
        combined = pd.concat([existing, new_rows], ignore_index=True)
        combined = combined.drop_duplicates(subset=["landing_url"], keep="first")
    else:
        combined = new_rows

    combined.to_csv(PROCESSED_URLS_PATH, index=False, encoding="utf-8-sig")
    logger.info(f"processed_urls 갱신: {len(urls)}건 추가 → 누적 {len(combined)}건")


def save_final(result_df: pd.DataFrame, send_dt: str):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now().strftime("%H%M%S")
    date = send_dt.replace("-", "")
    path = OUTPUT_DIR / f"campaign_meta_{date}_{ts}.csv"

    rename_map = {
        "contents_v1":       "[검수용] contents_v1_benefit",
        "contents_v2":       "[검수용] contents_v2_brand",
        "contents_v3":       "[검수용] contents_v3_scarcity",
        "contents_source":   "[검수용] contents_source",
        "brand_nm_verified": "[검수용] brand_nm_verified",
        "title_source":      "[검수용] title_source",
        "confidence_v1":     "[검수용] confidence_v1",
        "confidence_v2":     "[검수용] confidence_v2",
        "confidence_v3":     "[검수용] confidence_v3",
        "error_flag":        "[검수용] error_flag",
        "needs_review":      "[검수용] needs_review",
        "validation_notes":  "[검수용] validation_notes",
        "review_score":      "[검수용] review_score",
        "review_verdict":    "[검수용] review_verdict",
        "review_notes":      "[검수용] review_notes",
        "review_issues":     "[검수용] review_issues",
    }
    result_df = result_df.rename(columns=rename_map)

    for col in OUTPUT_COLUMNS:
        if col not in result_df.columns:
            result_df[col] = ""

    result_df[OUTPUT_COLUMNS].to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"최종 산출물 저장: {path}")
    return path


def generate_pending_jobs(selected_df: pd.DataFrame, brand_df: pd.DataFrame, send_dt: str) -> Path:
    """API 키 없을 때 Claude Code가 처리할 LLM 작업 목록을 JSON으로 생성."""
    jobs = []
    for _, row in selected_df.iterrows():
        brand_id = str(row.get("sourceBrandId", "") or "")
        brand    = lookup_brand_name(brand_id, brand_df)
        orig_title = str(row.get("main_title", "") or "")
        remarks_raw = str(row.get("remarks", "") or "")
        jobs.append({
            "id":                str(row.get("id", "")),
            "brand":             brand,
            "promotion_content": str(row.get("promotion_content", "") or ""),
            "target":            str(row.get("register_team_name", "") or ""),
            "content_type":      str(row.get("landing_url", "") or ""),
            "original_title":    orig_title,
            "needs_title_regen": not is_title_valid(orig_title),
            "remarks":           remarks_raw,
        })

    response_filename = f"llm_responses_{send_dt.replace('-', '')}.json"
    payload = {
        "send_dt":   send_dt,
        "total":     len(jobs),
        "generated_at": datetime.now().isoformat(),
        "instructions": _build_pending_instructions(response_filename),
        "message_rules": _PENDING_JOBS_MESSAGE_RULES,
        "jobs": jobs,
    }

    jobs_path = get_pending_jobs_path(send_dt)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(jobs_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info(f"Pending jobs 저장: {jobs_path} ({len(jobs)}건)")
    return jobs_path


def print_summary(result_df: pd.DataFrame, send_dt: str, output_path: Path,
                  selection_report_path: Path = None):
    total   = len(result_df)
    v1_ok   = result_df["contents"].notna().sum() if "contents" in result_df.columns else 0
    errors  = int(result_df.get("[검수용] error_flag", result_df.get("error_flag", pd.Series([False]*total))).sum())
    reviews = int(result_df.get("[검수용] needs_review", result_df.get("needs_review", pd.Series([False]*total))).sum())

    needs_review_ids = []
    flag_col = "[검수용] needs_review" if "[검수용] needs_review" in result_df.columns else "needs_review"
    if flag_col in result_df.columns:
        needs_review_ids = result_df[result_df[flag_col] == True]["id"].tolist()

    print("\n" + "="*60)
    print(f"[push-campaign 완료] send_dt={send_dt}")
    print("="*60)
    print(f"\n📊 처리 결과:")
    print(f"  선별 소재:      {total}건")
    print(f"  LLM 생성 성공: {v1_ok}건")
    print(f"  오류:          {errors}건")
    print(f"  검수 필요:     {reviews}건")
    print(f"\n📁 산출물:")
    print(f"  캠페인 메타:  {output_path}")
    if selection_report_path:
        print(f"  선별 리포트:  {selection_report_path}")
    if needs_review_ids:
        print(f"\n⚠️  검수 필요 항목 (id): {needs_review_ids[:10]}")
        if len(needs_review_ids) > 10:
            print(f"   ... 외 {len(needs_review_ids)-10}건")
    print("="*60 + "\n")


def _dates_in_range(date_from: str, date_to: str) -> list:
    """date_from ~ date_to 사이 날짜 목록 반환 (양 끝 포함)."""
    d_from = datetime.strptime(date_from, "%Y-%m-%d")
    d_to   = datetime.strptime(date_to,   "%Y-%m-%d")
    n_days = (d_to - d_from).days + 1
    if n_days <= 0:
        raise ValueError(f"--from({date_from}) 이 --to({date_to}) 보다 늦습니다.")
    return [(d_from + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n_days)]


def save_final_range(result_df: pd.DataFrame, date_from: str, date_to: str) -> Path:
    """기간 범위 통합 캠페인 메타 저장 — send_dt 컬럼으로 날짜 구분."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts    = datetime.now().strftime("%H%M%S")
    d_f   = date_from.replace("-", "")
    d_t   = date_to.replace("-", "")
    path  = OUTPUT_DIR / f"campaign_meta_{d_f}_{d_t}_{ts}.csv"

    rename_map = {
        "contents_v1":       "[검수용] contents_v1_benefit",
        "contents_v2":       "[검수용] contents_v2_brand",
        "contents_v3":       "[검수용] contents_v3_scarcity",
        "contents_source":   "[검수용] contents_source",
        "brand_nm_verified": "[검수용] brand_nm_verified",
        "title_source":      "[검수용] title_source",
        "confidence_v1":     "[검수용] confidence_v1",
        "confidence_v2":     "[검수용] confidence_v2",
        "confidence_v3":     "[검수용] confidence_v3",
        "error_flag":        "[검수용] error_flag",
        "needs_review":      "[검수용] needs_review",
        "validation_notes":  "[검수용] validation_notes",
        "review_score":      "[검수용] review_score",
        "review_verdict":    "[검수용] review_verdict",
        "review_notes":      "[검수용] review_notes",
        "review_issues":     "[검수용] review_issues",
    }
    out = result_df.rename(columns=rename_map)

    for col in OUTPUT_COLUMNS:
        if col not in out.columns:
            out[col] = ""

    out = out.sort_values("send_dt").reset_index(drop=True)
    out[OUTPUT_COLUMNS].to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"기간 범위 통합 산출물 저장: {path} ({len(out)}건)")
    return path


def run_range(
    date_from: str,
    date_to: str,
    raw_path: Path,
    brand_path: Path,
) -> None:
    """기간 범위 전체 파이프라인 실행 — P1(날짜별 선별+중복제거) → P2~P4(통합) → 단일 파일 출력."""
    dates = _dates_in_range(date_from, date_to)
    raw_df_base, brand_df, category_df = load_inputs(raw_path, brand_path)

    campaign_meta_urls = load_campaign_meta_urls()

    all_selected:   list = []
    all_rejected:   list = []
    range_ids:      set  = set()
    range_urls:     set  = set()

    print(f"\n{'='*60}")
    print(f"[기간 범위 선별] {date_from} ~ {date_to} ({len(dates)}일)")
    print(f"{'='*60}\n")

    # ── Phase 1: 날짜별 Pipeline 1 ──────────────────────────────────────
    run_log = RunLogger(send_dt=f"{date_from}~{date_to}", input_file=str(raw_path))

    for send_dt in dates:
        raw_df = raw_df_base.copy()
        raw_df["send_dt"] = send_dt

        selected_df, rejected_df = run_pipeline1(
            raw_df, send_dt,
            campaign_meta_urls=campaign_meta_urls,
            extra_processed_ids=range_ids,
            extra_processed_urls=range_urls,
        )

        day_name = ["월", "화", "수", "목", "금", "토", "일"][
            datetime.strptime(send_dt, "%Y-%m-%d").weekday()
        ]
        print(f"  {send_dt} ({day_name}) → 통과 {len(selected_df)}건 / 탈락 {len(rejected_df)}건")

        if len(selected_df):
            range_ids  |= set(selected_df["id"].dropna().astype(str))
            range_urls |= set(
                u for u in selected_df["landing_url"].dropna().str.strip() if u
            )
            all_selected.append(selected_df)
        all_rejected.append(rejected_df)

    if not all_selected:
        print("\n⚠️  선별된 소재 0건 — 처리 종료")
        return

    combined_selected = pd.concat(all_selected, ignore_index=True)
    combined_rejected = pd.concat(all_rejected, ignore_index=True)
    run_log.record_pipeline1(combined_selected, combined_rejected)

    # 날짜별 선별 리포트 저장 (기간 후보군 통합)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    d_f = date_from.replace("-", "")
    d_t = date_to.replace("-", "")
    # URL 탈락 항목도 포함한 후보군 리포트
    url_rejected = combined_rejected[
        combined_rejected["rejection_reason"].isin(URL_REJECTION_CODES)
    ] if "rejection_reason" in combined_rejected.columns else pd.DataFrame()
    candidate_df = pd.concat([combined_selected, url_rejected], ignore_index=True)
    if not candidate_df.empty:
        candidate_df = candidate_df.rename(columns={"send_dt": "발송예정일"})
        candidate_cols = [c for c in _WEEKLY_REPORT_COLS if c in candidate_df.columns]
        cand_path = OUTPUT_DIR / f"selection_report_{d_f}_{d_t}.csv"
        candidate_df.sort_values(["발송예정일", "selected"], ascending=[True, False]).reset_index(drop=True)[candidate_cols].to_csv(cand_path, index=False, encoding="utf-8-sig")
        logger.info(f"기간 범위 후보군 리포트: {cand_path}")

    total_selected = len(combined_selected)
    print(f"\n  → 총 통과: {total_selected}건 ({date_from}~{date_to})")

    # ── Phase 2: API 키 없을 때 응답 파일 자동 탐지 → 없으면 pending_jobs 생성 ──
    if not LLM_API_AVAILABLE and llm_client._file_responses is None:
        responses_path = get_responses_path(f"{d_f}_{d_t}")
        if responses_path.exists():
            with open(responses_path, encoding="utf-8") as f:
                llm_client.init_file_mode(json.load(f))
            logger.info(f"Claude Code 모드 — 범위 응답 파일 로드: {responses_path}")

    if not LLM_API_AVAILABLE and llm_client._file_responses is None:
        # 응답 파일 없음 → pending_jobs 생성 후 중단
        range_key = f"{d_f}_{d_t}"
        jobs_path = get_pending_jobs_path(range_key)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        jobs = []
        for _, row in combined_selected.iterrows():
            brand_id = str(row.get("sourceBrandId", "") or "")
            brand    = lookup_brand_name(brand_id, brand_df)
            orig_title = str(row.get("main_title", "") or "")
            remarks_raw = str(row.get("remarks", "") or "")
            jobs.append({
                "id":                str(row.get("id", "")),
                "send_dt":           str(row.get("send_dt", "")),
                "brand":             brand,
                "promotion_content": str(row.get("promotion_content", "") or ""),
                "target":            str(row.get("register_team_name", "") or ""),
                "content_type":      str(row.get("landing_url", "") or ""),
                "original_title":    orig_title,
                "needs_title_regen": not is_title_valid(orig_title),
                "remarks":           remarks_raw,
            })
        response_filename = f"llm_responses_{range_key}.json"
        payload = {
            "date_from": date_from, "date_to": date_to,
            "total": len(jobs),
            "generated_at": datetime.now().isoformat(),
            "instructions": _build_pending_instructions(response_filename),
            "message_rules": _PENDING_JOBS_MESSAGE_RULES,
            "jobs": jobs,
        }
        with open(jobs_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        responses_path = get_responses_path(range_key)
        print("\n" + "="*60)
        print("⚠️  ANTHROPIC_API_KEY 미설정 — Claude Code 모드")
        print(f"📋 Pending jobs: {jobs_path}")
        print(f"응답 저장 위치: {responses_path}")
        print(f"완료 후 재실행: python3 scripts/run.py --from {date_from} --to {date_to}")
        print("="*60 + "\n")
        return

    # ── Phase 3: Pipeline 2~4 통합 실행 ────────────────────────────────
    result_df = run_pipeline2(combined_selected, brand_df, category_df)
    run_log.record_pipeline2(result_df)

    result_df = run_pipeline3(result_df, brand_df)
    run_log.record_pipeline3(result_df)

    result_df = run_pipeline4(result_df, brand_df)
    run_log.record_pipeline4(result_df)

    output_path = save_final_range(result_df, date_from, date_to)
    save_processed_urls(result_df, date_from)

    log_path = run_log.finalize(str(output_path))

    # 결과 요약
    contents_ok = result_df["contents"].notna().sum() if "contents" in result_df.columns else 0
    reviews  = int(result_df.get("needs_review", pd.Series([False]*len(result_df))).sum())
    needs_review_ids = (
        result_df[result_df["needs_review"] == True]["id"].tolist()
        if "needs_review" in result_df.columns else []
    )

    print(f"\n{'='*60}")
    print(f"[push-campaign 완료] {date_from} ~ {date_to}")
    print(f"{'='*60}")
    print(f"\n📊 처리 결과:")
    print(f"  총 선별:        {total_selected}건")
    print(f"  LLM 생성 성공: {contents_ok}건")
    print(f"  검수 필요:     {reviews}건")
    print(f"\n📁 산출물:")
    print(f"  캠페인 메타:  {output_path}")
    if not candidate_df.empty:
        print(f"  후보군 리포트: {cand_path}")
    if needs_review_ids:
        print(f"\n⚠️  검수 필요 항목 (id): {needs_review_ids[:10]}")
    print(f"{'='*60}\n")

    run_log.print_log_summary(log_path)


def _next_monday() -> str:
    """다음 주 월요일 날짜 반환 (YYYY-MM-DD)."""
    today = datetime.now().date()
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def _week_dates(anchor: str) -> list:
    """anchor 날짜가 속한 주의 월~일 7일 날짜 목록 반환."""
    dt = datetime.strptime(anchor, "%Y-%m-%d")
    monday = dt - timedelta(days=dt.weekday())
    return [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]


def main():
    parser = argparse.ArgumentParser(description="앱푸시 캠페인 소재 선별 & 메시지 생성")
    parser.add_argument("--date",  type=str, help="발송일 YYYY-MM-DD (기본: 내일)")
    parser.add_argument("--from",  dest="date_from", type=str, metavar="YYYY-MM-DD",
                        help="기간 시작 발송일 (--to와 함께 사용)")
    parser.add_argument("--to",    dest="date_to",   type=str, metavar="YYYY-MM-DD",
                        help="기간 종료 발송일 (--from과 함께 사용)")
    parser.add_argument("--week",  type=str, nargs="?", const="next",
                        metavar="YYYY-MM-DD",
                        help="주단위 선별 (해당 날짜가 속한 주 월~일, 기본: 다음 주)")
    parser.add_argument("--input", type=str, help="비제스트 RAW CSV 경로")
    parser.add_argument("--stage", type=str,
                        choices=["pipeline1", "pipeline2", "pipeline3", "pipeline4", "all"],
                        default="all", help="실행 단계 (기본: all)")
    parser.add_argument("--from-responses", type=str, metavar="PATH",
                        help="LLM 응답 파일 경로 (Claude Code 모드 — API 키 불필요)")
    args = parser.parse_args()

    raw_path   = Path(args.input) if args.input else BIZEST_RAW_PATH
    brand_path = BRAND_LIST_PATH

    # ── 기간 범위 모드 (--from / --to) ──────────────────────────────────
    if args.date_from or args.date_to:
        if not (args.date_from and args.date_to):
            logger.error("--from 과 --to 를 함께 지정해야 합니다.")
            sys.exit(1)
        # 범위 응답 파일 명시 지정
        if args.from_responses:
            rp = Path(args.from_responses)
            if not rp.exists():
                logger.error(f"응답 파일 없음: {rp}")
                sys.exit(1)
            with open(rp, encoding="utf-8") as f:
                llm_client.init_file_mode(json.load(f))
            logger.info(f"Claude Code 모드 — 응답 파일 로드: {rp}")
        else:
            d_f = args.date_from.replace("-", "")
            d_t = args.date_to.replace("-", "")
            rp  = get_responses_path(f"{d_f}_{d_t}")
            if rp.exists():
                with open(rp, encoding="utf-8") as f:
                    llm_client.init_file_mode(json.load(f))
                logger.info(f"Claude Code 모드 — 범위 응답 파일 자동 로드: {rp}")
        run_range(args.date_from, args.date_to, raw_path, brand_path)
        return

    # ── 주단위 선별 모드 (--week, Pipeline 1 only) ──────────────────────
    if args.week is not None:
        anchor  = _next_monday() if args.week == "next" else args.week
        dates   = _week_dates(anchor)
        run_weekly(dates, raw_path, brand_path)
        return

    send_dt = args.date or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        datetime.strptime(send_dt, "%Y-%m-%d")
    except ValueError:
        logger.error(f"날짜 형식 오류: {send_dt} (YYYY-MM-DD 형식 필요)")
        sys.exit(1)

    logger.info(f"실행 시작 — send_dt={send_dt}, stage={args.stage}")

    raw_df, brand_df, category_df = load_inputs(raw_path, brand_path)
    raw_df["send_dt"] = send_dt

    # ── LLM 모드 결정 ─────────────────────────────────────────────────
    if args.from_responses:
        responses_path = Path(args.from_responses)
        if not responses_path.exists():
            logger.error(f"응답 파일 없음: {responses_path}")
            sys.exit(1)
        with open(responses_path, encoding="utf-8") as f:
            llm_client.init_file_mode(json.load(f))
        logger.info(f"Claude Code 모드 — 응답 파일 로드: {responses_path}")
    elif not LLM_API_AVAILABLE:
        responses_path = get_responses_path(send_dt)
        if responses_path.exists():
            with open(responses_path, encoding="utf-8") as f:
                llm_client.init_file_mode(json.load(f))
            logger.info(f"Claude Code 모드 — 응답 파일 자동 로드: {responses_path}")
        else:
            logger.warning("ANTHROPIC_API_KEY 미설정 — Pipeline 1만 실행 후 pending_jobs 생성")

    run_log = RunLogger(send_dt=send_dt, input_file=str(raw_path))
    selection_report_path = None

    # ── Pipeline 1 ────────────────────────────────────────────────────
    campaign_meta_urls = load_campaign_meta_urls()

    if args.stage in ("pipeline1", "all"):
        selected_df, rejected_df = run_pipeline1(raw_df, send_dt, campaign_meta_urls=campaign_meta_urls)
        run_log.record_pipeline1(selected_df, rejected_df)

        if len(selected_df) == 0:
            logger.warning("선별 소재 0건 — 처리 종료")
            print("\n⚠️  선별된 소재가 없습니다. 입력 파일과 발송일을 확인하세요.")
            log_path = run_log.finalize(None)
            run_log.print_log_summary(log_path)
            return

        save_pipeline1(selected_df, send_dt)
        selection_report_path = save_selection_report(selected_df, rejected_df, send_dt)

        if args.stage == "pipeline1":
            log_path = run_log.finalize(None)
            run_log.print_log_summary(log_path)
            logger.info(f"Pipeline 1 완료 — 선별 리포트: {selection_report_path}")
            return

        # API 키 없고 응답 파일도 없으면 pending_jobs 생성 후 종료
        if not LLM_API_AVAILABLE and llm_client._file_responses is None:
            jobs_path = generate_pending_jobs(selected_df, brand_df, send_dt)
            print("\n" + "="*60)
            print("⚠️  ANTHROPIC_API_KEY 미설정 — Claude Code 모드로 전환하세요")
            print("="*60)
            print(f"\n📋 생성된 작업 파일: {jobs_path}")
            print("\n다음 단계:")
            print("  1. Claude Code에게 아래 파일을 열어 LLM 응답을 생성해달라고 요청하세요:")
            print(f"     {jobs_path}")
            print(f"  2. 응답 파일 저장 위치: {get_responses_path(send_dt)}")
            print(f"  3. 완료 후 재실행: python3 scripts/run.py --date {send_dt}")
            print("="*60 + "\n")
            log_path = run_log.finalize(None)
            return

    # ── Pipeline 2 ────────────────────────────────────────────────────
    if args.stage in ("pipeline2", "all"):
        if args.stage == "pipeline2":
            p1_path = DATA_DIR / f"pipeline1_output_{send_dt.replace('-', '')}.csv"
            if not p1_path.exists():
                logger.error(f"Pipeline 1 출력 파일 없음: {p1_path}")
                sys.exit(1)
            selected_df = pd.read_csv(p1_path, dtype={"id": str})
            logger.info(f"Pipeline 1 출력 로드: {len(selected_df)}건")

        result_df = run_pipeline2(selected_df, brand_df, category_df)
        run_log.record_pipeline2(result_df)

    # ── Pipeline 3 ────────────────────────────────────────────────────
    if args.stage in ("pipeline3", "all"):
        if args.stage == "pipeline3":
            p1_path = DATA_DIR / f"pipeline1_output_{send_dt.replace('-', '')}.csv"
            if not p1_path.exists():
                logger.error(f"Pipeline 1 출력 파일 없음: {p1_path}")
                sys.exit(1)
            selected_df = pd.read_csv(p1_path, dtype={"id": str})
            result_df = run_pipeline2(selected_df, brand_df, category_df)
            run_log.record_pipeline2(result_df)

        result_df = run_pipeline3(result_df, brand_df)
        run_log.record_pipeline3(result_df)

    # ── Pipeline 4 ────────────────────────────────────────────────────
    if args.stage in ("pipeline4", "all"):
        result_df = run_pipeline4(result_df, brand_df)
        run_log.record_pipeline4(result_df)

    output_path = save_final(result_df, send_dt)
    save_processed_urls(result_df, send_dt)
    log_path    = run_log.finalize(str(output_path))
    print_summary(result_df, send_dt, output_path, selection_report_path)
    run_log.print_log_summary(log_path)


if __name__ == "__main__":
    main()
