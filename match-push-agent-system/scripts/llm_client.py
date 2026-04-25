"""Claude API 클라이언트 — 재시도·파싱 포함."""
import json
import time
import re
import logging
from typing import Optional
import anthropic
from config import LLM_MODEL, LLM_MAX_TOKENS, LLM_MAX_RETRIES
from prompts import build_title_prompt, build_v1_benefit_prompt, build_v2_brand_prompt, build_v3_best_prompt, build_review_prompt, build_category_infer_prompt

logger = logging.getLogger(__name__)

_client: Optional[anthropic.Anthropic] = None

# Claude Code 파일 모드 (API 키 없을 때 사용)
_file_responses: Optional[dict] = None
_current_row_id: str = ""


def init_file_mode(responses: dict) -> None:
    """API 키 없이 미리 생성된 응답 파일을 LLM 대신 사용하도록 설정."""
    global _file_responses
    _file_responses = responses
    logger.info(f"LLM 파일 모드 활성화 — {len(responses)}건 로드")


def set_current_row(row_id: str) -> None:
    global _current_row_id
    _current_row_id = str(row_id)


def _get_file_value(key: str):
    if _file_responses is None or not _current_row_id:
        return None
    return _file_responses.get(_current_row_id, {}).get(key)


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _call_claude(prompt: str) -> Optional[str]:
    from config import LLM_API_AVAILABLE
    if not LLM_API_AVAILABLE:
        return None
    client = get_client()
    for attempt in range(LLM_MAX_RETRIES):
        try:
            response = client.messages.create(
                model=LLM_MODEL,
                max_tokens=LLM_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except anthropic.RateLimitError:
            wait = 2 ** attempt
            logger.warning(f"Rate limit, {wait}s 대기 후 재시도 ({attempt + 1}/{LLM_MAX_RETRIES})")
            time.sleep(wait)
        except anthropic.APIError as e:
            logger.error(f"API 오류 (시도 {attempt + 1}): {e}")
            time.sleep(2 ** attempt)
    return None


def _parse_json(raw: Optional[str]) -> Optional[dict]:
    if not raw:
        return None
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    logger.error(f"JSON 파싱 실패: {(raw or '')[:100]}")
    return None


def regenerate_title(brand: str, promotion_content: str, target: str, remarks: str = "") -> Optional[str]:
    cached = _get_file_value("title")
    if cached is not None:
        return str(cached)
    prompt = build_title_prompt(brand, promotion_content, target, remarks=remarks)
    raw = _call_claude(prompt)
    parsed = _parse_json(raw)
    if parsed and "title" in parsed:
        return str(parsed["title"])
    return None


def generate_v1(
    title: str, brand: str, promotion_content: str,
    content_type: str, target: str, remarks: str = "",
) -> dict:
    cached = _get_file_value("contents")
    if cached is not None:
        return {"message": str(cached), "confidence": float(_get_file_value("confidence_v1") or 4.0)}
    prompt = build_v1_benefit_prompt(title, brand, promotion_content, content_type, target, remarks=remarks)
    raw = _call_claude(prompt)
    parsed = _parse_json(raw)
    if parsed and "message" in parsed:
        return {
            "message":    str(parsed["message"]),
            "confidence": float(parsed.get("confidence", 0.0)),
        }
    return {"message": None, "confidence": None}


def generate_v2(
    title: str, brand: str, promotion_content: str,
    content_type: str, target: str, remarks: str = "",
) -> dict:
    cached = _get_file_value("contents_v2")
    if cached is not None:
        return {"message": str(cached), "confidence": float(_get_file_value("confidence_v2") or 4.0)}
    prompt = build_v2_brand_prompt(title, brand, promotion_content, content_type, target, remarks=remarks)
    raw = _call_claude(prompt)
    parsed = _parse_json(raw)
    if parsed and "message" in parsed:
        return {
            "message":    str(parsed["message"]),
            "confidence": float(parsed.get("confidence", 0.0)),
        }
    return {"message": None, "confidence": None}


def generate_v3(
    title: str, brand: str, promotion_content: str,
    content_type: str, target: str, remarks: str = "",
    v1_message: str = "", v2_message: str = "",
) -> dict:
    cached = _get_file_value("contents_v3")
    if cached is not None:
        return {"message": str(cached), "confidence": float(_get_file_value("confidence_v3") or 4.0)}
    prompt = build_v3_best_prompt(
        title, brand, promotion_content, content_type, target,
        v1_message=v1_message, v2_message=v2_message, remarks=remarks,
    )
    raw = _call_claude(prompt)
    parsed = _parse_json(raw)
    if parsed and "message" in parsed:
        return {
            "message":    str(parsed["message"]),
            "confidence": float(parsed.get("confidence", 0.0)),
        }
    return {"message": None, "confidence": None}


def infer_category_ids(
    event_name: str,
    promotion_content: str,
    main_title: str,
    landing_url: str,
    category_list_str: str,
) -> list:
    """소재 내용 기반 카테고리 코드 유추 (최대 3개 리스트 반환).
    file mode에서는 응답 파일의 category_codes 필드를 사용한다.
    API 키도 없고 응답 파일도 없으면 빈 리스트 반환.
    """
    from config import LLM_API_AVAILABLE
    if not LLM_API_AVAILABLE:
        # file mode: pending_jobs 응답 파일에서 category_codes 읽기
        if _file_responses is not None:
            codes = _get_file_value("category_codes")
            if codes and isinstance(codes, list):
                return [str(c).strip() for c in codes if c]
        return []
    if not category_list_str:
        return []
    prompt = build_category_infer_prompt(event_name, promotion_content, main_title, landing_url, category_list_str)
    raw = _call_claude(prompt)
    parsed = _parse_json(raw)
    if parsed and "codes" in parsed and isinstance(parsed["codes"], list):
        return [str(c).strip() for c in parsed["codes"] if c]
    return []


def review_message(
    title: str, contents_v1: str, contents_v2: str,
    brand: str, promotion_content: str, target: str,
    contents_v3: str = "",
) -> dict:
    score = _get_file_value("review_score")
    if score is not None:
        return {
            "score":   float(score),
            "verdict": str(_get_file_value("review_verdict") or "warning"),
            "notes":   str(_get_file_value("review_notes") or ""),
            "issues":  list(_get_file_value("review_issues") or []),
        }
    prompt = build_review_prompt(title, contents_v1, contents_v2, brand, promotion_content, target, contents_v3=contents_v3)
    raw = _call_claude(prompt)
    parsed = _parse_json(raw)
    if parsed and "score" in parsed:
        return {
            "score":   float(parsed.get("score", 3.0)),
            "verdict": str(parsed.get("verdict", "warning")),
            "notes":   str(parsed.get("notes", "")),
            "issues":  list(parsed.get("issues", [])),
        }
    return {"score": None, "verdict": "warning", "notes": "검토 실패", "issues": []}
