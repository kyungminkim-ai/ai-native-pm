#!/usr/bin/env python3
"""
Braze User Attribute Analyzer
================================
/users/export/ids 로 샘플 유저 프로파일을 조회하고
실제 수집 중인 custom_attributes, 구매 이력, 이벤트 이력,
세션 정보 등 User Data 현황을 파악합니다.

사용법:
  BRAZE_API_KEY=xxx python3 scripts/fetch_braze_user_attributes.py
  BRAZE_API_KEY=xxx python3 scripts/fetch_braze_user_attributes.py --external-ids id1,id2,id3
  BRAZE_API_KEY=xxx python3 scripts/fetch_braze_user_attributes.py --from-segment-export
"""

import os, json, csv, argparse
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict

import requests

# ─── 설정 ──────────────────────────────────────────────────────────────────
BRAZE_API_KEY    = os.environ.get("BRAZE_API_KEY", "")
REST_ENDPOINT    = os.environ.get("BRAZE_REST_ENDPOINT", "https://rest.iad-05.braze.com")
OUTPUT_DIR       = Path("output/braze_user_attributes")
# ───────────────────────────────────────────────────────────────────────────

FIELDS_TO_REQUEST = [
    "external_id",
    "user_aliases",
    "braze_id",
    "first_name",
    "last_name",
    "email",
    "email_subscribe",
    "push_subscribe",
    "created_at",
    "updated_at",
    "country",
    "language",
    "last_coordinates",
    "sdk_version_info",
    "custom_attributes",
    "custom_events",
    "purchases",
    "devices",
    "push_tokens",
    "total_revenue",
    "attributed_campaign",
    "attributed_source",
    "attributed_adgroup",
    "attributed_ad",
    "email_unsubscribed_at",
    "push_opted_in_at",
]


def headers():
    return {
        "Authorization": f"Bearer {BRAZE_API_KEY}",
        "Content-Type": "application/json",
    }


# ══════════════════════════════════════════════════════════════════════════
#  1. 기존 캠페인 샘플에서 external_id 수집
# ══════════════════════════════════════════════════════════════════════════
def collect_sample_ids_from_export() -> list[str]:
    """이전에 저장된 유저 export 파일에서 external_id 수집"""
    sample_files = list(Path("output/braze_campaigns").glob("sample_*.json"))
    ids = []
    for f in sample_files:
        try:
            with open(f) as fp:
                data = json.load(fp)
            if isinstance(data, dict):
                users = data.get("users", [data]) if "users" in data else [data]
            else:
                users = data
            for u in users:
                eid = u.get("external_id") or u.get("external_ids", [None])[0] if "external_ids" in u else None
                if eid:
                    ids.append(eid)
        except Exception:
            pass
    return list(set(ids))


# ══════════════════════════════════════════════════════════════════════════
#  2. /users/export/ids 호출
# ══════════════════════════════════════════════════════════════════════════
def fetch_users_by_ids(external_ids: list[str]) -> list[dict]:
    """external_id 리스트로 유저 프로파일 조회 (최대 50개/요청)"""
    all_users = []
    chunk_size = 50
    chunks = [external_ids[i:i+chunk_size] for i in range(0, len(external_ids), chunk_size)]

    print(f"[2/3] /users/export/ids 조회 — {len(external_ids)}명 ({len(chunks)}개 배치)")
    for i, chunk in enumerate(chunks, 1):
        payload = {
            "external_ids": chunk,
            "fields_to_export": FIELDS_TO_REQUEST,
        }
        try:
            resp = requests.post(
                f"{REST_ENDPOINT}/users/export/ids",
                headers=headers(),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            users = data.get("users", [])
            all_users.extend(users)
            print(f"  배치 {i}/{len(chunks)}: {len(users)}명 수신")
        except Exception as e:
            print(f"  배치 {i} 오류: {e}")

    return all_users


# ══════════════════════════════════════════════════════════════════════════
#  3. 유저 프로파일에서 attribute 분석
# ══════════════════════════════════════════════════════════════════════════
def analyze_user_profiles(users: list[dict]) -> dict:
    """수집된 유저 프로파일에서 attribute 현황 분석"""
    n = len(users)
    if n == 0:
        return {}

    # custom_attributes 수집
    attr_counter  = Counter()   # attribute 이름 → 등장 횟수
    attr_types    = defaultdict(set)   # attribute 이름 → 값 타입 집합
    attr_samples  = defaultdict(list)  # attribute 이름 → 샘플 값 (최대 3개)

    # custom_events 수집
    event_counter = Counter()

    # purchases 수집
    purchase_counter = Counter()

    # 기본 필드 채워짐 여부
    std_fields = ["email", "first_name", "country", "language", "total_revenue",
                  "attributed_campaign", "push_tokens", "devices"]
    field_fill = {f: 0 for f in std_fields}

    for u in users:
        # custom_attributes
        attrs = u.get("custom_attributes", {}) or {}
        for k, v in attrs.items():
            attr_counter[k] += 1
            attr_types[k].add(type(v).__name__)
            if len(attr_samples[k]) < 3 and v not in (None, "", [], {}):
                attr_samples[k].append(v)

        # custom_events
        events = u.get("custom_events", []) or []
        for ev in events:
            name = ev.get("name", "")
            if name:
                event_counter[name] += 1

        # purchases
        purchases = u.get("purchases", []) or []
        for p in purchases:
            pid = p.get("name", "") or p.get("product_id", "")
            if pid:
                purchase_counter[pid] += 1

        # 표준 필드 fill rate
        for f in std_fields:
            val = u.get(f)
            if val not in (None, "", [], {}):
                field_fill[f] += 1

    return {
        "sample_size": n,
        "custom_attributes": {
            "count": len(attr_counter),
            "top_by_coverage": [
                {
                    "attribute":  k,
                    "users_with": v,
                    "coverage":   f"{v/n*100:.1f}%",
                    "types":      list(attr_types[k]),
                    "sample":     attr_samples[k],
                }
                for k, v in attr_counter.most_common(100)
            ],
        },
        "custom_events_in_profile": {
            "count": len(event_counter),
            "top": [{"event": k, "users_with": v} for k, v in event_counter.most_common(50)],
        },
        "purchases_in_profile": {
            "count": len(purchase_counter),
            "top": [{"product": k, "users_with": v} for k, v in purchase_counter.most_common(30)],
        },
        "standard_field_fill": {
            f: {"users_with": v, "coverage": f"{v/n*100:.1f}%"}
            for f, v in field_fill.items()
        },
    }


# ══════════════════════════════════════════════════════════════════════════
#  4. 저장 + 출력
# ══════════════════════════════════════════════════════════════════════════
def save_results(users: list[dict], analysis: dict, ts_tag: str):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 프로파일 raw 저장
    raw_path = OUTPUT_DIR / f"user_profiles_{ts_tag}.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2, default=str)

    # 분석 결과 저장
    analysis_path = OUTPUT_DIR / f"user_attributes_analysis_{ts_tag}.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    # Custom Attributes CSV
    attr_csv_path = OUTPUT_DIR / f"custom_attributes_{ts_tag}.csv"
    with open(attr_csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["attribute", "users_with", "coverage", "types", "sample"])
        writer.writeheader()
        for row in analysis.get("custom_attributes", {}).get("top_by_coverage", []):
            writer.writerow({
                "attribute":  row["attribute"],
                "users_with": row["users_with"],
                "coverage":   row["coverage"],
                "types":      "|".join(row["types"]),
                "sample":     str(row["sample"]),
            })

    n = analysis.get("sample_size", 0)
    attrs = analysis.get("custom_attributes", {})
    std   = analysis.get("standard_field_fill", {})

    print(f"\n{'='*65}")
    print(f"User Attribute 분석 완료")
    print(f"  샘플 유저 수:        {n}명")
    print(f"  custom_attributes:  {attrs.get('count', 0)}개 종류")

    print(f"\n  [표준 필드 Fill Rate]")
    for f, v in std.items():
        print(f"    {f:<35} {v['coverage']:>7}  ({v['users_with']}/{n}명)")

    print(f"\n  [Custom Attribute Top 30 (커버리지)]")
    for row in attrs.get("top_by_coverage", [])[:30]:
        types_str = "|".join(row["types"])
        print(f"    {row['attribute']:<45} {row['coverage']:>7}  ({types_str})")

    print(f"\n{'='*65}")
    print(f"📁 산출물:")
    print(f"  User Profiles (raw):   {raw_path}")
    print(f"  Attribute 분석:        {analysis_path}")
    print(f"  Attribute CSV:         {attr_csv_path}")

    return raw_path, analysis_path, attr_csv_path


# ══════════════════════════════════════════════════════════════════════════
#  main
# ══════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--external-ids", help="쉼표로 구분된 external_id 목록")
    parser.add_argument("--from-segment-export", action="store_true",
                        help="이전에 저장된 export 파일에서 ID 수집")
    args = parser.parse_args()

    if not BRAZE_API_KEY:
        print("[오류] BRAZE_API_KEY 미설정.")
        return

    ts_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Braze User Attribute Analyzer")
    print(f"Endpoint: {REST_ENDPOINT}\n")

    # ── Step 1. ID 수집 ─────────────────────────────────────────────────
    print("[1/3] 샘플 external_id 수집 중...")

    if args.external_ids:
        external_ids = [x.strip() for x in args.external_ids.split(",") if x.strip()]
        print(f"      CLI 입력: {len(external_ids)}개")
    elif args.from_segment_export:
        external_ids = collect_sample_ids_from_export()
        print(f"      기존 export 파일에서: {len(external_ids)}개")
    else:
        # 기존 export 파일 우선, 없으면 샘플 유저 직접 조회 시도
        external_ids = collect_sample_ids_from_export()
        if external_ids:
            print(f"      기존 export 파일에서: {len(external_ids)}개")
        else:
            print("      [참고] --external-ids로 유저 ID를 전달하거나")
            print("             --from-segment-export 옵션을 사용하세요.")
            print("      기존 sample 파일에서 ID를 찾을 수 없습니다.")
            return

    if not external_ids:
        print("[오류] 조회할 external_id가 없습니다.")
        return

    # ── Step 2. 유저 프로파일 조회 ──────────────────────────────────────
    users = fetch_users_by_ids(external_ids)
    print(f"\n      총 {len(users)}명 프로파일 수신\n")

    if not users:
        print("[오류] 수신된 유저 프로파일이 없습니다.")
        return

    # ── Step 3. 분석 ────────────────────────────────────────────────────
    print("[3/3] Attribute 분석 중...")
    analysis = analyze_user_profiles(users)

    save_results(users, analysis, ts_tag)


if __name__ == "__main__":
    main()
