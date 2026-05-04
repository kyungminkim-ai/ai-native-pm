#!/usr/bin/env python3
"""
Notion 페이지/DB 검색
사용법: python3 search.py --query "검색어" [--filter page|database] [--limit 10]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from client import request


def search(query: str, filter_type: str = None, limit: int = 10) -> dict:
    payload = {
        "query": query,
        "page_size": min(limit, 100),
        "sort": {"direction": "descending", "timestamp": "last_edited_time"},
    }
    if filter_type in ("page", "database"):
        payload["filter"] = {"value": filter_type, "property": "object"}

    data = request("POST", "/search", json=payload)

    results = []
    for obj in data.get("results", []):
        obj_type = obj.get("object", "")
        title = ""

        if obj_type == "page":
            props = obj.get("properties", {})
            for prop in props.values():
                if prop.get("type") == "title":
                    title = "".join(t.get("plain_text", "") for t in prop.get("title", []))
                    break
            # DB child page의 경우 title이 없으면 properties에서 찾기
            if not title:
                # plain page
                for key in ["title", "Name"]:
                    if key in props:
                        p = props[key]
                        if p.get("type") == "title":
                            title = "".join(t.get("plain_text", "") for t in p.get("title", []))

        elif obj_type == "database":
            title_list = obj.get("title", [])
            title = "".join(t.get("plain_text", "") for t in title_list)

        url = obj.get("url", "")
        last_edited = obj.get("last_edited_time", "")[:10]
        parent = obj.get("parent", {})
        parent_type = parent.get("type", "")

        results.append({
            "id": obj.get("id", ""),
            "title": title or "(제목 없음)",
            "type": obj_type,
            "parent_type": parent_type,
            "url": url,
            "last_edited": last_edited,
        })

    return {
        "query": query,
        "total": len(results),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--filter", choices=["page", "database"], default=None)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    result = search(args.query, args.filter, args.limit)

    # output 저장
    out_path = Path("output/notion_context.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
