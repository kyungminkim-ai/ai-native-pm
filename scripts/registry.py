#!/usr/bin/env python3
"""
Cross-team Artifact Registry — pm-studio 루트 레벨 공유 레지스트리

산출물을 등록(register)하거나 조회(get/list)할 때 사용한다.
레지스트리 경로: output/_registry.json

사용법:
  # 등록
  python3 scripts/registry.py register --type prd --path prd-agent-system/output/prd_20260412_foo.md --topic "Campaign Meta Engine"
  python3 scripts/registry.py register --type redteam --path prd-agent-system/output/redteam_20260412_foo.md --topic "Campaign Meta Engine"
  python3 scripts/registry.py register --type flash --path pgm-agent-system/output/flash_20260412.md

  # 조회 (최신 항목)
  python3 scripts/registry.py get --type prd
  python3 scripts/registry.py get --type flash

  # 목록
  python3 scripts/registry.py list
  python3 scripts/registry.py list --type prd

  # 클리어 (특정 타입 최신 항목 제거)
  python3 scripts/registry.py clear --type prd
"""

import argparse
import json
import os
from datetime import datetime

REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output", "_registry.json"
)

VALID_TYPES = [
    "prd",          # 기능 PRD (최신 버전)
    "prd-data",     # 데이터 PRD
    "prd-v2",       # Generator-Verifier 1회차 보강본
    "prd-v3",       # Generator-Verifier 2회차 보강본
    "redteam",      # Red Team 질문지
    "two-pager",    # 2-Pager 문서
    "discovery",    # Discovery 분석 보고서
    "flash",        # Weekly Flash Report
    "meeting",      # 회의록
    "analysis",     # 데이터 분석 결과
    "design-spec",  # Figma 화면 설계서
]


def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return {}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(registry):
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def cmd_register(args):
    if args.type not in VALID_TYPES:
        print(f"[registry] 오류: 알 수 없는 타입 '{args.type}'. 허용: {VALID_TYPES}")
        return 1

    registry = load_registry()
    now = datetime.now().isoformat()

    # 기존 항목이 있으면 history에 보관 (최대 3개)
    if args.type in registry:
        existing = registry[args.type]
        history = existing.get("history", [])
        history.insert(0, {
            "path": existing["path"],
            "topic": existing.get("topic", ""),
            "registered_at": existing["registered_at"],
        })
        registry[args.type]["history"] = history[:3]  # 최근 3개만 유지

    registry[args.type] = {
        "path": args.path,
        "topic": args.topic or "",
        "registered_at": now,
        "history": registry.get(args.type, {}).get("history", []),
    }

    save_registry(registry)
    print(f"[registry] 등록 완료: {args.type} → {args.path}")
    return 0


def cmd_get(args):
    registry = load_registry()
    if args.type not in registry:
        print(f"[registry] 없음: {args.type}")
        return 1

    entry = registry[args.type]
    print(entry["path"])
    return 0


def cmd_list(args):
    registry = load_registry()
    if not registry:
        print("[registry] 비어 있음")
        return 0

    print("[registry] 현재 등록된 산출물:")
    for key, entry in registry.items():
        if args.type and key != args.type:
            continue
        topic = f" ({entry['topic']})" if entry.get("topic") else ""
        print(f"  {key:<14} → {entry['path']}{topic}")
        print(f"             등록: {entry['registered_at'][:10]}")
    return 0


def cmd_clear(args):
    registry = load_registry()
    if args.type not in registry:
        print(f"[registry] 없음: {args.type}")
        return 1
    del registry[args.type]
    save_registry(registry)
    print(f"[registry] 제거 완료: {args.type}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="pm-studio Cross-team Artifact Registry")
    subparsers = parser.add_subparsers(dest="command")

    # register
    reg = subparsers.add_parser("register", help="산출물 등록")
    reg.add_argument("--type", required=True, help="산출물 타입")
    reg.add_argument("--path", required=True, help="파일 경로 (pm-studio 루트 기준 상대경로)")
    reg.add_argument("--topic", default="", help="주제 (선택)")

    # get
    get = subparsers.add_parser("get", help="최신 경로 출력")
    get.add_argument("--type", required=True, help="산출물 타입")

    # list
    lst = subparsers.add_parser("list", help="전체 목록 출력")
    lst.add_argument("--type", default="", help="특정 타입만 필터")

    # clear
    clr = subparsers.add_parser("clear", help="항목 제거")
    clr.add_argument("--type", required=True, help="산출물 타입")

    args = parser.parse_args()

    if args.command == "register":
        return cmd_register(args)
    elif args.command == "get":
        return cmd_get(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "clear":
        return cmd_clear(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    exit(main())
