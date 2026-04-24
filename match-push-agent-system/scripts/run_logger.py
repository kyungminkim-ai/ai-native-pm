"""실행 로그 기록 모듈 — 파이프라인별 처리 결과를 JSON으로 저장."""
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd
from config import LOGS_DIR

logger = logging.getLogger(__name__)

# 탈락 사유 코드 (Pipeline 1)
REASON_CANCELLED                 = "CANCELLED"                  # 취소 키워드 감지
REASON_ALREADY_SELECTED          = "ALREADY_SELECTED"           # 선정 여부=광고진행 계열
REASON_ALREADY_PROC              = "ALREADY_PROCESSED"          # 동일 실행 내 id 중복 (기간/주간 배치 전용)
REASON_URL_ALREADY_SENT          = "URL_ALREADY_SENT"           # 동일 실행 내 URL 중복 (기간/주간 배치 전용)
REASON_CAMPAIGN_META_REGISTERED  = "CAMPAIGN_META_REGISTERED"   # 캠페인메타엔진 시트 등록 URL
REASON_SHEET_DUPLICATE           = "SHEET_DUPLICATE"            # 시트 기반 중복 (url+brand+date)
REASON_LANDING_NOT_OPEN          = "LANDING_NOT_IN_WINDOW"      # 발송 윈도우 미충족

# 선별 사유 코드 (Pipeline 1)
REASON_MARKETING_EXCEPTION = "MARKETING_TEAM_EXCEPTION"  # 마케팅팀 예외 통과 (레거시)
REASON_LANDING_OPEN        = "LANDING_IN_WINDOW"          # 발송 윈도우 내 오픈

# URL 유효성 탈락 코드 (Pipeline 1 — 윈도우 통과 후 추가 검증)
REASON_URL_MISSING      = "URL_MISSING"       # landing_url 없음
REASON_URL_PLACEHOLDER  = "URL_PLACEHOLDER"   # URL에 한국어/TBD 등 임시값
REASON_URL_NO_ID        = "URL_NO_ID"         # /content/ 또는 /campaign/ ID 없음/너무 짧음
REASON_URL_NOT_MUSINSA  = "URL_NOT_MUSINSA"   # musinsa.com이 아닌 외부 URL
REASON_URL_FORMAT       = "URL_FORMAT"        # http 시작 아닌 비정상 형식

URL_REJECTION_CODES = {
    REASON_URL_MISSING, REASON_URL_PLACEHOLDER,
    REASON_URL_NO_ID, REASON_URL_NOT_MUSINSA, REASON_URL_FORMAT,
}

_REASON_LABEL = {
    REASON_CANCELLED:                "취소 키워드 감지",
    REASON_ALREADY_SELECTED:         "선정여부 = 광고진행 계열",
    REASON_ALREADY_PROC:             "동일 실행 내 id 중복",
    REASON_URL_ALREADY_SENT:         "동일 실행 내 URL 중복",
    REASON_CAMPAIGN_META_REGISTERED: "캠페인메타엔진 등록 URL 중복",
    REASON_SHEET_DUPLICATE:          "시트 기반 중복 (URL+브랜드+날짜)",
    REASON_LANDING_NOT_OPEN:   "발송 윈도우(D-1~D-0) 미충족",
    REASON_MARKETING_EXCEPTION:"마케팅팀 예외 통과 (레거시)",
    REASON_LANDING_OPEN:       "발송 윈도우(D-1~D-0) 내 오픈",
    REASON_URL_MISSING:        "랜딩 URL 없음",
    REASON_URL_PLACEHOLDER:    "랜딩 URL 임시값 (추후기재/TBD 등)",
    REASON_URL_NO_ID:          "랜딩 URL content/campaign ID 없음",
    REASON_URL_NOT_MUSINSA:    "랜딩 URL musinsa.com 외부 도메인",
    REASON_URL_FORMAT:         "랜딩 URL 형식 오류 (http 미시작)",
}


class RunLogger:
    """파이프라인 실행 로그를 수집하고 JSON 파일로 저장."""

    def __init__(self, send_dt: str, input_file: str):
        self.send_dt    = send_dt
        self.input_file = str(input_file)
        self.run_id     = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._log: dict = {
            "run_id":       self.run_id,
            "send_dt":      send_dt,
            "input_file":   str(input_file),
            "started_at":   datetime.now().isoformat(),
            "pipeline1":    None,
            "pipeline2":    None,
            "pipeline3":    None,
            "pipeline4":    None,
            "output_file":  None,
            "completed_at": None,
        }

    # ── Pipeline 1 ────────────────────────────────────────────────────
    def record_pipeline1(
        self,
        selected_df: pd.DataFrame,
        rejected_df: pd.DataFrame,
    ) -> None:
        n_sel = len(selected_df)
        n_rej = len(rejected_df)

        # 탈락 사유 집계
        rej_counts: dict = {}
        if not rejected_df.empty and "rejection_reason" in rejected_df.columns:
            rej_counts = rejected_df["rejection_reason"].value_counts().to_dict()

        # 선별 사유 집계
        sel_counts: dict = {}
        if not selected_df.empty and "selection_reason" in selected_df.columns:
            sel_counts = selected_df["selection_reason"].value_counts().to_dict()

        # 탈락 상세 목록 (최대 500건)
        rejected_items = []
        if not rejected_df.empty:
            key_cols = ["id", "rejection_reason", "rejection_detail",
                        "register_team_name", "landing_url"]
            available = [c for c in key_cols if c in rejected_df.columns]
            for row in rejected_df[available].to_dict("records"):
                rejected_items.append({k: str(v or "") for k, v in row.items()})

        self._log["pipeline1"] = {
            "total_input":       n_sel + n_rej,
            "selected":          n_sel,
            "rejected":          n_rej,
            "selection_reasons": {
                k: {"count": v, "label": _REASON_LABEL.get(k, k)}
                for k, v in sel_counts.items()
            },
            "rejection_reasons": {
                k: {"count": v, "label": _REASON_LABEL.get(k, k)}
                for k, v in rej_counts.items()
            },
            "rejected_items":    rejected_items[:500],
        }

    # ── Pipeline 2 ────────────────────────────────────────────────────
    def record_pipeline2(self, result_df: pd.DataFrame) -> None:
        total  = len(result_df)
        v1_ok  = int(result_df["contents"].notna().sum())    if "contents"    in result_df.columns else 0
        v2_ok  = int(result_df["contents_v2"].notna().sum()) if "contents_v2" in result_df.columns else 0

        title_src: dict = {}
        if "title_source" in result_df.columns:
            title_src = result_df["title_source"].value_counts().to_dict()

        self._log["pipeline2"] = {
            "processed":    total,
            "title_source": {
                "original": title_src.get("original", 0),
                "llm":      title_src.get("llm",      0),
                "fallback": title_src.get("fallback",  0),
            },
            "v1_success":   v1_ok,
            "v1_failed":    total - v1_ok,
            "v2_success":   v2_ok,
            "v2_failed":    total - v2_ok,
        }

    # ── Pipeline 3 ────────────────────────────────────────────────────
    def record_pipeline3(self, result_df: pd.DataFrame) -> None:
        total   = len(result_df)
        errors  = int(result_df["error_flag"].sum())  if "error_flag"   in result_df.columns else 0
        reviews = int(result_df["needs_review"].sum()) if "needs_review" in result_df.columns else 0

        issue_counts: dict = {}
        if "validation_notes" in result_df.columns:
            for notes in result_df["validation_notes"].dropna():
                for issue in str(notes).split(", "):
                    issue = issue.strip()
                    if issue:
                        base = re.sub(r'\(.*?\)', '', issue).strip()
                        issue_counts[base] = issue_counts.get(base, 0) + 1

        self._log["pipeline3"] = {
            "total":        total,
            "passed":       total - reviews,
            "needs_review": reviews,
            "errors":       errors,
            "issue_counts": issue_counts,
        }

    # ── Pipeline 4 ────────────────────────────────────────────────────
    def record_pipeline4(self, result_df: pd.DataFrame) -> None:
        total    = len(result_df)
        verdicts = result_df["review_verdict"].value_counts().to_dict() if "review_verdict" in result_df.columns else {}
        scores   = result_df["review_score"].dropna() if "review_score" in result_df.columns else pd.Series([], dtype=float)

        issue_counts: dict = {}
        if "review_issues" in result_df.columns:
            for issues in result_df["review_issues"].dropna():
                for issue in str(issues).split(", "):
                    issue = issue.strip()
                    if issue:
                        issue_counts[issue] = issue_counts.get(issue, 0) + 1

        self._log["pipeline4"] = {
            "total":          total,
            "verdict_pass":   int(verdicts.get("pass", 0)),
            "verdict_warning": int(verdicts.get("warning", 0)),
            "verdict_fail":   int(verdicts.get("fail", 0)),
            "avg_score":      round(float(scores.mean()), 2) if len(scores) > 0 else None,
            "issue_counts":   issue_counts,
        }

    # ── Finalize ─────────────────────────────────────────────────────
    def finalize(self, output_file: Optional[str]) -> Path:
        self._log["output_file"]  = str(output_file) if output_file else None
        self._log["completed_at"] = datetime.now().isoformat()

        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOGS_DIR / f"run_{self.run_id}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(self._log, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"실행 로그 저장: {log_path}")
        return log_path

    def print_log_summary(self, log_path: Path) -> None:
        p1 = self._log.get("pipeline1") or {}
        p2 = self._log.get("pipeline2") or {}
        p3 = self._log.get("pipeline3") or {}

        print(f"\n📋 실행 로그: {log_path}")

        if p1:
            print(f"\n[Pipeline 1] 입력={p1['total_input']}건 → 선별={p1['selected']}건 / 탈락={p1['rejected']}건")
            for code, info in p1.get("rejection_reasons", {}).items():
                print(f"  ├ {info['label']} ({code}): {info['count']}건")

        if p2:
            ts = p2.get("title_source", {})
            print(f"\n[Pipeline 2] title_source: 원본={ts.get('original',0)} / LLM재생성={ts.get('llm',0)} / fallback={ts.get('fallback',0)}")
            print(f"  V1 생성 성공={p2.get('v1_success',0)} / 실패={p2.get('v1_failed',0)}")
            print(f"  V2 생성 성공={p2.get('v2_success',0)} / 실패={p2.get('v2_failed',0)}")

        if p3:
            print(f"\n[Pipeline 3] 통과={p3.get('passed',0)} / 검수필요={p3.get('needs_review',0)} / 오류={p3.get('errors',0)}")
            for issue, cnt in sorted(p3.get("issue_counts", {}).items(), key=lambda x: -x[1]):
                print(f"  ├ {issue}: {cnt}건")

        p4 = self._log.get("pipeline4") or {}
        if p4:
            avg = p4.get("avg_score")
            avg_str = f"{avg:.2f}" if avg is not None else "-"
            print(f"\n[Pipeline 4] pass={p4.get('verdict_pass',0)} / warning={p4.get('verdict_warning',0)} / fail={p4.get('verdict_fail',0)} (평균점수={avg_str})")
            for issue, cnt in sorted(p4.get("issue_counts", {}).items(), key=lambda x: -x[1])[:5]:
                print(f"  ├ {issue}: {cnt}건")
