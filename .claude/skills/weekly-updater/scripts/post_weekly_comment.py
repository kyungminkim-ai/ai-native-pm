"""
Weekly Updater — Jira Initiative에 Weekly 공유사항 코멘트 게시

사용법:
  python3 post_weekly_comment.py --input weekly_draft.json

입력 JSON 형식 (weekly_draft.json):
  {
    "week": 10,
    "updates": [
      {
        "ticket": "TM-2055",
        "prev_week": [
          "항목 텍스트",
          {"text": "항목 텍스트", "sub": ["하위 항목1", "하위 항목2"]}
        ],
        "action_items": [
          "항목 텍스트",
          {"text": "항목 텍스트", "sub": ["하위 항목1"]}
        ]
      }
    ]
  }

출력:
  output/weekly_result_{YYYYMMDD}.json — 게시 결과 (티켓별 코멘트 URL)
"""

import argparse
import json
import sys
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[4] / "epic-ticket-system" / ".claude" / "skills" / "jira-skill" / "scripts"))
import client

OUTPUT_DIR = Path(__file__).parents[4] / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("weekly-updater")


# ─── ADF 빌더 ────────────────────────────────────────────────────────────────

def build_text_node(text: str, bold: bool = False) -> dict:
    node = {"type": "text", "text": text}
    if bold:
        node["marks"] = [{"type": "strong"}]
    return node


def build_bullet_item(item) -> dict:
    """
    item: str 또는 {"text": str, "sub": [str, ...]}
    """
    if isinstance(item, str):
        return {
            "type": "listItem",
            "content": [
                {"type": "paragraph", "content": [build_text_node(item)]}
            ],
        }
    else:
        # 텍스트 + 하위 항목
        inner = [{"type": "paragraph", "content": [build_text_node(item["text"])]}]
        sub_items = item.get("sub", [])
        if sub_items:
            inner.append({
                "type": "bulletList",
                "content": [build_bullet_item(s) for s in sub_items],
            })
        return {"type": "listItem", "content": inner}


def build_bullet_list(items: list) -> dict:
    return {
        "type": "bulletList",
        "content": [build_bullet_item(i) for i in items],
    }


def build_weekly_adf(week: int, prev_week: list, action_items: list) -> dict:
    """
    Weekly 공유사항 ADF 문서 생성.
    기존 'Automation for Jira' 코멘트와 동일한 구조.
    """
    content = [
        # 제목줄: 🧭 N주차 Weekly 공유사항
        {
            "type": "paragraph",
            "content": [
                build_text_node("🧭 "),
                build_text_node(f"{week}주차 Weekly 공유사항", bold=True),
            ],
        },
        # 섹션1: 지난주 진행상황
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [build_text_node("지난주 진행상황")],
        },
    ]

    if prev_week:
        content.append(build_bullet_list(prev_week))
    else:
        content.append({
            "type": "paragraph",
            "content": [build_text_node("(내용 없음)")],
        })

    # 섹션2: Action Item (이번주)
    content.append({
        "type": "heading",
        "attrs": {"level": 3},
        "content": [build_text_node("Action Item (이번주)")],
    })

    if action_items:
        content.append(build_bullet_list(action_items))
    else:
        content.append({
            "type": "paragraph",
            "content": [build_text_node("(내용 없음)")],
        })

    return {"type": "doc", "version": 1, "content": content}


# ─── 코멘트 게시 ─────────────────────────────────────────────────────────────

def post_comment(ticket_key: str, adf_body: dict) -> dict:
    """POST /rest/api/3/issue/{key}/comment"""
    result = client.post(f"/issue/{ticket_key}/comment", {"body": adf_body})
    comment_id = result.get("id", "")
    base_url = client.get_base_url()
    comment_url = f"{base_url}/browse/{ticket_key}?focusedCommentId={comment_id}"
    return {
        "ticket": ticket_key,
        "comment_id": comment_id,
        "url": comment_url,
        "status": "success",
    }


# ─── 메인 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Jira Weekly 공유사항 코멘트 게시")
    parser.add_argument("--input", "-i", required=True, help="weekly_draft.json 파일 경로")
    parser.add_argument("--dry-run", action="store_true", help="실제 게시 없이 ADF 미리보기만 출력")
    args = parser.parse_args()

    draft_path = Path(args.input)
    if not draft_path.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {draft_path}", file=sys.stderr)
        sys.exit(1)

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    week = draft.get("week")
    updates = draft.get("updates", [])

    if not week or not updates:
        print("[ERROR] 'week'와 'updates' 필드가 필요합니다.", file=sys.stderr)
        sys.exit(1)

    results = []

    for update in updates:
        ticket = update.get("ticket")
        prev_week = update.get("prev_week", [])
        action_items = update.get("action_items", [])

        logger.info(f"처리 중: {ticket} ({week}주차)")

        adf = build_weekly_adf(week, prev_week, action_items)

        if args.dry_run:
            print(f"\n=== {ticket} — {week}주차 Weekly ADF 미리보기 ===")
            print(json.dumps(adf, ensure_ascii=False, indent=2))
            results.append({"ticket": ticket, "status": "dry-run"})
            continue

        try:
            result = post_comment(ticket, adf)
            results.append(result)
            logger.info(f"✅ {ticket} 게시 완료 → {result['url']}")
        except RuntimeError as e:
            logger.error(f"❌ {ticket} 게시 실패: {e}")
            results.append({"ticket": ticket, "status": "error", "error": str(e)})

    # 결과 저장
    today = datetime.now().strftime("%Y%m%d")
    output_path = OUTPUT_DIR / f"weekly_result_{today}.json"
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n📁 결과 저장: {output_path}")
    for r in results:
        status = "✅" if r.get("status") == "success" else ("🔍" if r.get("status") == "dry-run" else "❌")
        url = r.get("url", r.get("status", ""))
        print(f"  {status} {r['ticket']} → {url}")


if __name__ == "__main__":
    main()
