#!/usr/bin/env python3
"""
19시 시트에서 brand_id 추출 스크립트
Step 1: Haiku로 푸시 텍스트에서 브랜드명 추출
Step 2: 브랜드 dict로 front_brand_no 매핑
"""

import csv
import json
import os
import time
import anthropic

BRAND_CSV = "/Users/musinsa/Downloads/[29CM] 캠페인메타엔진-시트 - Brand 정보 (1).csv"
PUSH_CSV = "/Users/musinsa/Downloads/[29CM] 캠페인메타엔진-시트 - 19시 (1).csv"
OUTPUT_FILE = "/Users/musinsa/Documents/agent_project/pm-studio/output/brand_id_extraction_result.json"

client = anthropic.Anthropic()


def load_brands():
    """브랜드 딕셔너리 및 원본 리스트 로드"""
    brand_dict = {}   # normalized name → front_brand_no
    brand_entries = []
    with open(BRAND_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            no = row["front_brand_no"].strip()
            kor = row["brand_name_kor"].strip()
            eng = row["brand_name_eng"].strip()
            brand_entries.append({"kor": kor, "eng": eng, "no": no})
            if kor:
                brand_dict[kor.lower()] = no
                # 공백 제거 버전도 추가
                brand_dict[kor.replace(" ", "").lower()] = no
            if eng:
                brand_dict[eng.lower()] = no
                brand_dict[eng.replace(" ", "").lower()] = no
    return brand_dict, brand_entries


def load_19_rows():
    """19:00 시간대 rows 로드"""
    rows = []
    with open(PUSH_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        all_rows = list(reader)

    for r in all_rows:
        if len(r) > 2 and r[2].strip() == "19:00":
            rows.append({
                "campaign_id": r[0].strip(),
                "existing_brand_id": r[8].strip() if len(r) > 8 else "",
                "title": r[14].strip() if len(r) > 14 else "",
                "body": r[15].strip() if len(r) > 15 else "",
            })
    return rows


def extract_brand_names_haiku(title: str, body: str) -> list[str]:
    """Haiku로 푸시에서 브랜드명 추출 (텍스트만 반환)"""
    prompt = f"""다음 앱푸시 메시지에서 브랜드명만 추출하세요.

타이틀: {title}
본문: {body}

규칙:
- 브랜드명만 추출 (여러 개면 줄바꿈으로 구분)
- 브랜드가 없으면 "없음" 반환
- 브랜드명 외 다른 텍스트 없이 반환
- 한국어/영어 그대로 반환 (번역 불필요)

예시:
나이키
아디다스

또는: 없음"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text.strip()
    if text == "없음" or not text:
        return []
    return [name.strip() for name in text.split("\n") if name.strip() and name.strip() != "없음"]


def match_brand_names(brand_names: list[str], brand_dict: dict) -> list[str]:
    """브랜드명 → front_brand_no 매핑"""
    found_ids = []
    for name in brand_names:
        normalized = name.lower()
        if normalized in brand_dict:
            found_ids.append(brand_dict[normalized])
            continue
        # 공백 제거 버전
        no_space = name.replace(" ", "").lower()
        if no_space in brand_dict:
            found_ids.append(brand_dict[no_space])
            continue
        # 부분 매칭 (긴 브랜드명이 포함된 경우)
        for brand_key, brand_no in brand_dict.items():
            if len(name) >= 2 and (name.lower() in brand_key or brand_key in name.lower()):
                if brand_no not in found_ids:
                    found_ids.append(brand_no)
                break
    return found_ids


def main():
    print("브랜드 데이터 로드 중...")
    brand_dict, _ = load_brands()
    print(f"  총 {len(brand_dict)}개 브랜드명 인덱싱")

    print("19:00 rows 로드 중...")
    rows = load_19_rows()
    total = len(rows)
    print(f"  총 {total}개 rows\n")

    results = []
    stats = {"existing": 0, "haiku_found": 0, "not_found": 0, "error": 0}

    for i, row in enumerate(rows):
        cid = row["campaign_id"]
        title = row["title"]
        body = row["body"]
        existing = row["existing_brand_id"]

        if existing:
            stats["existing"] += 1
            results.append({"campaign_id": cid, "brand_id": existing, "source": "existing", "title": title})
            print(f"[{i+1}/{total}] {cid}: {existing} (기존) | {title[:40]}")
            continue

        try:
            brand_names = extract_brand_names_haiku(title, body)
            matched_ids = match_brand_names(brand_names, brand_dict) if brand_names else []

            if matched_ids:
                brand_id_str = ",".join(matched_ids)
                stats["haiku_found"] += 1
                source = "haiku"
            else:
                brand_id_str = ""
                stats["not_found"] += 1
                source = "not_found"

            results.append({
                "campaign_id": cid,
                "brand_id": brand_id_str,
                "extracted_names": brand_names,
                "source": source,
                "title": title,
            })
            status = brand_id_str if brand_id_str else f"[미발견: {brand_names}]"
            print(f"[{i+1}/{total}] {cid}: {status} | {title[:50]}")

        except Exception as e:
            print(f"[{i+1}/{total}] {cid}: ERROR - {e}")
            results.append({"campaign_id": cid, "brand_id": "", "source": "error", "title": title})
            stats["error"] += 1

        time.sleep(0.15)

    # 저장
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n=== 완료 ===")
    print(f"  기존 채워진: {stats['existing']}")
    print(f"  Haiku 매칭 성공: {stats['haiku_found']}")
    print(f"  미발견: {stats['not_found']}")
    print(f"  오류: {stats['error']}")
    print(f"\n결과 저장: {OUTPUT_FILE}")

    print("\n=== campaign_id → brand_id 매핑 결과 ===")
    print(f"{'campaign_id':<15} {'brand_id':<20} {'타이틀'}")
    print("-" * 80)
    for r in results:
        if r["brand_id"]:
            print(f"{r['campaign_id']:<15} {r['brand_id']:<20} {r['title'][:40]}")

    # 미발견 목록
    not_found_rows = [r for r in results if not r["brand_id"] and r["source"] != "existing"]
    if not_found_rows:
        print(f"\n=== 브랜드 미발견 ({len(not_found_rows)}건) ===")
        for r in not_found_rows:
            names = r.get("extracted_names", [])
            print(f"  {r['campaign_id']}: [{', '.join(names) if names else '추출 실패'}] | {r['title'][:50]}")


if __name__ == "__main__":
    main()
