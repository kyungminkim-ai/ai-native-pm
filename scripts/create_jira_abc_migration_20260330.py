"""
ABC 이관 관련 Jira Task 티켓 일괄 생성
회의: 2026-03-30 Action-based CRM 현황 공유
프로젝트: MEMB, 이슈 타입: Task (ID: 10006)
"""

import os
import json
import requests
from requests.auth import HTTPBasicAuth

# ── 인증 설정 ──────────────────────────────────────────────
EMAIL = os.environ["CONFLUENCE_EMAIL"]
TOKEN = os.environ["CONFLUENCE_API_TOKEN"]
BASE_URL = "https://musinsa-oneteam.atlassian.net"
AUTH = HTTPBasicAuth(EMAIL, TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

PROJECT_KEY = "MEMB"
ISSUE_TYPE_ID = "10006"  # Task


def make_description(background: str, tasks: list[str], notes: list[str]) -> dict:
    """ADF 형식 description 생성"""
    content = []

    # 배경 섹션
    content.append({
        "type": "heading",
        "attrs": {"level": 3},
        "content": [{"type": "text", "text": "배경"}]
    })
    content.append({
        "type": "paragraph",
        "content": [{"type": "text", "text": background}]
    })

    # 작업 내용 섹션
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

    # 참고 사항 섹션
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


# ── 티켓 정의 ──────────────────────────────────────────────
TICKETS = [
    {
        "summary": "[ABC 이관] Ground Rule 및 이관 범위 문서 정리 + 사전 미팅 진행",
        "priority": "High",
        "background": "2026-03-30 Action-based CRM 현황 공유 회의에서 API 트리거 방식으로의 마이그레이션 우선 추진이 결정되었다. 이관 전에 반드시 Ground Rule과 이관 범위를 문서화해야 개발팀(김준탁 Daniel)이 Job으로 옮겨올 때 제약 사항을 정의할 수 있다.",
        "tasks": [
            "현재 캠페인 구분(비정상적 구분)의 목적 및 히스토리 파악",
            "시간 변경, 캠페인 시기 등 이슈 발생 시 지킬 Ground Rule 정의 (예: CTR만 높이면 되는지, 지켜야 할 룰이 있는지)",
            "이관 범위(스코프) 확정 문서 작성",
            "문서 기반으로 포하이지 리뷰 전 추가 미팅 1회 진행",
        ],
        "notes": [
            "Ground Rule이 있어야 개발팀이 Job으로 이관 시 제약 사항을 정의할 수 있음",
            "FC 미적용 캠페인(포 스토어, 알림받기, 출석 체크 등)은 이관 제외 여부도 이 문서에서 함께 결정",
            "회의 참석자: 김경민, 김건희, 김준호, 김준탁(29cm), 김두하, 최민영",
        ],
    },
    {
        "summary": "[ABC 이관] FC 미적용 캠페인 목록 확인 및 이관 제외 대상 확정",
        "priority": "High",
        "background": "회의에서 빈도 제한(FC, Frequency Capping)이 적용되지 않는 캠페인들은 이관 스코프에서 제외하거나 별도 처리가 필요하다는 논의가 있었다. 김준호 Junho가 FC가 적용되지 않는 캠페인은 마이그레이션하지 않는 등 스코프를 빨리 확정하는 것이 중요하다고 강조했다.",
        "tasks": [
            "현재 운영 중인 ABC 캠페인 중 FC 미적용 대상 전체 목록 추출 (해당 캠페인 예시: 포 스토어, 알림받기, 출석 체크 등)",
            "각 캠페인별 이관 포함/제외 여부 결정",
            "제외 대상은 현행 유지 또는 별도 처리 방안 마련",
        ],
        "notes": [
            "전체 ABC 캠페인 약 70개 운영 중, 잡(Job)으로 실행되는 것 39개",
            "FC 미적용 캠페인이 많으면 이관 복잡도 증가 → 스코프 조기 확정 필요",
            "Ground Rule 문서와 연계하여 진행",
        ],
    },
    {
        "summary": "[ABC 이관] 광고 코드(Ad Code) 처리 방식 결정",
        "priority": "Medium",
        "background": "현재 ABC 캠페인의 광고 코드는 고정으로 운영되며, 날짜나 개인화 변수와 무관하게 동일한 코드가 나간다. 이는 향후 최적화의 이슈가 될 수 있으며, 이관 스코프에서 광고 코드 핸들링 방식을 명확히 해야 한다. 또한 광고 코드가 비즈니스팀의 매출 집계에 활용되는 문제가 있어 처리 방식 결정이 필요하다.",
        "tasks": [
            "고정 광고 코드 유지 vs UTM 뒤 별도 구분 부여 방식 검토",
            "Trace ID 도입 여부 결정 (로그에 광고 코드 외 별도 추적 ID 삽입): CME 등장으로 Trace ID를 로그에 박아 이관 여부와 관계없이 트래킹 가능, PSN 메타에 파라미터 추가 → 딥링크 URL 파싱 → 클릭 로그 트래킹 방식",
            "매출 집계 방식 영향 확인 (비즈니스팀 협의 필요)",
            "광고 코드 번호 중복 문제 검토 (새로 부여 시 다른 코드와 겹칠 가능성)",
        ],
        "notes": [
            "발송 로그 + 클릭 로그 트래킹은 가능하나, 매출 집계는 고정 광고 코드 기준일 수밖에 없어 확인 필요",
            "마케팅 테이블보다 딥링크 URL 파싱 방식이 더 정확할 수 있으며, 데이터 엔지니어링 작업 필요",
        ],
    },
    {
        "summary": "[ABC 이관] API 트리거 이관 대상 캠페인 우선순위 확정",
        "priority": "High",
        "background": "회의에서 이벤트 트리거 방식보다 API 트리거 방식을 우선 마이그레이션하기로 결정했다. API 트리거 방식은 데이터 브릭스 잡이 실행될 때 API를 호출해 메시지를 발송하는 구조로, 발송 대상 목록을 미리 뽑아볼 수 있어 이관에 유리하다.",
        "tasks": [
            "API 트리거 방식 대상 캠페인 전체 목록 정리",
            "우선 이관 대상 선정 기준 정의: 특정 시간대(새벽 시간대) 집중 캠페인 우선 이관 검토, 현재 특정 시간대(10~11시 등)에 '5분 단위로 몰려있다'는 구조 개선 필요",
            "개발팀(김준탁 Daniel)에 Job 이관 시 제약 사항 공유",
            "이관 순서 및 일정 계획 수립",
        ],
        "notes": [
            "API 트리거 방식: 워크플로우 실행 시간이 발송 시간보다 30분~1시간 전에 실행되는 경향",
            "API 트리거는 주로 알림톡 또는 뷰티 상품 조회 시 가격 안내, 회원 이벤트 등 상품 메타 정보 변경 관련 사항 처리",
            "Braze API 호출 부분은 그대로 두고, 코드만 자체 시스템으로 마이그레이션 필요",
        ],
    },
    {
        "summary": "[ABC 이관] 인바운스 연동 설계 검토 및 MVP 범위 합의",
        "priority": "High",
        "background": "이번 이관의 최종 목표는 통합 파이프라인에서 Send Time 최적화를 인바운스로 이관하는 것이다. 이관 전에 인바운스 연동 설계 흐름을 확인하고 MVP 범위(시간 최적화 포함/미포함)를 합의해야 한다.",
        "tasks": [
            "인바운스 연동 설계 흐름 검토: 사용자별 등록된 API → 인바운스 메시지 적재 → 스케줄 최적화 → 발송, 발송 전 사용자별 체크 및 최적화 수행 방식 확인",
            "시간 최적화 미포함 MVP 범위 합의: 현재 시간 최적화는 제외 결정 → MVP에서 제외 기준 명확화, '5개 슬롯으로 나눠 개인 스코어 기반 할당' 로직은 이후 단계에서 구현",
            "이관 전 이관이 완료되지 않으면 발송 시마다 모든 스크를 실행해야 하는 문제 확인 (API 호출은 그대로, 코드만 마이그레이션하는 방식으로 준비)",
        ],
        "notes": [
            "인바운스 이관 전에는 이관 완료가 안 되면 발송마다 모든 스크 실행 필요 → 확장 어려움",
            "ABC는 이미 사용자마다 트리거가 달라 인입되는 것이므로, 옵티마이저 이후 'A를 보내면 B를 보내지 않는다'는 기본 정책에 따라 우선순위만 정렬해 넘겨주는 방식 가능",
            "최민영 Lucca의 우려: 변수 복잡성 + FC 미걸리는 캠페인 등 변수 많음 → 스코프 빠른 확정 필요",
        ],
    },
    {
        "summary": "[ABC 이관] Send Time 최적화 인바운스 이관 (분기 최종 목표)",
        "priority": "Medium",
        "background": "이번 분기 마이그레이션의 최종 목표는 통합 파이프라인에서 Send Time(발송 시간) 최적화를 인바운스로 이관하는 것이다. 현재 캠페인들이 특정 시간대에 몰려 있어 슬롯 분산이 필요하며, 개인별 최적 발송 시간을 찾아 할당하는 로직이 필요하다.",
        "tasks": [
            "기존 노트북 기반의 발송 스케줄을 FC 스케줄 테이블로 만들어 파이프라인으로 연계하는 방식 설계",
            "개인별 시간대 스코어 기반 슬롯 할당 로직 구현: 가장 높은 CTR을 보이는 시간대별 개인 스코어 할당, 5개 슬롯으로 나눠 분산 발송",
            "ML팀과 협의: 여러 배치를 단일 배치로 모아 최적화 후 넘겨주는 구조",
            "이관 우선순위 재정렬 미수행 확인 (현재 제외 결정)",
        ],
        "notes": [
            "현재 캠페인들이 11시, 13시, 14시 등 정해진 시간대에만 발송되도록 되어 있음",
            "이미 타겟팅이 되어 있으므로 온사이트 타겟팅은 제외",
            "Send Time 최적화는 이미 모델링 완료 상태 → 파이프라인 연계 작업만 남음",
            "이번 분기 마이그레이션 스코프: 통합 파이프라인에서 Send Time 최적화까지 포함하여 인바운스로 이관",
        ],
    },
]


def create_ticket(ticket: dict) -> dict:
    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": ticket["summary"],
            "issuetype": {"id": ISSUE_TYPE_ID},
            "priority": {"name": ticket["priority"]},
            "description": make_description(
                ticket["background"], ticket["tasks"], ticket["notes"]
            ),
        }
    }
    resp = requests.post(
        f"{BASE_URL}/rest/api/3/issue",
        auth=AUTH,
        headers=HEADERS,
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    results = []
    for i, ticket in enumerate(TICKETS, 1):
        print(f"[{i}/{len(TICKETS)}] 생성 중: {ticket['summary']}")
        try:
            result = create_ticket(ticket)
            key = result.get("key", "?")
            url = f"{BASE_URL}/browse/{key}"
            print(f"  ✅ {key} → {url}")
            results.append({"key": key, "url": url, "summary": ticket["summary"]})
        except requests.HTTPError as e:
            print(f"  ❌ 실패: {e.response.status_code} — {e.response.text}")
            results.append({"key": None, "error": str(e), "summary": ticket["summary"]})

    output_path = "output/created_abc_migration_tickets.json"
    os.makedirs("output", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n📁 결과 저장: {output_path}")
    print(f"\n생성된 티켓 목록:")
    for r in results:
        if r.get("key"):
            print(f"  - [{r['key']}] {r['summary']}")
            print(f"    {r['url']}")


if __name__ == "__main__":
    main()
