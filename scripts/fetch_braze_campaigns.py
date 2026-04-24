#!/usr/bin/env python3
"""
Braze Campaign Bulk Fetcher v2
=================================
brazecampaign.md의 URL에서 캠페인을 식별하여 Braze REST API로 상세 정보(본문·설정값)를 일괄 조회·저장합니다.

전략:
  A) 이름 기반 정확 매칭  (URL에 campaignName 있는 경우)
  B1) 퍼지 매칭          (이름은 있지만 정확 매칭 실패)
  B2) ObjectId 타임스탬프 (URL에 이름 없는 경우 → 생성 날짜로 후보군 추론)

사용법:
  python3 scripts/fetch_braze_campaigns.py
  python3 scripts/fetch_braze_campaigns.py --dry-run
  BRAZE_API_KEY=xxx python3 scripts/fetch_braze_campaigns.py
"""

import re, json, time, os, argparse, warnings
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import unquote
from difflib import SequenceMatcher

warnings.filterwarnings("ignore")

# ─── 설정 ──────────────────────────────────────────────────────────────────
BRAZE_API_KEY    = os.environ.get("BRAZE_API_KEY", "")
REST_ENDPOINT    = "https://rest.iad-05.braze.com"
INPUT_FILE       = "brazecampaign.md"
OUTPUT_DIR       = "output/braze_campaigns"
RATE_LIMIT_DELAY = 15          # 초 (250 req/hour 준수)
FUZZY_THRESHOLD  = 0.72        # 퍼지 매칭 최소 유사도
TS_WINDOW_DAYS   = 14          # ObjectId 타임스탬프 매칭 윈도우 (±일)
# ───────────────────────────────────────────────────────────────────────────

import requests


# ═══════════════════════════════════════════════════════════════════════════
#  유틸
# ═══════════════════════════════════════════════════════════════════════════

def objectid_to_ts(hex_id: str):
    """MongoDB ObjectId (24 hex) → Unix timestamp"""
    try:
        return int(hex_id[:8], 16)
    except Exception:
        return None


def fuzzy_score(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ═══════════════════════════════════════════════════════════════════════════
#  1. brazecampaign.md 파싱
# ═══════════════════════════════════════════════════════════════════════════

def parse_input(filepath: str) -> list[dict]:
    url_pat  = re.compile(r"campaigns/([a-f0-9]{24})/[a-f0-9]{24}")
    name_pat = re.compile(r"campaignName=([^&\s]+)")

    entries, seen = [], set()
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            m = url_pat.search(line)
            if not m:
                continue
            hex_id = m.group(1)
            if hex_id in seen:
                continue
            seen.add(hex_id)

            nm = name_pat.search(line)
            url_name = unquote(nm.group(1)) if nm else ""
            ts       = objectid_to_ts(hex_id)
            created_approx = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None

            entries.append({
                "hex_id":          hex_id,
                "url_name":        url_name,
                "created_approx":  created_approx,
                "api_id":          None,   # 매칭 후 채워짐
                "match_method":    None,
                "match_score":     None,
                "candidates":      [],
            })
    return entries


# ═══════════════════════════════════════════════════════════════════════════
#  2. Braze 전체 캠페인 목록 수집 (페이지네이션)
# ═══════════════════════════════════════════════════════════════════════════

def fetch_all_campaigns(api_key: str, cache_path: Path = None) -> list[dict]:
    """전체 캠페인 목록 수집. cache_path가 있으면 로드/저장."""
    if cache_path and cache_path.exists():
        print(f"  캐시 로드: {cache_path}")
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    all_campaigns, page = [], 0
    while True:
        # 재시도 로직 (502 등 일시 오류 대응)
        for attempt in range(4):
            try:
                resp = requests.get(
                    f"{REST_ENDPOINT}/campaigns/list",
                    headers={"Authorization": f"Bearer {api_key}"},
                    params={"page": page, "include_archived": True},
                    timeout=30,
                )
                if resp.status_code in (502, 503, 504):
                    wait = (attempt + 1) * 5
                    print(f"  [{resp.status_code}] page {page} 재시도 {attempt+1}/3 ({wait}s 대기)...")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                break
            except requests.exceptions.ConnectionError:
                time.sleep((attempt + 1) * 5)
        else:
            print(f"  [경고] page {page} 4회 실패, 건너뜁니다.")
            page += 1
            continue

        batch = resp.json().get("campaigns", [])
        if not batch:
            break
        all_campaigns.extend(batch)
        page += 1
        if page % 20 == 0:
            print(f"  목록 수집 중... {len(all_campaigns)}개")

    if cache_path:
        save_json(all_campaigns, cache_path)
        print(f"  캐시 저장: {cache_path}")

    return all_campaigns


# ═══════════════════════════════════════════════════════════════════════════
#  3. 매칭
# ═══════════════════════════════════════════════════════════════════════════

def match_entries(entries: list[dict], braze_campaigns: list[dict]) -> None:
    name_map = {c["name"]: c for c in braze_campaigns}

    for entry in entries:
        url_name = entry["url_name"]

        # ── A) 정확 매칭 ─────────────────────────────────────────
        if url_name and url_name in name_map:
            entry["api_id"]       = name_map[url_name]["id"]
            entry["match_method"] = "exact"
            entry["match_score"]  = 1.0
            continue

        # ── B1) 퍼지 매칭 (이름 있는 경우) ───────────────────────
        if url_name:
            best_score, best_camp = 0.0, None
            for c in braze_campaigns:
                s = fuzzy_score(url_name, c["name"])
                if s > best_score:
                    best_score, best_camp = s, c
            if best_score >= FUZZY_THRESHOLD and best_camp:
                entry["api_id"]       = best_camp["id"]
                entry["match_method"] = "fuzzy"
                entry["match_score"]  = round(best_score, 3)
            else:
                entry["match_method"] = "no_match"
            continue

        # ── B2) ObjectId 타임스탬프 매칭 (이름 없는 경우) ─────────
        if entry["created_approx"]:
            ref_dt = entry["created_approx"]
            candidates = []
            for c in braze_campaigns:
                try:
                    edited_dt = datetime.fromisoformat(
                        c["last_edited"].replace("Z", "+00:00")
                    )
                    delta_days = abs((edited_dt - ref_dt).total_seconds()) / 86400
                    if delta_days <= TS_WINDOW_DAYS:
                        candidates.append({
                            "api_id":     c["id"],
                            "name":       c["name"],
                            "last_edited": c["last_edited"],
                            "delta_days": round(delta_days, 1),
                        })
                except Exception:
                    continue
            candidates.sort(key=lambda x: x["delta_days"])
            entry["candidates"]    = candidates[:5]  # 상위 5개만
            entry["match_method"]  = "ts_candidates"
        else:
            entry["match_method"] = "no_match"


# ═══════════════════════════════════════════════════════════════════════════
#  4. 상세 조회
# ═══════════════════════════════════════════════════════════════════════════

def fetch_details(api_id: str, api_key: str) -> dict:
    resp = requests.get(
        f"{REST_ENDPOINT}/campaigns/details",
        headers={"Authorization": f"Bearer {api_key}"},
        params={"campaign_id": api_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def extract_messages(messages: dict) -> dict:
    result = {}
    for key, val in messages.items():
        if not isinstance(val, dict):
            result[key] = val
            continue
        body = {}
        for f in ("title", "body", "message", "subject", "header",
                  "html_body", "plaintext_body", "image_url", "uri", "link_text",
                  "url", "method", "type", "name", "channel"):
            if f in val:
                body[f] = val[f]
        result[key] = body if body else val
    return result


# ═══════════════════════════════════════════════════════════════════════════
#  5. 저장
# ═══════════════════════════════════════════════════════════════════════════

def save_json(data, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
#  main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--input",      default=INPUT_FILE)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--api-key",    default=BRAZE_API_KEY)
    args = parser.parse_args()

    api_key = args.api_key
    out_dir = Path(args.output_dir)
    ts_tag  = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── Step 1. 파싱 ────────────────────────────────────────────
    entries = parse_input(args.input)
    print(f"[1/4] brazecampaign.md 파싱 완료: {len(entries)}개\n")

    if args.dry_run:
        print("[dry-run] 이름 추출 결과:")
        for e in entries:
            label = e["url_name"][:60] if e["url_name"] else "(이름 없음)"
            ts_str = e["created_approx"].strftime("%Y-%m-%d") if e["created_approx"] else "?"
            print(f"  {e['hex_id']}  ts={ts_str}  {label}")
        print("\n[dry-run 모드] 종료.")
        return

    if not api_key:
        print("[오류] BRAZE_API_KEY 미설정.")
        return

    # ── Step 2. 전체 캠페인 목록 ────────────────────────────────
    print("[2/4] Braze 전체 캠페인 목록 수집 중...")
    cache_path = out_dir / "_campaigns_list_cache.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    braze_campaigns = fetch_all_campaigns(api_key, cache_path)
    print(f"      수집 완료: {len(braze_campaigns)}개\n")

    # ── Step 3. 매칭 ────────────────────────────────────────────
    print("[3/4] 매칭 중...")
    match_entries(entries, braze_campaigns)

    exact_list  = [e for e in entries if e["match_method"] == "exact"]
    fuzzy_list  = [e for e in entries if e["match_method"] == "fuzzy"]
    ts_list     = [e for e in entries if e["match_method"] == "ts_candidates"]
    no_match    = [e for e in entries if e["match_method"] == "no_match"]
    to_fetch    = [e for e in entries if e["api_id"]]

    print(f"  정확 매칭(A):       {len(exact_list)}개")
    print(f"  퍼지 매칭(B1):      {len(fuzzy_list)}개")
    print(f"  타임스탬프 후보(B2): {len(ts_list)}개 (자동 선택 불가, 리포트에 포함)")
    print(f"  매칭 실패:          {len(no_match)}개")
    print(f"  상세 조회 대상:     {len(to_fetch)}개\n")

    # ── Step 4. 상세 조회 ───────────────────────────────────────
    print(f"[4/4] 상세 조회 시작 (Rate-limit {RATE_LIMIT_DELAY}s/req)")
    results, errors = [], []

    for i, entry in enumerate(to_fetch, 1):
        print(f"  [{i:02d}/{len(to_fetch):02d}] {entry['api_id']}  [{entry['match_method']}]", end="  ")
        try:
            data = fetch_details(entry["api_id"], api_key)
            result = {
                "hex_id":          entry["hex_id"],
                "api_id":          entry["api_id"],
                "url_name":        entry["url_name"],
                "match_method":    entry["match_method"],
                "match_score":     entry["match_score"],
                "name":            data.get("name", ""),
                "api_status":      data.get("message", ""),
                "schedule_type":   data.get("schedule_type", ""),
                "channels":        data.get("channels", []),
                "tags":            data.get("tags", []),
                "archived":        data.get("archived", False),
                "draft":           data.get("draft", False),
                "first_sent":      data.get("first_sent"),
                "last_sent":       data.get("last_sent"),
                "messages":        extract_messages(data.get("messages", {})),
                "conversion_behaviors": data.get("conversion_behaviors", []),
                "_raw":            data,
            }
            results.append(result)
            print(f"✓  {result['name'][:50]}")
        except Exception as e:
            errors.append({"hex_id": entry["hex_id"], "api_id": entry["api_id"], "error": str(e)})
            print(f"✗  {e}")

        if i < len(to_fetch):
            time.sleep(RATE_LIMIT_DELAY)

    # ── 저장 ─────────────────────────────────────────────────────
    # 4-a. 메시지 요약
    summary = [{
        "hex_id":        r["hex_id"],
        "api_id":        r["api_id"],
        "name":          r["name"],
        "url_name":      r["url_name"],
        "match_method":  r["match_method"],
        "channels":      r["channels"],
        "schedule_type": r["schedule_type"],
        "tags":          r["tags"],
        "first_sent":    r["first_sent"],
        "last_sent":     r["last_sent"],
        "messages":      r["messages"],
    } for r in results]
    summary_path = out_dir / f"campaigns_messages_{ts_tag}.json"
    save_json(summary, summary_path)

    # 4-b. Raw 전체
    raw_path = out_dir / f"campaigns_raw_{ts_tag}.json"
    save_json(results, raw_path)

    # 4-c. B2 타임스탬프 후보 리포트
    ts_report = [{
        "hex_id":         e["hex_id"],
        "created_approx": e["created_approx"].isoformat() if e["created_approx"] else None,
        "candidates":     e["candidates"],
    } for e in ts_list]
    if ts_report:
        ts_path = out_dir / f"campaigns_ts_candidates_{ts_tag}.json"
        save_json(ts_report, ts_path)

    # 4-d. 오류
    if errors:
        err_path = out_dir / f"campaigns_errors_{ts_tag}.json"
        save_json(errors, err_path)

    # ── 리포트 ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"완료: {len(results)}건 성공 / {len(errors)}건 실패")
    print(f"  메시지 요약:  {summary_path}")
    print(f"  Raw 전체:    {raw_path}")
    if ts_report:
        print(f"  B2 후보 목록: {ts_path}  ({len(ts_report)}개 — 수동 확인 필요)")
    if errors:
        print(f"  오류:        {out_dir}/campaigns_errors_{ts_tag}.json")

    # B2 콘솔 출력
    if ts_list:
        print(f"\n[B2] 타임스탬프 후보 — 수동 확인 필요 ({len(ts_list)}개)")
        for e in ts_list:
            dt_str = e["created_approx"].strftime("%Y-%m-%d") if e["created_approx"] else "?"
            print(f"  hex={e['hex_id']}  생성추정={dt_str}")
            for c in e["candidates"][:3]:
                print(f"    후보: {c['api_id']}  {c['name'][:55]}  (Δ{c['delta_days']}d)")


if __name__ == "__main__":
    main()
