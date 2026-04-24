"""Pipeline 4 — LLM Red Team 메시지 품질 검토.

생성된 메시지를 생성 규칙과 독립된 관점에서 LLM이 재검토한다.
수신자 경험·브랜드 적합성·마케팅 효과 관점에서 score/verdict/notes를 추가하고,
warning/fail 판정 시 needs_review 플래그를 상향한다.
"""
import logging
import pandas as pd
from llm_client import review_message, set_current_row
from rules import lookup_brand_name

logger = logging.getLogger(__name__)

VERDICT_FAIL = "fail"
VERDICT_WARN = "warning"


def run_pipeline4(result_df: pd.DataFrame, brand_df: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"Pipeline 4 시작 — {len(result_df)}건 LLM 검토")

    scores, verdicts, notes_list, issues_list = [], [], [], []

    for i, (_, row) in enumerate(result_df.iterrows(), 1):
        row_id     = str(row.get("id", f"idx-{i}"))
        set_current_row(row_id)
        brand_id   = str(row.get("brand_id", "") or "")
        brand_name = lookup_brand_name(brand_id, brand_df)
        promo      = str(row.get("promotion_content", "") or "")
        title      = str(row.get("title", "") or "")
        v1         = str(row.get("contents_v1", "") or "")
        v2         = str(row.get("contents_v2", "") or "")
        v3         = str(row.get("contents_v3", "") or "")
        target     = str(row.get("target", "") or "")

        result = review_message(title, v1, v2, brand_name, promo, target, contents_v3=v3)

        scores.append(result.get("score"))
        verdicts.append(result.get("verdict", VERDICT_WARN))
        notes_list.append(result.get("notes", ""))
        issues_list.append(", ".join(result.get("issues", [])))

        if i % 10 == 0:
            logger.info(f"  진행: {i}/{len(result_df)}")

    df = result_df.copy()
    df["review_score"]   = scores
    df["review_verdict"] = verdicts
    df["review_notes"]   = notes_list
    df["review_issues"]  = issues_list

    prev_review = df.get("needs_review", pd.Series([False] * len(df)))
    df["needs_review"] = prev_review | df["review_verdict"].isin([VERDICT_FAIL, VERDICT_WARN])

    pass_cnt = verdicts.count("pass")
    warn_cnt = verdicts.count(VERDICT_WARN)
    fail_cnt = verdicts.count(VERDICT_FAIL)
    logger.info(f"LLM 검토 완료 — pass={pass_cnt} / warning={warn_cnt} / fail={fail_cnt}")

    return df
