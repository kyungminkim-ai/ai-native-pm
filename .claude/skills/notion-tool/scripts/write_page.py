#!/usr/bin/env python3
"""
Notion 페이지 생성 / 업데이트
마크다운 → Notion 블록 변환 후 API 호출

사용법:
  python3 write_page.py --title "제목" --content output/draft.md [--parent-id ID] [--icon "📄"]
  python3 write_page.py --title "제목" --content output/draft.md --page-id EXISTING_ID  # 업데이트
"""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from client import request, extract_page_id


# ── 마크다운 → Notion 블록 변환 ───────────────────────────────────────────────

def md_to_rich_text(text: str) -> list:
    """인라인 마크다운을 Notion rich_text 배열로 변환 (간단 버전)"""
    # bold+italic, bold, italic, code, link 처리
    segments = []
    pattern = re.compile(
        r'(\*\*\*(.+?)\*\*\*)'      # bold+italic
        r'|(\*\*(.+?)\*\*)'         # bold
        r'|(\*(.+?)\*)'             # italic
        r'|(`(.+?)`)'               # code
        r'|(\[(.+?)\]\((.+?)\))'    # link
    )
    pos = 0
    for m in pattern.finditer(text):
        # plain text before match
        if m.start() > pos:
            segments.append({"type": "text", "text": {"content": text[pos:m.start()]}})
        if m.group(1):  # bold+italic
            segments.append({"type": "text", "text": {"content": m.group(2)},
                             "annotations": {"bold": True, "italic": True}})
        elif m.group(3):  # bold
            segments.append({"type": "text", "text": {"content": m.group(4)},
                             "annotations": {"bold": True}})
        elif m.group(5):  # italic
            segments.append({"type": "text", "text": {"content": m.group(6)},
                             "annotations": {"italic": True}})
        elif m.group(7):  # code
            segments.append({"type": "text", "text": {"content": m.group(8)},
                             "annotations": {"code": True}})
        elif m.group(9):  # link
            segments.append({"type": "text", "text": {"content": m.group(10),
                                                        "link": {"url": m.group(11)}}})
        pos = m.end()
    if pos < len(text):
        segments.append({"type": "text", "text": {"content": text[pos:]}})
    if not segments:
        segments = [{"type": "text", "text": {"content": text}}]
    return segments


def md_line_to_block(line: str) -> dict | None:
    """마크다운 한 줄 → Notion 블록"""
    stripped = line.rstrip()
    if not stripped:
        return None

    # Heading
    m = re.match(r'^(#{1,3})\s+(.*)', stripped)
    if m:
        level = len(m.group(1))
        return {
            "object": "block",
            "type": f"heading_{level}",
            f"heading_{level}": {"rich_text": md_to_rich_text(m.group(2))},
        }

    # Divider
    if re.match(r'^---+$', stripped):
        return {"object": "block", "type": "divider", "divider": {}}

    # Todo
    m = re.match(r'^[-*]\s+\[( |x)\]\s+(.*)', stripped)
    if m:
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {"rich_text": md_to_rich_text(m.group(2)), "checked": m.group(1) == "x"},
        }

    # Bulleted list
    m = re.match(r'^[-*+]\s+(.*)', stripped)
    if m:
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": md_to_rich_text(m.group(1))},
        }

    # Numbered list
    m = re.match(r'^\d+\.\s+(.*)', stripped)
    if m:
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {"rich_text": md_to_rich_text(m.group(1))},
        }

    # Quote / Callout
    m = re.match(r'^>\s+(.*)', stripped)
    if m:
        return {
            "object": "block",
            "type": "quote",
            "quote": {"rich_text": md_to_rich_text(m.group(1))},
        }

    # Table row: | a | b | c |
    if stripped.startswith("|") and stripped.endswith("|"):
        cells = [c.strip() for c in stripped[1:-1].split("|")]
        # separator 행 무시
        if all(re.match(r'^[-:]+$', c) for c in cells if c):
            return None
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": md_to_rich_text(" | ".join(cells))
            },
        }

    # Paragraph (기본)
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": md_to_rich_text(stripped)},
    }


def md_to_blocks(md_text: str) -> list:
    """마크다운 전체 텍스트 → Notion 블록 목록"""
    blocks = []
    lines = md_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        # 코드 블록 처리
        m = re.match(r'^```(\w*)', line)
        if m:
            lang = m.group(1) or "plain text"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            code_text = "\n".join(code_lines)
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": code_text}}],
                    "language": lang if lang else "plain text",
                },
            })
            i += 1
            continue

        block = md_line_to_block(line)
        if block:
            blocks.append(block)
        i += 1

    return blocks


# ── Notion API 호출 ───────────────────────────────────────────────────────────

def chunk_blocks(blocks: list, size: int = 100) -> list[list]:
    return [blocks[i:i+size] for i in range(0, len(blocks), size)]


def create_page(title: str, blocks: list, parent_id: str = None, icon: str = None) -> dict:
    parent_id = parent_id or os.environ.get("NOTION_DEFAULT_PAGE_ID", "")
    if not parent_id:
        print("[ERROR] --parent-id 또는 NOTION_DEFAULT_PAGE_ID 환경변수가 필요합니다.", file=sys.stderr)
        sys.exit(1)

    # parent_id가 DB인지 page인지 판단 (일단 page로 시도, 실패 시 DB로)
    payload = {
        "parent": {"page_id": extract_page_id(parent_id)},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": title}}]}
        },
        "children": blocks[:100],  # 최초 생성 시 최대 100개
    }
    if icon:
        payload["icon"] = {"type": "emoji", "emoji": icon}

    page = request("POST", "/pages", json=payload)
    page_id = page["id"]

    # 나머지 블록 append
    remaining = blocks[100:]
    for chunk in chunk_blocks(remaining):
        request("PATCH", f"/blocks/{page_id}/children", json={"children": chunk})

    return page


def update_page(page_id: str, title: str, blocks: list, icon: str = None) -> dict:
    page_id = extract_page_id(page_id)

    # 제목 업데이트
    props_payload = {
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": title}}]}
        }
    }
    if icon:
        props_payload["icon"] = {"type": "emoji", "emoji": icon}
    request("PATCH", f"/pages/{page_id}", json=props_payload)

    # 기존 블록 모두 삭제 후 새로 추가
    existing = request("GET", f"/blocks/{page_id}/children")
    for block in existing.get("results", []):
        try:
            request("DELETE", f"/blocks/{block['id']}")
        except SystemExit:
            pass  # 삭제 실패 무시

    # 새 블록 추가
    for chunk in chunk_blocks(blocks):
        request("PATCH", f"/blocks/{page_id}/children", json={"children": chunk})

    return request("GET", f"/pages/{page_id}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--content", required=True, help="마크다운 파일 경로")
    parser.add_argument("--parent-id", default=None)
    parser.add_argument("--page-id", default=None, help="업데이트할 기존 페이지 ID")
    parser.add_argument("--icon", default=None, help="이모지 아이콘 (예: 📄)")
    args = parser.parse_args()

    md_text = Path(args.content).read_text(encoding="utf-8")
    blocks = md_to_blocks(md_text)

    if args.page_id:
        page = update_page(args.page_id, args.title, blocks, args.icon)
        print(f"[UPDATE] 페이지 업데이트 완료")
    else:
        page = create_page(args.title, blocks, args.parent_id, args.icon)
        print(f"[CREATE] 페이지 생성 완료")

    url = page.get("url", "")
    page_id = page.get("id", "")
    print(f"URL: {url}")
    print(f"PAGE_ID: {page_id}")


if __name__ == "__main__":
    main()
