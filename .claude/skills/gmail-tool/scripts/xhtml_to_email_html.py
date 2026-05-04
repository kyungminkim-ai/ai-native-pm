"""
gmail-tool — Confluence Storage XHTML → 이메일 인라인 CSS HTML 변환기

Confluence 페이지 원본 구조를 그대로 보존하고 이메일 클라이언트 호환 스타일만 입힌다.
LLM이 본문을 재작성하지 않는 것이 원칙.

사용법:
  python3 xhtml_to_email_html.py \
    --input output/source_page.xhtml \
    --title "페이지 제목" \
    --source-url "https://..." \
    --output output/final_email.html

  # JSON 형식 입력도 지원 (fetch_page.py --json 출력)
  python3 xhtml_to_email_html.py --input output/source_page.xhtml --output output/final_email.html
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ─── 인라인 스타일 정의 ──────────────────────────────────────────────────

S = {
    "wrap":       "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;font-size:14px;line-height:1.7;color:#333333;max-width:700px;margin:0 auto;padding:24px 16px;background:#ffffff;",
    "title":      "font-size:22px;font-weight:700;color:#172B4D;border-bottom:3px solid #0052CC;padding-bottom:10px;margin:0 0 20px 0;",
    "h1":         "font-size:20px;font-weight:700;color:#172B4D;border-bottom:2px solid #0052CC;padding-bottom:8px;margin:28px 0 14px 0;",
    "h2":         "font-size:16px;font-weight:700;color:#0052CC;margin:24px 0 10px 0;",
    "h3":         "font-size:14px;font-weight:700;color:#253858;margin:18px 0 8px 0;",
    "h4":         "font-size:13px;font-weight:700;color:#42526E;margin:14px 0 6px 0;",
    "p":          "margin:0 0 8px 0;",
    "ul":         "margin:0 0 10px 0;padding-left:20px;",
    "ol":         "margin:0 0 10px 0;padding-left:20px;",
    "li":         "margin:3px 0;",
    "table":      "border-collapse:collapse;width:100%;margin:0 0 16px 0;font-size:13px;",
    "th":         "background:#F4F5F7;color:#172B4D;font-weight:700;text-align:left;padding:8px 12px;border:1px solid #DFE1E6;",
    "td":         "padding:7px 12px;border:1px solid #DFE1E6;vertical-align:top;",
    "blockquote": "background:#F4F5F7;border-left:4px solid #0052CC;margin:0 0 12px 0;padding:10px 14px;color:#5E6C84;",
    "hr":         "border:none;border-top:1px solid #DFE1E6;margin:20px 0;",
    "a":          "color:#0052CC;text-decoration:none;",
    "code":       "background:#F4F5F7;border-radius:3px;padding:2px 4px;font-family:monospace;font-size:12px;color:#172B4D;",
    "footer":     "font-size:11px;color:#97A0AF;margin-top:32px;padding-top:12px;border-top:1px solid #DFE1E6;",
}

# ─── Notion 콜아웃 스타일 정의 ───────────────────────────────────────────

# Confluence panelIcon → (emoji, 배경색, 왼쪽 보더색)
CALLOUT_PRESETS = {
    ":info:":       ("ℹ️",  "#EAF3FF", "#0052CC"),
    ":check:":      ("✅",  "#EDFAF1", "#36B37E"),
    ":warning:":    ("⚠️",  "#FFFAE6", "#FFAB00"),
    ":error:":      ("❌",  "#FFF0F0", "#DE350B"),
    ":tip:":        ("💡",  "#FFFDF0", "#FF991F"),
    ":note:":       ("📝",  "#F3F0FF", "#6554C0"),
    ":star:":       ("⭐",  "#FFFDF0", "#FF991F"),
    ":question:":   ("❓",  "#F4F5F7", "#42526E"),
}
CALLOUT_DEFAULT = ("💬", "#F4F5F7", "#42526E")


def _callout_html(icon_name: str, bg_color: str, content: str) -> str:
    """Notion 스타일 콜아웃을 이메일 호환 table 레이아웃으로 생성."""
    emoji, bg, border = CALLOUT_PRESETS.get(icon_name, CALLOUT_DEFAULT)
    # bgColor 파라미터가 있으면 배경색 우선 적용 (단, 기본 회색이면 preset 색상 사용)
    if bg_color and bg_color.upper() not in ("#F4F5F7", "#FFFFFF", ""):
        bg = bg_color

    return (
        f'<table cellpadding="0" cellspacing="0" style="width:100%;border-collapse:collapse;'
        f'background:{bg};border-radius:6px;border-left:4px solid {border};margin:0 0 16px 0;">'
        f'<tr>'
        f'<td style="width:36px;padding:12px 6px 12px 14px;vertical-align:top;'
        f'font-size:18px;line-height:1.4;">{emoji}</td>'
        f'<td style="padding:12px 14px 12px 6px;vertical-align:top;">{content}</td>'
        f'</tr></table>'
    )


# ─── 변환 함수 ───────────────────────────────────────────────────────────

def convert(xhtml: str, title: str = "", source_url: str = "") -> str:
    """Confluence Storage XHTML을 이메일 HTML로 변환."""

    # ── Step 1: 패널 내용만 미리 추출해 플레이스홀더로 교체 ─────────────────
    # (스타일 주입 후 덮어써지지 않도록 나중에 복원)
    panel_store: dict[str, str] = {}

    def stash_panel(m):
        raw = m.group(0)
        icon_match = re.search(r'<ac:parameter ac:name="panelIcon">(.*?)</ac:parameter>', raw)
        bg_match   = re.search(r'<ac:parameter ac:name="bgColor">(.*?)</ac:parameter>', raw)
        inner      = re.search(r'<ac:rich-text-body>(.*?)</ac:rich-text-body>', raw, re.DOTALL)
        if not inner:
            return ""
        icon_name = icon_match.group(1) if icon_match else ""
        bg_color  = bg_match.group(1) if bg_match else ""
        key = f"__PANEL_{len(panel_store)}__"
        # rich-text-body 내용은 나중에 스타일 주입 후 콜아웃으로 감쌈
        panel_store[key] = (icon_name, bg_color, inner.group(1))
        return key

    xhtml = re.sub(
        r'<ac:structured-macro ac:name="panel"[^>]*>.*?</ac:structured-macro>',
        stash_panel, xhtml, flags=re.DOTALL,
    )

    # ── Step 2: 나머지 Confluence 전용 태그/매크로 제거 ──────────────────────
    xhtml = re.sub(r'<ac:structured-macro[^>]*>.*?</ac:structured-macro>', '', xhtml, flags=re.DOTALL)
    xhtml = re.sub(r'<ac:[^>]+>.*?</ac:[^>]+>', '', xhtml, flags=re.DOTALL)
    xhtml = re.sub(r'<ac:[^/][^>]*/>', '', xhtml)
    xhtml = re.sub(r'<ri:[^>]*/>', '', xhtml)

    # ── Step 3: Confluence 전용 속성 제거 ────────────────────────────────────
    for attr in ['local-id', 'ac:local-id', 'ac:macro-id', 'ac:schema-version',
                 'data-layout', 'data-table-width', 'ac:name', 'ac:parameter']:
        xhtml = re.sub(rf'\s+{re.escape(attr)}="[^"]*"', '', xhtml)
    xhtml = re.sub(r'\s+data-[a-z\-]+="[^"]*"', '', xhtml)

    # ── Step 4: colgroup 제거 ────────────────────────────────────────────────
    xhtml = re.sub(r'<colgroup>.*?</colgroup>', '', xhtml, flags=re.DOTALL)

    # ── Step 5: 빈 p 태그 제거 ──────────────────────────────────────────────
    xhtml = re.sub(r'<p[^>]*>\s*(?:&nbsp;)?\s*</p>', '', xhtml)

    # ── Step 6: 기존 style 속성 제거 ─────────────────────────────────────────
    xhtml = re.sub(r'\s+style="[^"]*"', '', xhtml)

    # ── Step 7: 인라인 CSS 주입 ──────────────────────────────────────────────
    def inject_style(tag, style_key=None):
        s = S.get(style_key or tag, "")
        return f' style="{s}"' if s else ""

    html = xhtml
    for tag in ["h1", "h2", "h3", "h4", "ul", "ol", "li", "blockquote"]:
        html = re.sub(
            rf"<{tag}(\s[^>]*)?>",
            lambda m, t=tag: f"<{t}{inject_style(t)}>",
            html, flags=re.IGNORECASE,
        )

    html = re.sub(r"<p(\s[^>]*)?>",
                  lambda m: f'<p{inject_style("p")}>', html, flags=re.IGNORECASE)
    html = re.sub(r"<table(\s[^>]*)?>",
                  lambda m: f'<table{inject_style("table")}>', html, flags=re.IGNORECASE)
    html = re.sub(r"<th(\s[^>]*)?>",
                  lambda m: f'<th{inject_style("th")}>', html, flags=re.IGNORECASE)
    html = re.sub(r"<td(\s[^>]*)?>",
                  lambda m: f'<td{inject_style("td")}>', html, flags=re.IGNORECASE)
    html = re.sub(r"<blockquote(\s[^>]*)?>",
                  lambda m: f'<blockquote{inject_style("blockquote")}>', html, flags=re.IGNORECASE)
    html = re.sub(r"<hr(\s[^>]*)?/?>",
                  f'<hr style="{S["hr"]}" />', html, flags=re.IGNORECASE)
    html = re.sub(r"<a(\s[^>]*)?>",
                  lambda m: f'<a{m.group(1) or ""} style="{S["a"]}">', html, flags=re.IGNORECASE)
    html = re.sub(r"<code(\s[^>]*)?>",
                  lambda m: f'<code{inject_style("code")}>', html, flags=re.IGNORECASE)

    # ── Step 8: 플레이스홀더를 Notion 콜아웃으로 복원 ────────────────────────
    # 패널 내 rich-text-body도 스타일 주입 후 처리
    for key, (icon_name, bg_color, raw_inner) in panel_store.items():
        # 패널 내 콘텐츠에도 인라인 스타일 주입
        inner_html = raw_inner
        for tag in ["h1", "h2", "h3", "h4", "ul", "ol", "li"]:
            inner_html = re.sub(
                rf"<{tag}(\s[^>]*)?>",
                lambda m, t=tag: f"<{t}{inject_style(t)}>",
                inner_html, flags=re.IGNORECASE,
            )
        inner_html = re.sub(r"<p(\s[^>]*)?>",
                            lambda m: f'<p{inject_style("p")}>', inner_html, flags=re.IGNORECASE)
        inner_html = re.sub(r'\s+(?:local-id|ac:local-id)="[^"]*"', '', inner_html)
        html = html.replace(key, _callout_html(icon_name, bg_color, inner_html))

    # 8. 푸터 구성
    footer_parts = ["Confluence Intelligence Agent 자동 변환 (이메일 발송용)"]
    if source_url:
        footer_parts.append(f'<a href="{source_url}" style="{S["a"]}">Confluence 원문 보기</a>')
    footer = " &nbsp;·&nbsp; ".join(footer_parts)

    page_title = title or "Weekly Flash"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1.0" />
  <title>{page_title}</title>
</head>
<body>
<div style="{S['wrap']}">
  <h1 style="{S['title']}">{page_title}</h1>
  {html}
  <p style="{S['footer']}">{footer}</p>
</div>
</body>
</html>"""


# ─── 검증 ────────────────────────────────────────────────────────────────

def validate(html: str) -> list[str]:
    errors = []
    if len(html) < 500:
        errors.append("HTML 크기 너무 작음 (< 500 bytes)")
    if "<body" not in html:
        errors.append("<body> 태그 없음")
    for tag in ["h1", "h2", "table", "tr"]:
        opens = len(re.findall(rf"<{tag}[\s>]", html, re.IGNORECASE))
        closes = len(re.findall(rf"</{tag}>", html, re.IGNORECASE))
        if opens != closes:
            errors.append(f"<{tag}> 태그 불일치 (열림:{opens} 닫힘:{closes})")
    return errors


# ─── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Confluence XHTML → 이메일 HTML 변환")
    parser.add_argument("--input", "-i", required=True, help="입력 파일 (XHTML 텍스트 또는 fetch_page.py --json 출력)")
    parser.add_argument("--output", "-o", help="출력 HTML 파일 (미지정 시 stdout)")
    parser.add_argument("--title", "-t", help="페이지 제목 (JSON 입력 시 자동 추출)")
    parser.add_argument("--source-url", "-u", help="Confluence 원문 URL (푸터 링크용)")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[ERROR] 입력 파일 없음: {in_path}", file=sys.stderr)
        sys.exit(1)

    raw = in_path.read_text(encoding="utf-8")
    title = args.title or ""
    source_url = args.source_url or ""

    # JSON 형식 지원 (fetch_page.py --json 출력)
    if raw.strip().startswith("{"):
        try:
            data = json.loads(raw)
            xhtml = data.get("content", raw)
            if not title:
                title = data.get("title", "")
            if not source_url:
                source_url = data.get("url", "")
        except json.JSONDecodeError:
            xhtml = raw
    else:
        xhtml = raw

    try:
        html = convert(xhtml, title=title, source_url=source_url)
    except Exception as e:
        print(f"[ERROR] 변환 실패: {e}", file=sys.stderr)
        sys.exit(2)

    errors = validate(html)
    for err in errors:
        print(f"[WARN] {err}", file=sys.stderr)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"[OK] HTML 저장 완료: {out_path} ({len(html):,} bytes)")
    else:
        print(html)


if __name__ == "__main__":
    main()
