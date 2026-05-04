#!/usr/bin/env python3
"""
Notion API 공통 클라이언트
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("[ERROR] requests 패키지가 필요합니다: pip install requests", file=sys.stderr)
    sys.exit(1)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
LOG_PATH = Path("output/notion_skill.log")


def get_token():
    token = os.environ.get("NOTION_API_TOKEN", "")
    if not token:
        print("[AUTH ERROR] NOTION_API_TOKEN 환경변수가 설정되지 않았습니다.", file=sys.stderr)
        sys.exit(1)
    return token


def get_headers():
    return {
        "Authorization": f"Bearer {get_token()}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _log(message: str):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")


def request(method: str, path: str, retries: int = 1, **kwargs):
    url = f"{NOTION_API_BASE}{path}"
    headers = get_headers()

    for attempt in range(retries + 1):
        try:
            resp = requests.request(method, url, headers=headers, **kwargs)
            _log(f"{method} {path} → {resp.status_code}")

            if resp.status_code == 401:
                print("[AUTH ERROR] API 토큰이 유효하지 않습니다. NOTION_API_TOKEN을 확인하세요.", file=sys.stderr)
                sys.exit(1)
            if resp.status_code == 404:
                print(f"[NOT FOUND] 페이지/DB를 찾을 수 없습니다: {path}", file=sys.stderr)
                print("Integration이 해당 페이지에 공유(Share)되어 있는지 확인하세요.", file=sys.stderr)
                sys.exit(1)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 2))
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()

        except requests.RequestException as e:
            if attempt < retries:
                time.sleep(1)
                continue
            _log(f"ERROR: {e}")
            print(f"[ERROR] API 요청 실패: {e}", file=sys.stderr)
            sys.exit(1)


def extract_page_id(url_or_id: str) -> str:
    """Notion URL 또는 ID에서 순수 ID(하이픈 제거) 추출"""
    # URL 형태: https://notion.so/Title-abc123def456...
    if "notion.so" in url_or_id or "notion.com" in url_or_id:
        # 마지막 경로 세그먼트에서 ID 추출
        segment = url_or_id.rstrip("/").split("/")[-1]
        # ?v= 등 쿼리 제거
        segment = segment.split("?")[0].split("#")[0]
        # 32자리 hex 추출 (하이픈 제거 후)
        raw = segment.replace("-", "")
        # 마지막 32자
        if len(raw) >= 32:
            raw_id = raw[-32:]
            return f"{raw_id[:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"
    # 이미 UUID 형태
    cleaned = url_or_id.replace("-", "")
    if len(cleaned) == 32:
        return f"{cleaned[:8]}-{cleaned[8:12]}-{cleaned[12:16]}-{cleaned[16:20]}-{cleaned[20:]}"
    return url_or_id


def get_plain_text(rich_text_list: list) -> str:
    """Notion rich_text 배열에서 평문 텍스트 추출"""
    return "".join(t.get("plain_text", "") for t in rich_text_list)


def get_page_title(page: dict) -> str:
    """페이지/DB 객체에서 제목 추출"""
    props = page.get("properties", {})
    # 제목 프로퍼티 우선순위: title > Name > 첫 번째 title 타입
    for key in ["title", "Name", "제목"]:
        if key in props:
            prop = props[key]
            if prop.get("type") == "title":
                return get_plain_text(prop.get("title", []))
    for prop in props.values():
        if prop.get("type") == "title":
            return get_plain_text(prop.get("title", []))
    return "(제목 없음)"
