#!/usr/bin/env python3
"""
Notion 페이지 읽기 → 마크다운 변환
사용법: python3 fetch_page.py --page-id PAGE_ID_OR_URL [--output path.md] [--depth 2]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from client import request, extract_page_id, get_plain_text, get_page_title


def rich_text_to_md(rich_text_list: list) -> str:
    parts = []
    for t in rich_text_list:
        text = t.get("plain_text", "")
        ann = t.get("annotations", {})
        href = t.get("href")
        if ann.get("code"):
            text = f"`{text}`"
        if ann.get("bold"):
            text = f"**{text}**"
        if ann.get("italic"):
            text = f"*{text}*"
        if ann.get("strikethrough"):
            text = f"~~{text}~~"
        if href:
            text = f"[{text}]({href})"
        parts.append(text)
    return "".join(parts)


def blocks_to_md(blocks: list, depth: int = 0, max_depth: int = 2) -> list[str]:
    lines = []
    indent = "  " * depth

    for block in blocks:
        btype = block.get("type", "")
        content = block.get(btype, {})
        rich = content.get("rich_text", [])
        text = rich_text_to_md(rich)

        if btype == "paragraph":
            lines.append(f"{indent}{text}" if text else "")
        elif btype.startswith("heading_"):
            level = int(btype[-1])
            lines.append(f"{'#' * level} {text}")
        elif btype == "bulleted_list_item":
            lines.append(f"{indent}- {text}")
        elif btype == "numbered_list_item":
            lines.append(f"{indent}1. {text}")
        elif btype == "to_do":
            checked = "x" if content.get("checked") else " "
            lines.append(f"{indent}- [{checked}] {text}")
        elif btype == "toggle":
            lines.append(f"{indent}> **{text}**")
        elif btype == "quote":
            lines.append(f"{indent}> {text}")
        elif btype == "callout":
            emoji = (content.get("icon") or {}).get("emoji", "")
            lines.append(f"{indent}> {emoji} {text}")
        elif btype == "code":
            lang = content.get("language", "")
            code_text = get_plain_text(rich)
            lines.append(f"```{lang}")
            lines.append(code_text)
            lines.append("```")
        elif btype == "divider":
            lines.append("---")
        elif btype == "table_of_contents":
            pass  # skip
        elif btype == "image":
            img_url = (content.get("file") or content.get("external") or {}).get("url", "")
            caption = rich_text_to_md(content.get("caption", []))
            lines.append(f"![{caption}]({img_url})")
        elif btype == "bookmark":
            url = content.get("url", "")
            caption = rich_text_to_md(content.get("caption", [])) or url
            lines.append(f"[{caption}]({url})")
        elif btype == "child_page":
            child_title = content.get("title", "")
            lines.append(f"- [하위 페이지] {child_title}")
        elif btype == "child_database":
            db_title = content.get("title", "")
            lines.append(f"- [하위 DB] {db_title}")
        elif btype == "column_list":
            pass  # 컬럼은 하위 블록으로 처리
        elif btype == "column":
            pass  # 동일
        elif btype == "table":
            pass  # table_row로 처리
        elif btype == "table_row":
            cells = content.get("cells", [])
            row_texts = [rich_text_to_md(cell) for cell in cells]
            lines.append("| " + " | ".join(row_texts) + " |")
        else:
            if text:
                lines.append(f"{indent}{text}")

        # 하위 블록 재귀 처리
        if block.get("has_children") and depth < max_depth:
            children = fetch_block_children(block["id"])
            lines.extend(blocks_to_md(children, depth + 1, max_depth))

    return lines


def fetch_block_children(block_id: str) -> list:
    all_results = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        data = request("GET", f"/blocks/{block_id}/children", params=params)
        all_results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return all_results


def fetch_page_as_md(page_id: str, max_depth: int = 2) -> tuple[str, str]:
    """(title, markdown_content) 반환"""
    # 페이지 메타 가져오기
    page = request("GET", f"/pages/{page_id}")
    title = get_page_title(page)

    # 블록 내용 가져오기
    blocks = fetch_block_children(page_id)
    lines = blocks_to_md(blocks, max_depth=max_depth)

    md = f"# {title}\n\n" + "\n".join(lines)
    return title, md


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-id", required=True, help="Notion 페이지 ID 또는 URL")
    parser.add_argument("--output", default=None, help="저장할 파일 경로 (미지정 시 stdout)")
    parser.add_argument("--depth", type=int, default=2, help="중첩 블록 깊이 (기본값: 2)")
    args = parser.parse_args()

    page_id = extract_page_id(args.page_id)
    title, md = fetch_page_as_md(page_id, max_depth=args.depth)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"[OK] 저장 완료 → {args.output}")
        print(f"     제목: {title}")
    else:
        print(md)


if __name__ == "__main__":
    main()
