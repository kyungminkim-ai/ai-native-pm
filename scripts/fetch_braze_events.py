#!/usr/bin/env python3
"""
Braze Events Analyzer (v2 — 병렬 처리)
========================================
Braze REST API로 커스텀 이벤트 목록, 메타데이터, 최근 30일 사용량을 조회하고
활성/비활성 이벤트를 분류하여 리포트를 저장합니다.

개선: ThreadPoolExecutor로 data_series 병렬 조회 (기본 10 workers)

사용법:
  BRAZE_API_KEY=xxx python3 scripts/fetch_braze_events.py
  BRAZE_API_KEY=xxx python3 scripts/fetch_braze_events.py --workers 5
"""

import os, json, time, csv, argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import requests

# ─── 설정 ──────────────────────────────────────────────────────────────────
BRAZE_API_KEY     = os.environ.get("BRAZE_API_KEY", "")
REST_ENDPOINT     = os.environ.get("BRAZE_REST_ENDPOINT", "https://rest.iad-05.braze.com")
OUTPUT_DIR        = Path("output/braze_events")
SERIES_DAYS       = 30
SERIES_UNIT       = "day"
MAX_WORKERS       = 10   # 병렬 요청 수 (Braze rate limit 고려)
REQUEST_DELAY     = 0.1  # worker당 딜레이 (초)
# ───────────────────────────────────────────────────────────────────────────

_print_lock = threading.Lock()


def safe_print(*args):
    with _print_lock:
        print(*args)


def headers():
    return {"Authorization": f"Bearer {BRAZE_API_KEY}"}


def get(path: str, params: dict = None) -> dict:
    url = f"{REST_ENDPOINT}{path}"
    resp = requests.get(url, headers=headers(), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ══════════════════════════════════════════════════════════════════════════
#  1. 이벤트 목록 수집 (/events/list)
# ══════════════════════════════════════════════════════════════════════════
def fetch_event_list() -> list[str]:
    all_events, page = [], 0
    print("[1/3] /events/list 조회 중...")
    while True:
        data = get("/events/list", {"page": page})
        batch = data.get("events", [])
        if not batch:
            break
        all_events.extend(batch)
        page += 1
        if len(batch) < 250:
            break
        time.sleep(0.5)
    print(f"      총 {len(all_events)}개 이벤트 발견\n")
    return all_events


# ══════════════════════════════════════════════════════════════════════════
#  2. 이벤트 메타데이터 수집 (/events)
# ══════════════════════════════════════════════════════════════════════════
def fetch_event_meta() -> list[dict]:
    all_meta, page = [], 0
    print("[2/3] /events 메타데이터 조회 중...")
    while True:
        data = get("/events", {"page": page})
        batch = data.get("data", [])
        if not batch:
            break
        all_meta.extend(batch)
        page += 1
        if len(batch) < 250:
            break
        time.sleep(0.5)
    print(f"      메타데이터 {len(all_meta)}개 수집\n")
    return all_meta


# ══════════════════════════════════════════════════════════════════════════
#  3. 이벤트별 사용량 수집 — 병렬 (/events/data_series)
# ══════════════════════════════════════════════════════════════════════════
def fetch_one_series(event_name: str) -> dict:
    end_dt = datetime.now(timezone.utc)
    params = {
        "event":     event_name,
        "length":    SERIES_DAYS,
        "unit":      SERIES_UNIT,
        "ending_at": end_dt.strftime("%Y-%m-%dT%H:%M:%S") + "+00:00",
    }
    try:
        time.sleep(REQUEST_DELAY)
        data   = get("/events/data_series", params)
        series = data.get("data", [])
        total  = sum(d.get("count", 0) for d in series)
        return {"event_name": event_name, "total": total, "series": series, "error": None}
    except Exception as e:
        return {"event_name": event_name, "total": 0, "series": [], "error": str(e)}


def fetch_all_series(event_list: list[str], workers: int) -> dict[str, dict]:
    total      = len(event_list)
    counter    = [0]
    results    = {}

    print(f"[3/3] 사용량 조회 (최근 {SERIES_DAYS}일, {workers} workers) — {total}개...")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(fetch_one_series, name): name for name in event_list}
        for future in as_completed(future_map):
            res = future.result()
            results[res["event_name"]] = res
            counter[0] += 1
            if counter[0] % 50 == 0 or counter[0] == total:
                safe_print(f"  진행: {counter[0]}/{total} ({counter[0]/total*100:.0f}%)")

    return results


# ══════════════════════════════════════════════════════════════════════════
#  4. 통합 분석 + 저장
# ══════════════════════════════════════════════════════════════════════════
def analyze_and_save(event_list: list[str], event_meta: list[dict], series_map: dict):
    ts_tag   = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    meta_map = {m.get("name", ""): m for m in event_meta}

    results = []
    for event_name in event_list:
        sr   = series_map.get(event_name, {"total": 0, "series": [], "error": "not fetched"})
        meta = meta_map.get(event_name, {})
        results.append({
            "event_name":            event_name,
            "total_30d":             sr["total"],
            "status":                "active" if sr["total"] > 0 else "inactive",
            "description":           meta.get("description", ""),
            "tags":                  meta.get("tag_names", []),
            "included_in_analytics": meta.get("included_in_analytics_report", None),
            "error":                 sr["error"],
            "series":                sr["series"],
        })

    # 사용량 내림차순 정렬 + rank
    results.sort(key=lambda x: x["total_30d"], reverse=True)
    for rank, r in enumerate(results, 1):
        r["rank"] = rank

    # ── 통계 ──
    active   = [r for r in results if r["status"] == "active"]
    inactive = [r for r in results if r["status"] == "inactive"]
    errors   = [r for r in results if r["error"]]

    print(f"\n{'='*65}")
    print(f"이벤트 분석 완료")
    print(f"  전체:   {len(results):,}개")
    print(f"  활성:   {len(active):,}개  (최근 {SERIES_DAYS}일 1건 이상)")
    print(f"  비활성: {len(inactive):,}개")
    print(f"  오류:   {len(errors):,}개")

    if active:
        print(f"\n  TOP 20 활성 이벤트 (30일 발생량):")
        for r in active[:20]:
            tags = "|".join(r["tags"]) if r["tags"] else "-"
            print(f"    {r['rank']:4d}. {r['event_name'][:55]:<55}  {r['total_30d']:>12,}건  [{tags}]")

    if inactive:
        print(f"\n  비활성 이벤트 샘플 (최근 5개):")
        for r in inactive[:5]:
            print(f"         {r['event_name']}")

    # ── JSON 저장 ──
    json_path = OUTPUT_DIR / f"events_analysis_{ts_tag}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # ── CSV 저장 ──
    csv_path = OUTPUT_DIR / f"events_analysis_{ts_tag}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "rank", "event_name", "total_30d", "status",
            "description", "tags", "included_in_analytics", "error"
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "rank":                  r["rank"],
                "event_name":            r["event_name"],
                "total_30d":             r["total_30d"],
                "status":                r["status"],
                "description":           r["description"],
                "tags":                  "|".join(r["tags"]) if isinstance(r["tags"], list) else str(r["tags"]),
                "included_in_analytics": r["included_in_analytics"],
                "error":                 r["error"] or "",
            })

    print(f"\n{'='*65}")
    print(f"📁 산출물:")
    print(f"  JSON (시계열 포함): {json_path}")
    print(f"  CSV  (요약):       {csv_path}")
    return results, json_path, csv_path


# ══════════════════════════════════════════════════════════════════════════
#  main
# ══════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    args = parser.parse_args()

    if not BRAZE_API_KEY:
        print("[오류] BRAZE_API_KEY 미설정. export BRAZE_API_KEY=xxx")
        return

    print(f"Braze Events Analyzer v2")
    print(f"Endpoint : {REST_ENDPOINT}")
    print(f"분석기간 : 최근 {SERIES_DAYS}일 / Workers: {args.workers}\n")

    event_list = fetch_event_list()
    event_meta = fetch_event_meta()
    series_map = fetch_all_series(event_list, args.workers)
    analyze_and_save(event_list, event_meta, series_map)


if __name__ == "__main__":
    main()
