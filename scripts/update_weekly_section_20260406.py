"""
2026-04-06 Weekly 공유사항 — 16개 TM 티켓 Description append
각 티켓의 'Weekly 공유사항' 섹션에 이번 주 내용을 추가한다.
섹션이 없으면 Description 하단에 새로 생성한다.
"""

import os
import json
import requests
from requests.auth import HTTPBasicAuth

EMAIL    = os.environ["CONFLUENCE_EMAIL"]
TOKEN    = os.environ["CONFLUENCE_API_TOKEN"]
BASE_URL = "https://musinsa-oneteam.atlassian.net"
AUTH     = HTTPBasicAuth(EMAIL, TOKEN)
HEADERS  = {"Accept": "application/json", "Content-Type": "application/json"}

# ── 이번 주 업데이트 내용 ──────────────────────────────────────
UPDATES = {
    "TM-2664": [
        "PRD 작성 중: 세일즈푸시 전체 Flow + 최소 작업 범위 (ETA: 4/9)",
    ],
    "TM-2665": [
        "일정 산출 요청 (4월 착수 과제, 금주 중 일정 검토 필요)",
        "무신사와 비즈니스 로직 중 다르게 적용되는 영역 존재 → 관련 내용 검토 중",
        "엑셀 시트 정책, 최적화 로직 정책 별도 문서 작성 중 (ETA: 4/7)",
    ],
    "TM-2666": [
        "Inbox Optimizer 관련 분석 및 논의 (ETA: 4/10)",
        "ABC 일부 이관 후 최적화 방안 검토 (ETA: 4/10)",
        "배치 스케줄러 / Inbox 설계 Overview (4/8)",
        "Action-based CRM 코드 분석 및 정리 (ETA: 4/8)",
    ],
    "TM-2686": [
        "모델 설계 마무리 및 확정 (ETA: 4/7)",
    ],
    "TM-2689": [
        "A/B TEST 실행 예정 (화요일 발송)",
    ],
    "TM-2677": [
        "PRD 리뷰 (ETA: 4/6)",
    ],
    "TM-2688": [
        "작업 범위 및 진행 방식 논의 필요",
    ],
    "TM-2232": [
        "SRP 퍼널 배너 개선 진행 중",
    ],
    "TM-2659": [
        "백엔드팀과 운영 관련 결정 사항 논의",
        "실시간 파이프라인 작업",
    ],
    "TM-2690": [
        "PRD를 위한 사전 분석 중 (ETA: 4/10)",
        "MATCH Console Audience API 메뉴 추가 작업",
    ],
    "TM-2696": [
        "오프라인 테스트 진행 예정",
    ],
    "TM-2658": [
        "Lookalike Audience 2분기 과제범위 싱크 (4/7 미팅)",
    ],
    "TM-2657": [
        "진행 중 (Next Milestone: 4/27 오픈)",
    ],
    "TM-2667": [
        "필요한 데이터 스펙 정리 단계 (진행 중)",
    ],
    "TM-2692": [
        "데이터 사용성 확인 (ETA: 4/23)",
    ],
    "TM-2687": [
        "필요한 데이터 스펙 정리 단계 (진행 중)",
    ],
}

WEEKLY_SECTION_TITLE = "Weekly 공유사항"


def make_bullet_nodes(items: list[str]) -> list[dict]:
    return [
        {
            "type": "listItem",
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": item}]
            }]
        }
        for item in items
    ]


def make_weekly_section(items: list[str]) -> list[dict]:
    """새 Weekly 공유사항 섹션 ADF 노드 목록 반환"""
    return [
        {
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": WEEKLY_SECTION_TITLE}]
        },
        {
            "type": "bulletList",
            "content": make_bullet_nodes(items)
        }
    ]


def get_issue(key: str) -> dict:
    url = f"{BASE_URL}/rest/api/3/issue/{key}?fields=description,summary"
    r = requests.get(url, auth=AUTH, headers=HEADERS)
    r.raise_for_status()
    return r.json()


def update_description(key: str, new_desc: dict) -> bool:
    url = f"{BASE_URL}/rest/api/3/issue/{key}"
    payload = {"fields": {"description": new_desc}}
    r = requests.put(url, auth=AUTH, headers=HEADERS, json=payload)
    if r.status_code == 204:
        return True
    print(f"  ⚠️  PUT {key} 실패: {r.status_code} {r.text[:200]}")
    return False


def find_weekly_section_index(content: list[dict]) -> int:
    """'Weekly 공유사항' h2 heading의 인덱스 반환. 없으면 -1."""
    for i, node in enumerate(content):
        if (
            node.get("type") == "heading"
            and node.get("attrs", {}).get("level") == 2
            and any(
                c.get("text", "") == WEEKLY_SECTION_TITLE
                for c in node.get("content", [])
            )
        ):
            return i
    return -1


def append_to_weekly_section(content: list[dict], items: list[str]) -> list[dict]:
    """
    Weekly 공유사항 섹션이 있으면 해당 섹션 내 bulletList에 항목 append.
    없으면 맨 끝에 새 섹션 추가.
    """
    idx = find_weekly_section_index(content)
    new_content = list(content)

    if idx == -1:
        # 섹션 없음 → 하단에 추가
        new_content.extend(make_weekly_section(items))
        return new_content

    # 섹션 있음 → 섹션 바로 뒤의 bulletList에 append (없으면 새로 생성)
    # idx+1이 bulletList이면 거기에 추가, 아니면 idx+1 위치에 삽입
    if idx + 1 < len(new_content) and new_content[idx + 1].get("type") == "bulletList":
        existing_list = new_content[idx + 1]
        existing_list["content"].extend(make_bullet_nodes(items))
    else:
        new_content.insert(idx + 1, {
            "type": "bulletList",
            "content": make_bullet_nodes(items)
        })

    return new_content


def process_ticket(key: str, items: list[str]):
    print(f"\n{'─'*50}")
    print(f"🔄 {key}")
    try:
        issue = get_issue(key)
        summary = issue["fields"].get("summary", "")
        print(f"   {summary[:60]}")

        desc = issue["fields"].get("description")
        if desc is None:
            # Description 없음 → 새로 생성
            desc = {"type": "doc", "version": 1, "content": []}

        existing_content = desc.get("content", [])
        updated_content = append_to_weekly_section(existing_content, items)

        new_desc = {"type": "doc", "version": 1, "content": updated_content}
        ok = update_description(key, new_desc)
        if ok:
            print(f"   ✅ Weekly 공유사항 업데이트 완료 ({len(items)}개 항목)")
        return ok
    except requests.HTTPError as e:
        print(f"   ❌ HTTP 오류: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False


def main():
    print("=" * 50)
    print("📋 2026-04-06 Weekly 공유사항 일괄 업데이트")
    print(f"   대상 티켓: {len(UPDATES)}개")
    print("=" * 50)

    results = {"ok": [], "fail": []}
    for key, items in UPDATES.items():
        ok = process_ticket(key, items)
        (results["ok"] if ok else results["fail"]).append(key)

    print(f"\n{'='*50}")
    print(f"✅ 완료: {len(results['ok'])}개  |  ❌ 실패: {len(results['fail'])}개")
    if results["fail"]:
        print(f"   실패 티켓: {', '.join(results['fail'])}")

    # 결과 저장
    out_path = "output/weekly_update_result_20260406.json"
    os.makedirs("output", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"📁 결과: {out_path}")


if __name__ == "__main__":
    main()
