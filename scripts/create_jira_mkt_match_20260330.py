"""
MKT-MATCH 정기미팅 (2026-03-31) 회의록 기반 Task 티켓 일괄 생성
프로젝트: MEMB, 이슈 타입: Task (ID: 10006)
Assignee: 김경민 (712020:9bbd1f66-a6e3-4385-957b-56995ea34f89)
"""

import os
import json
import requests
from requests.auth import HTTPBasicAuth

EMAIL = os.environ["CONFLUENCE_EMAIL"]
TOKEN = os.environ["CONFLUENCE_API_TOKEN"]
BASE_URL = "https://musinsa-oneteam.atlassian.net"
AUTH = HTTPBasicAuth(EMAIL, TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

PROJECT_KEY = "MEMB"
ISSUE_TYPE_ID = "10006"  # Task
ASSIGNEE_ID = "712020:9bbd1f66-a6e3-4385-957b-56995ea34f89"


def make_description(background: str, tasks: list[str], notes: list[str] = None) -> dict:
    content = []

    content.append({
        "type": "heading",
        "attrs": {"level": 3},
        "content": [{"type": "text", "text": "배경"}]
    })
    content.append({
        "type": "paragraph",
        "content": [{"type": "text", "text": background}]
    })

    content.append({
        "type": "heading",
        "attrs": {"level": 3},
        "content": [{"type": "text", "text": "작업 내용"}]
    })
    content.append({
        "type": "bulletList",
        "content": [
            {
                "type": "listItem",
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": t}]}]
            }
            for t in tasks
        ]
    })

    if notes:
        content.append({
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "참고 사항"}]
        })
        content.append({
            "type": "bulletList",
            "content": [
                {
                    "type": "listItem",
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": n}]}]
                }
                for n in notes
            ]
        })

    return {"type": "doc", "version": 1, "content": content}


TICKETS = [
    {
        "summary": "[MKT-MATCH] [MSS] 캠페인 메타메시지 Phase1 — 마케팅 실무자 리뷰 및 기존 파이프라인 종료 일정 확인",
        "priority": "High",
        "duedate": "2026-04-04",
        "background": "2026-03-31 MKT-MATCH 정기미팅에서 MSS 캠페인 메타메시지 Phase1 개발이 4/6 완료 예정이며, 4/7 11시 Push부터 변경된 시스템으로 이관 예정임이 공유되었다.",
        "tasks": [
            "마케팅팀 실무자 대상 리뷰 진행 (Phase1 변경 사항 및 영향 범위 공유)",
            "기존 파이프라인 종료 일정 확인 및 합의",
            "이관 전 QA 체크리스트 준비",
        ],
        "notes": [
            "4/6 개발 완료 후 4/7 11시 Push부터 변경된 시스템 적용 예정",
            "마케팅팀 실무자가 새 시스템 사용에 불편함 없도록 사전 리뷰 필수",
        ],
    },
    {
        "summary": "[MKT-MATCH] [Audience API] 출석체크 이외 2Q 보상시스템 연동 알림톡 도메인 확인",
        "priority": "Medium",
        "duedate": "2026-04-04",
        "background": "출석체크 세그먼트 적용 관련 개발이 금주 완료 예정이며, 동일한 세그먼트/API를 활용해 출석체크 이외 도메인에도 적용할 수 있는지 확인이 필요하다.",
        "tasks": [
            "26-2Q 내 보상시스템 관련 연동하려는 알림톡 도메인 목록 확인",
            "각 도메인에 동일 세그먼트/API 활용 가능 여부 검토",
            "알림톡 도메인별 적용 우선순위 정리 및 마케팅팀과 공유",
        ],
        "notes": [
            "출석체크 이외 도메인 예시: 알림받기 등 보상시스템 관련 항목",
            "26-2Q 내 적용을 목표로 도메인 확정 필요",
        ],
    },
    {
        "summary": "[MKT-MATCH] [29CM 캠페인 메타메시지] 세부기획서 포함 PRD 리뷰 진행",
        "priority": "High",
        "duedate": "2026-03-31",
        "background": "29CM 캠페인 메타메시지 과제의 2-Pager 리뷰가 완료되었으며, 방향성과 작업 범위에 대한 마케팅팀 싱크가 끝났다. 3/31 세부기획서 포함한 PRD 리뷰를 진행해야 한다.",
        "tasks": [
            "세부기획서 포함한 PRD 리뷰 진행 (3/31)",
            "리뷰 후 개발팀과 일정 협의 및 공유",
        ],
        "notes": [
            "방향성과 작업 범위 싱크는 마케팅팀(신하지님, 한재하님, 이상인님)과 완료",
            "PRD 리뷰 후 개발팀 일정 우선 연락 후 공유 예정",
        ],
    },
    {
        "summary": "[MKT-MATCH] [29CM 캠페인 메타메시지] 캠페인 메타메시지 발칙 일정 마케팅팀 공유",
        "priority": "High",
        "duedate": "2026-04-04",
        "background": "29CM 캠페인 메타메시지 과제의 반칙(발칙) 일정과 적용 일정을 마케팅팀에 공유해야 한다. MATCH → 마케팅 방향의 커뮤니케이션 항목이다.",
        "tasks": [
            "캠페인 메타메시지 반칙 일정 확정",
            "적용 일정 및 범위 마케팅팀에 공유 (MATCH → 마케팅)",
        ],
        "notes": [
            "마케팅팀에서 MATCH 최적화 적용할 시간대 지정 및 공유 수신 대기 중 (마케팅 → MATCH)",
            "양방향 커뮤니케이션 항목으로, 마케팅팀 응신 후 시간대 반영 필요",
        ],
    },
    {
        "summary": "[MKT-MATCH] [라이브커머스 채팅] 발송 결과 정리 및 차주 공유",
        "priority": "Medium",
        "duedate": "2026-04-07",
        "background": "라이브커머스 채팅의 발송 결과를 차주(4/7 기준)까지 정리하여 미팅에서 공유하기로 했다.",
        "tasks": [
            "라이브커머스 채팅 발송 결과 데이터 수집 및 정리",
            "주요 지표(CTR, 발송량 등) 분석",
            "다음 주 MKT-MATCH 정기미팅에서 결과 공유",
        ],
        "notes": [
            "Due: 차주 정기미팅 전까지 자료 준비",
        ],
    },
    {
        "summary": "[MKT-MATCH] [29CM AI Assistant] 2-Pager 리뷰",
        "priority": "High",
        "duedate": "2026-04-03",
        "background": "29CM AI Assistant 과제의 방향성 싱크가 완료되었다. 마케팅기획팀 담당자의 방향성 싱크가 끝났으며, AI Assistant 구축에 활용할 데이터 소스(Semantic Layer) 관련 Data Intelligence팀, Personalization팀, 마케팅기획팀과 협의 및 제공 범위 구체화가 필요하다.",
        "tasks": [
            "2-Pager 리뷰 완료 (4/3까지)",
            "AI Assistant 구축에 활용할 데이터 소스(Semantic Layer) 관련 협의 내용 반영",
            "Data Intelligence팀, Personalization팀, 마케팅기획팀과 제공 범위 구체화",
        ],
        "notes": [
            "Due: 2026-04-03",
            "PRD 리뷰 및 개발 일정 산출은 4/10까지 별도 진행",
        ],
    },
    {
        "summary": "[MKT-MATCH] [MSS] 캠페인 메타메시지 카피/메시지 작성 자동화 2-Pager 리뷰",
        "priority": "High",
        "duedate": "2026-04-03",
        "background": "MSS 캠페인 메타메시지 중 카피/메시지 작성 자동화 과제의 스코프 정리 후 라인 결재 단계이다. 2-Pager 리뷰를 4/3까지 완료해야 한다.",
        "tasks": [
            "2-Pager 리뷰 완료 (4/3까지)",
            "세일즈툴 자동화 이슈 관련 스코프 정리 내용 반영 확인",
        ],
        "notes": [
            "Due: 2026-04-03",
            "PRD 리뷰 및 개발 일정 산출은 4/10까지 별도 진행",
        ],
    },
    {
        "summary": "[MKT-MATCH] [29CM AI Assistant] PRD 리뷰 및 개발 일정 산출",
        "priority": "Medium",
        "duedate": "2026-04-10",
        "background": "29CM AI Assistant 과제의 2-Pager 리뷰 완료 후, PRD 리뷰 및 개발 일정 산출을 4/10까지 완료해야 한다.",
        "tasks": [
            "PRD 리뷰 진행",
            "개발팀과 일정 협의 및 개발 일정 산출",
            "산출된 일정 관련 이해관계자에게 공유",
        ],
        "notes": [
            "Due: 2026-04-10",
            "2-Pager 리뷰(4/3 완료) 선행 후 진행",
        ],
    },
    {
        "summary": "[MKT-MATCH] [MSS] 카피/메시지 작성 자동화 PRD 리뷰 및 개발 일정 산출",
        "priority": "Medium",
        "duedate": "2026-04-10",
        "background": "MSS 캠페인 메타메시지 카피/메시지 작성 자동화 과제의 2-Pager 리뷰 완료 후, PRD 리뷰 및 개발 일정 산출을 4/10까지 완료해야 한다.",
        "tasks": [
            "PRD 리뷰 진행",
            "개발팀과 일정 협의 및 개발 일정 산출",
            "산출된 일정 관련 이해관계자에게 공유",
        ],
        "notes": [
            "Due: 2026-04-10",
            "2-Pager 리뷰(4/3 완료) 선행 후 진행",
        ],
    },
    {
        "summary": "[MKT-MATCH] [DFC] 이관 범위 및 Dynamic Frequency Capping 실험 설계 라인 일정 수립",
        "priority": "Medium",
        "duedate": None,
        "background": "Tech 내부적으로 Dynamic Frequency Capping을 통한 비즈니스 임팩트 도출 방식 라인 중이며, Action-based CRM 캠페인 중 일부 캠페인의 MATCH 이관 검토 및 분석이 진행 중이다. ABC 현황 분석은 완료되었으며, 이관 범위 및 DFC 실험 설계 라인 일정 수립이 필요하다.",
        "tasks": [
            "MATCH 이관 대상 ABC 캠페인 범위 확정",
            "Dynamic Frequency Capping 실험 설계 방안 수립",
            "라인 결재를 위한 일정 계획 작성",
        ],
        "notes": [
            "ABC 현황 분석 완료 (3/31 기준)",
            "ABC 이관 관련 MEMB-404~409 티켓과 연계하여 진행",
        ],
    },
    {
        "summary": "[MKT-MATCH] [MATCH 데이터] 온보딩 생성 및 활용을 위한 세부 데이터 리스트업",
        "priority": "Medium",
        "duedate": None,
        "background": "MATCH 내 데이터 제공을 위한 세부 리스트 확인이 필요하다. 무신사 머신러닝 가입여부 이외의 MATCH 내 온보딩 생성 및 활용을 위한 세부 데이터를 리스트업해야 한다.",
        "tasks": [
            "(무신사 머신러닝 가입여부 이외) MATCH 내 온보딩 생성 및 활용을 위한 세부 데이터 리스트업",
            "Braze 등을 통해 이미 활용 중인 데이터가 있다면 별도 확인",
            "시나리오 이상을 해야 하지만 Braze에 없는 데이터가 있다면 구분하여 전달 요청",
        ],
        "notes": [
            "3/24 Weekly에서 요청된 사항",
            "Braze에 이미 있는 데이터와 없는 데이터를 구분하여 정리 필요",
        ],
    },
    {
        "summary": "[MKT-MATCH] [MATCH 데이터] Braze 활용 데이터 확인 및 미보유 데이터 구분 전달",
        "priority": "Medium",
        "duedate": None,
        "background": "MATCH 데이터 리스트업 과정에서 Braze 등 현재 툴을 통해 이미 활용 중인 데이터와 그렇지 않은 데이터를 구분하여 관련 팀에 전달해야 한다.",
        "tasks": [
            "Braze 등 현재 활용 중인 데이터 목록 확인",
            "시나리오 구현에 필요하지만 현재 보유하지 않은 데이터 목록 구분",
            "구분된 데이터 리스트 관련 팀에 전달 요청",
        ],
        "notes": [
            "MATCH 데이터 리스트업 티켓과 병행 진행",
            "없는 데이터는 별도 수집/연동 방안 검토 필요",
        ],
    },
]


def create_ticket(ticket: dict) -> dict:
    fields = {
        "project": {"key": PROJECT_KEY},
        "summary": ticket["summary"],
        "issuetype": {"id": ISSUE_TYPE_ID},
        "priority": {"name": ticket["priority"]},
        "assignee": {"id": ASSIGNEE_ID},
        "description": make_description(
            ticket["background"], ticket["tasks"], ticket.get("notes")
        ),
    }
    if ticket.get("duedate"):
        fields["duedate"] = ticket["duedate"]

    resp = requests.post(
        f"{BASE_URL}/rest/api/3/issue",
        auth=AUTH,
        headers=HEADERS,
        json={"fields": fields},
    )
    resp.raise_for_status()
    return resp.json()


def main():
    results = []
    for i, ticket in enumerate(TICKETS, 1):
        print(f"[{i}/{len(TICKETS)}] 생성 중: {ticket['summary'][:60]}...")
        try:
            result = create_ticket(ticket)
            key = result.get("key", "?")
            url = f"{BASE_URL}/browse/{key}"
            print(f"  ✅ {key} → {url}")
            results.append({"key": key, "url": url, "summary": ticket["summary"]})
        except requests.HTTPError as e:
            print(f"  ❌ 실패: {e.response.status_code} — {e.response.text}")
            results.append({"key": None, "error": str(e), "summary": ticket["summary"]})

    output_path = "output/created_mkt_match_tickets.json"
    os.makedirs("output", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n📁 결과 저장: {output_path}")
    success = [r for r in results if r.get("key")]
    print(f"\n✅ 생성 완료: {len(success)}/{len(TICKETS)}개")
    for r in success:
        print(f"  - [{r['key']}] {r['summary'][:60]}")
        print(f"    {r['url']}")


if __name__ == "__main__":
    main()
