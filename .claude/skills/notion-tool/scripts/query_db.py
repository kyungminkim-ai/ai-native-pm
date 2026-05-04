#!/usr/bin/env python3
"""
Notion 데이터베이스 조회 / 아이템 업데이트

사용법:
  # DB 조회
  python3 query_db.py --db-id DATABASE_ID [--filter '{...}'] [--sort '{...}'] [--limit 20]

  # 아이템 속성 업데이트
  python3 query_db.py --update-page-id PAGE_ID --properties '{...}'
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from client import request, extract_page_id, get_plain_text, get_page_title


def format_property(prop: dict) -> str:
    """Notion property → 읽기 쉬운 문자열"""
    ptype = prop.get("type", "")
    val = prop.get(ptype, None)

    if val is None:
        return ""
    if ptype == "title":
        return get_plain_text(val)
    if ptype == "rich_text":
        return get_plain_text(val)
    if ptype == "number":
        return str(val) if val is not None else ""
    if ptype == "select":
        return (val or {}).get("name", "") if val else ""
    if ptype == "multi_select":
        return ", ".join(s.get("name", "") for s in (val or []))
    if ptype == "status":
        return (val or {}).get("name", "")
    if ptype == "date":
        if not val:
            return ""
        start = val.get("start", "")
        end = val.get("end", "")
        return f"{start} ~ {end}" if end else start
    if ptype == "checkbox":
        return "✅" if val else "☐"
    if ptype == "url":
        return val or ""
    if ptype == "email":
        return val or ""
    if ptype == "people":
        return ", ".join((p.get("name") or p.get("id", "")) for p in (val or []))
    if ptype == "relation":
        return f"{len(val)}개 연결됨" if val else ""
    if ptype == "formula":
        ftype = val.get("type", "")
        return str(val.get(ftype, ""))
    if ptype == "rollup":
        return str(val.get("number", val.get("array", "")))
    if ptype == "files":
        return ", ".join(
            (f.get("file") or f.get("external") or {}).get("url", f.get("name", ""))
            for f in (val or [])
        )
    return str(val)


def query_database(db_id: str, filter_obj: dict = None,
                   sort_obj: dict = None, limit: int = 50) -> dict:
    db_id = extract_page_id(db_id)
    payload = {"page_size": min(limit, 100)}
    if filter_obj:
        payload["filter"] = filter_obj
    if sort_obj:
        payload["sorts"] = sort_obj if isinstance(sort_obj, list) else [sort_obj]

    all_results = []
    cursor = None
    while len(all_results) < limit:
        if cursor:
            payload["start_cursor"] = cursor
        data = request("POST", f"/databases/{db_id}/query", json=payload)
        results = data.get("results", [])
        all_results.extend(results)
        if not data.get("has_more") or len(all_results) >= limit:
            break
        cursor = data.get("next_cursor")

    formatted = []
    for page in all_results[:limit]:
        title = get_page_title(page)
        props_summary = {}
        for key, prop in page.get("properties", {}).items():
            if prop.get("type") == "title":
                continue  # 이미 title로 표시
            val = format_property(prop)
            if val:
                props_summary[key] = val

        formatted.append({
            "id": page["id"],
            "title": title,
            "url": page.get("url", ""),
            "last_edited": page.get("last_edited_time", "")[:10],
            "properties": props_summary,
        })

    return {
        "database_id": db_id,
        "total": len(formatted),
        "results": formatted,
    }


def update_page_properties(page_id: str, properties: dict) -> dict:
    page_id = extract_page_id(page_id)
    payload = {"properties": properties}
    page = request("PATCH", f"/pages/{page_id}", json=payload)
    return {
        "id": page["id"],
        "title": get_page_title(page),
        "url": page.get("url", ""),
    }


def main():
    parser = argparse.ArgumentParser()
    # 조회 모드
    parser.add_argument("--db-id", default=None, help="Notion DB ID")
    parser.add_argument("--filter", default=None, help="Notion filter JSON")
    parser.add_argument("--sort", default=None, help="Notion sort JSON")
    parser.add_argument("--limit", type=int, default=50)
    # 업데이트 모드
    parser.add_argument("--update-page-id", default=None, help="업데이트할 페이지 ID")
    parser.add_argument("--properties", default=None, help="업데이트할 properties JSON")
    args = parser.parse_args()

    if args.update_page_id:
        if not args.properties:
            print("[ERROR] --properties 가 필요합니다.", file=sys.stderr)
            sys.exit(1)
        props = json.loads(args.properties)
        result = update_page_properties(args.update_page_id, props)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not args.db_id:
        print("[ERROR] --db-id 또는 --update-page-id 가 필요합니다.", file=sys.stderr)
        sys.exit(1)

    filter_obj = json.loads(args.filter) if args.filter else None
    sort_obj = json.loads(args.sort) if args.sort else None

    result = query_database(args.db_id, filter_obj, sort_obj, args.limit)

    # output 저장
    out_path = Path("output/notion_db_query.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
