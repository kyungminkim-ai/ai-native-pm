"""
gmail-tool — 마크다운 → 이메일 인라인 CSS HTML 변환기

사용법:
  python3 md_to_html.py --input output/weekly_flash_v1.md --output output/final_email.html
  python3 md_to_html.py --input report.md  # stdout 출력

출력: 이메일 클라이언트 호환 인라인 CSS HTML (외부 의존성 없음)
"""

import argparse
import re
import sys
from pathlib import Path

# ─── 인라인 스타일 정의 ──────────────────────────────────────────────────

STYLES = {
    "body": (
        "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;"
        "font-size: 14px; line-height: 1.6; color: #333333;"
        "max-width: 680px; margin: 0 auto; padding: 24px 16px;"
        "background-color: #ffffff;"
    ),
    "h1": (
        "font-size: 22px; font-weight: 700; color: #172B4D;"
        "border-bottom: 2px solid #0052CC; padding-bottom: 8px;"
        "margin: 0 0 16px 0;"
    ),
    "h2": (
        "font-size: 16px; font-weight: 700; color: #0052CC;"
        "margin: 28px 0 10px 0; padding: 0;"
    ),
    "h3": (
        "font-size: 14px; font-weight: 700; color: #253858;"
        "margin: 20px 0 8px 0;"
    ),
    "p": "margin: 0 0 10px 0;",
    "ul": "margin: 0 0 10px 0; padding-left: 20px;",
    "li": "margin: 4px 0;",
    "table": (
        "border-collapse: collapse; width: 100%;"
        "margin: 0 0 16px 0; font-size: 13px;"
    ),
    "th": (
        "background-color: #F4F5F7; color: #172B4D;"
        "font-weight: 700; text-align: left;"
        "padding: 8px 12px; border: 1px solid #DFE1E6;"
    ),
    "td": (
        "padding: 7px 12px; border: 1px solid #DFE1E6;"
        "vertical-align: top;"
    ),
    "blockquote": (
        "background-color: #F4F5F7; border-left: 4px solid #0052CC;"
        "margin: 0 0 10px 0; padding: 10px 14px; color: #5E6C84;"
    ),
    "hr": (
        "border: none; border-top: 1px solid #DFE1E6;"
        "margin: 20px 0;"
    ),
    "a": "color: #0052CC; text-decoration: none;",
    "code": (
        "background-color: #F4F5F7; border-radius: 3px;"
        "padding: 2px 4px; font-family: monospace; font-size: 12px;"
        "color: #172B4D;"
    ),
    "footer": (
        "font-size: 11px; color: #97A0AF; margin-top: 32px;"
        "padding-top: 12px; border-top: 1px solid #DFE1E6;"
    ),
}


# ─── 변환 함수 ───────────────────────────────────────────────────────────

def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline_styles(text: str) -> str:
    """인라인 마크다운(굵게, 기울임, 코드, 링크)을 HTML로 변환."""
    # 코드 (백틱)
    text = re.sub(
        r"`([^`]+)`",
        lambda m: f'<code style="{STYLES["code"]}">{_escape_html(m.group(1))}</code>',
        text,
    )
    # 굵게
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    # 기울임
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)
    # 링크
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{m.group(2)}" style="{STYLES["a"]}">{m.group(1)}</a>',
        text,
    )
    return text


def _parse_table(lines: list[str]) -> str:
    """마크다운 테이블 블록을 HTML <table>로 변환."""
    html = f'<table style="{STYLES["table"]}">'
    header_done = False
    for line in lines:
        # 구분선 행 (| --- | --- |) 스킵
        if re.match(r"^\|[\s\-:|]+\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not header_done:
            html += "<thead><tr>"
            for cell in cells:
                html += f'<th style="{STYLES["th"]}">{_inline_styles(cell)}</th>'
            html += "</tr></thead><tbody>"
            header_done = True
        else:
            html += "<tr>"
            for cell in cells:
                html += f'<td style="{STYLES["td"]}">{_inline_styles(cell)}</td>'
            html += "</tr>"
    html += "</tbody></table>"
    return html


def convert(md_text: str, title: str = "") -> str:
    """마크다운 텍스트 전체를 HTML 문서로 변환."""
    lines = md_text.splitlines()
    html_parts: list[str] = []
    doc_title = title
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── 테이블 블록 감지 ──────────────────────────────────
        if re.match(r"^\|", line):
            table_lines = []
            while i < len(lines) and re.match(r"^\|", lines[i]):
                table_lines.append(lines[i])
                i += 1
            html_parts.append(_parse_table(table_lines))
            continue

        # ── 인용 ─────────────────────────────────────────────
        if line.startswith("> "):
            content = _inline_styles(line[2:].strip())
            html_parts.append(f'<blockquote style="{STYLES["blockquote"]}"><p style="{STYLES["p"]}">{content}</p></blockquote>')
            i += 1
            continue

        # ── 수평선 ────────────────────────────────────────────
        if re.match(r"^---+$|^===+$|^\*\*\*+$", line.strip()):
            html_parts.append(f'<hr style="{STYLES["hr"]}" />')
            i += 1
            continue

        # ── 제목 ─────────────────────────────────────────────
        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading_match:
            level = len(heading_match.group(1))
            text = _inline_styles(heading_match.group(2).strip())
            tag = f"h{level}"
            style = STYLES.get(tag, "")
            if level == 1 and not doc_title:
                doc_title = heading_match.group(2).strip()
            html_parts.append(f'<{tag} style="{style}">{text}</{tag}>')
            i += 1
            continue

        # ── 비순서 목록 ───────────────────────────────────────
        if re.match(r"^[-*+]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*+]\s+", lines[i]):
                item_text = _inline_styles(re.sub(r"^[-*+]\s+", "", lines[i]))
                items.append(f'<li style="{STYLES["li"]}">{item_text}</li>')
                i += 1
            html_parts.append(f'<ul style="{STYLES["ul"]}">{"".join(items)}</ul>')
            continue

        # ── 순서 목록 ─────────────────────────────────────────
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                item_text = _inline_styles(re.sub(r"^\d+\.\s+", "", lines[i]))
                items.append(f'<li style="{STYLES["li"]}">{item_text}</li>')
                i += 1
            html_parts.append(f'<ol style="{STYLES["ul"]}">{"".join(items)}</ol>')
            continue

        # ── 빈 줄 스킵 ────────────────────────────────────────
        if not line.strip():
            i += 1
            continue

        # ── 일반 단락 ─────────────────────────────────────────
        html_parts.append(f'<p style="{STYLES["p"]}">{_inline_styles(line)}</p>')
        i += 1

    body_content = "\n".join(html_parts)
    page_title = doc_title or "Weekly Flash"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{_escape_html(page_title)}</title>
</head>
<body style="{STYLES["body"]}">
{body_content}
<p style="{STYLES["footer"]}">이 메일은 Confluence Intelligence Agent가 자동 생성했습니다.</p>
</body>
</html>"""


# ─── 검증 함수 ───────────────────────────────────────────────────────────

def validate_html(html: str) -> list[str]:
    """기본 HTML 구조 검증. 오류 목록 반환 (빈 리스트 = 정상)."""
    errors = []
    if len(html) < 200:
        errors.append("HTML 크기가 너무 작음 (< 200 bytes)")
    if "<html" not in html:
        errors.append("<html> 태그 없음")
    if "<body" not in html:
        errors.append("<body> 태그 없음")
    # 닫히지 않은 태그 검사 (기본 태그)
    for tag in ["h1", "h2", "p", "table", "tr", "td", "ul", "li"]:
        open_count = len(re.findall(rf"<{tag}[\s>]", html))
        close_count = len(re.findall(rf"</{tag}>", html))
        if open_count != close_count:
            errors.append(f"<{tag}> 태그 불일치 (열림: {open_count}, 닫힘: {close_count})")
    return errors


# ─── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="마크다운 → 이메일 HTML 변환")
    parser.add_argument("--input", "-i", required=True, help="입력 마크다운 파일")
    parser.add_argument("--output", "-o", help="출력 HTML 파일 (미지정 시 stdout)")
    parser.add_argument("--title", "-t", help="HTML <title> 태그 텍스트")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[ERROR] 입력 파일 없음: {in_path}", file=sys.stderr)
        sys.exit(1)

    try:
        md_text = in_path.read_text(encoding="utf-8")
        html = convert(md_text, title=args.title or "")
    except Exception as e:
        print(f"[ERROR] 변환 실패: {e}", file=sys.stderr)
        sys.exit(2)

    errors = validate_html(html)
    if errors:
        for err in errors:
            print(f"[WARN] {err}", file=sys.stderr)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"[OK] HTML 저장 완료: {out_path} ({len(html)} bytes)")
    else:
        print(html)


if __name__ == "__main__":
    main()
