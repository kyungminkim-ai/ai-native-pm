#!/usr/bin/env python3
"""
캠페인 Markdown + CSV 파싱 → Jira 티켓 description JSON 생성
Output: /tmp/campaign_tickets.json
"""
import re
import csv
import json

MD_FILE = "/Users/musinsa/Documents/agent_project/pm-studio/campaigns_body_20260415_101943.md"
CSV_FILE = "/Users/musinsa/Downloads/[무신사_그로스코어] 리인게이지먼트 자동화 현황 - 현황 (1).csv"
BODY_CSV = "/Users/musinsa/Documents/agent_project/pm-studio/output/braze_campaigns/campaigns_body_20260415_101943.csv"
OUTPUT_FILE = "/tmp/campaign_tickets.json"

# ─── 1. CSV 참고 데이터 로드 (ad_code → 참고 필드) ────────────────────────────
def load_reference_csv():
    ref = {}
    with open(CSV_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = (row.get("ad_code") or "").strip()
            if not code:
                continue
            ref[code] = {
                "발송종료시간대": (row.get("(예상)\n발송 종료 시간대") or row.get("(예상) 발송 종료 시간대") or "").strip(),
                "sending_interval": (row.get("Sending\ninterval") or row.get("Sending interval") or "").strip(),
                "브랜드성별구분": (row.get("브랜드\n성별 구분") or row.get("브랜드 성별 구분") or "").strip(),
                "개인화설정로직": (row.get("개인화 설정 로직") or "").strip(),
                "상세조건": (row.get("상세 조건") or "").strip(),
                "braze_url": (row.get("Braze (웹훅)") or "").strip(),
                "notebook_url": (row.get("Notebook") or "").strip(),
                "workflows_url": (row.get("Workflows") or "").strip(),
            }
    return ref

# ─── 2. Body CSV (Liquid 코드 포함) 로드 ──────────────────────────────────────
def load_body_csv():
    bodies = {}
    with open(BODY_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("campaign_name") or "").strip()
            body = (row.get("body") or "").strip()
            if name:
                # campaign_name에서 ad_code 추출
                parts = name.split("_")
                # ad_code는 보통 3번째 element (APSRENG015 형태)
                ad_code = None
                for p in parts:
                    if re.match(r'^[A-Z]{3,}[A-Z0-9]+\d{3,}$', p):
                        ad_code = p
                        break
                if ad_code:
                    if ad_code not in bodies:
                        bodies[ad_code] = body
    return bodies

# ─── 3. Markdown 파싱 ─────────────────────────────────────────────────────────
def parse_markdown():
    with open(MD_FILE, encoding="utf-8") as f:
        content = f.read()

    # ## N. 캠페인명 으로 분리
    sections = re.split(r'\n## \d+\. ', content)
    campaigns = []

    for i, sec in enumerate(sections[1:], 1):  # 첫 번째는 헤더
        lines = sec.strip().split('\n')
        campaign_name = lines[0].strip()

        # ad_code 추출
        ad_code_match = re.search(r'(APS[A-Z0-9]+|ALT[A-Z0-9]+)', campaign_name)
        ad_code = ad_code_match.group(1) if ad_code_match else ""

        # Liquid body 추출 (```liquid 또는 ``` 블럭)
        body_match = re.search(r'```(?:liquid)?\s*\n([\s\S]*?)\n```', sec)
        liquid_body = body_match.group(1).strip() if body_match else ""

        campaigns.append({
            "index": i,
            "campaign_name": campaign_name,
            "ad_code": ad_code,
            "liquid_body": liquid_body,
        })

    return campaigns

# ─── 4. Liquid 분석 ────────────────────────────────────────────────────────────
def analyze_liquid(liquid_body):
    """Liquid 로직 구문과 메시지 필드를 분리 분석"""
    # title, body, linkUrl, imageUrl 추출
    fields = {}
    for field in ["title", "body", "linkUrl", "imageUrl"]:
        m = re.search(rf'"{field}":\s*"((?:[^"\\]|\\.)*)"', liquid_body)
        if m:
            fields[field] = m.group(1)
        else:
            fields[field] = ""

    # 개인화 변수 추출 ({{ ... }} 패턴)
    vars_found = re.findall(r'\{\{([^}]+)\}\}', liquid_body)
    personal_vars = []
    seen = set()
    for v in vars_found:
        v = v.strip()
        if v not in seen:
            seen.add(v)
            personal_vars.append(v)

    # Liquid 로직 구문 추출 ({% ... %} 블럭)
    logic_lines = []
    for line in liquid_body.split('\n'):
        stripped = line.strip()
        if stripped.startswith('{%') and stripped.endswith('%}'):
            logic_lines.append(stripped)
        elif stripped.startswith('{%'):
            logic_lines.append(stripped)

    return fields, personal_vars, logic_lines

# ─── 5. Liquid 로직 한글 해석 ─────────────────────────────────────────────────
def interpret_liquid(logic_lines):
    interpretations = []
    for line in logic_lines:
        line_clean = line.strip()
        if 'assign' in line_clean:
            interpretations.append((line_clean, "변수 할당 — API/이벤트 속성 값을 로컬 변수에 저장"))
        elif 'catalog_items' in line_clean:
            interpretations.append((line_clean, "카탈로그 조회 — 지정 카탈로그에서 항목 조회"))
        elif line_clean.startswith('{% if'):
            # 조건 내용 요약
            if 'brand_gender' in line_clean and 'gender_custom' in line_clean:
                interpretations.append((line_clean, "발송 조건 — ①브랜드 성별 null이거나 ②사용자 성별 null이거나 ③브랜드 성별 = 사용자 성별이면 발송"))
            elif 'null' in line_clean:
                interpretations.append((line_clean, "발송 조건 — null 체크 후 조건 충족 시 발송"))
            else:
                interpretations.append((line_clean, "발송 조건 — 조건 충족 시 발송"))
        elif 'abort_message' in line_clean:
            interpretations.append((line_clean, "조건 불일치 시 발송 중단"))
        elif line_clean.startswith('{% else'):
            interpretations.append((line_clean, "조건 불일치 분기"))
        elif line_clean.startswith('{% endif'):
            interpretations.append((line_clean, "조건문 종료"))
    return interpretations

# ─── 6. 개인화 변수 분류 ───────────────────────────────────────────────────────
def classify_var(var):
    var = var.strip()
    if 'api_trigger_properties' in var:
        return "API 트리거 속성"
    elif 'event_properties' in var:
        return "이벤트 속성"
    elif 'custom_attribute' in var:
        return "유저 커스텀 속성"
    elif var.startswith('campaign.'):
        return "시스템 변수 (캠페인)"
    elif var.startswith('${user_id}') or var == '${user_id}':
        return "시스템 변수 (유저)"
    elif 'canvas' in var.lower():
        return "시스템 변수 (캔버스)"
    else:
        return "시스템/기타 변수"

def get_var_desc(var):
    var = var.strip()
    known = {
        'api_trigger_properties.${brand}': "브랜드 코드",
        'api_trigger_properties.${brand_nm}': "브랜드명",
        'api_trigger_properties.${new_cnt}': "신상품 수",
        'api_trigger_properties.${act_search_keyword}': "검색 키워드",
        'api_trigger_properties.${coupon_no}': "쿠폰 번호",
        'api_trigger_properties.${coupon_per}': "쿠폰 할인율",
        'api_trigger_properties.${category}': "카테고리 코드",
        'api_trigger_properties.${category_nm}': "카테고리명",
        'api_trigger_properties.${goods_no}': "상품 번호",
        'api_trigger_properties.${goods_nm}': "상품명",
        'api_trigger_properties.${review_cnt_gap}': "후기 증가 수",
        'api_trigger_properties.${message}': "메시지 내용",
        'api_trigger_properties.${id}': "ID",
        'custom_attribute.${gender_custom}': "사용자 성별 (필터링용)",
        'custom_attribute.${brand_alarm_cart_250925}': "커스텀 속성 브랜드",
        'custom_attribute.${brand_nm_alarm_cart_250925}': "커스텀 속성 브랜드명",
        'custom_attribute.${goods_nm_alarm_cart_250925}': "커스텀 속성 상품명",
        'custom_attribute.${qty_alarm_cart_250925}': "커스텀 속성 수량",
        'custom_attribute.${goods_no_alarm_cart_250925}': "커스텀 속성 상품번호",
        'campaign.${api_id}': "캠페인 API ID",
        'campaign.${name}': "캠페인명",
        '${user_id}': "회원 Hash ID",
        'event_properties.${brand}': "이벤트 브랜드 코드",
        'event_properties.${brand_nm}': "이벤트 브랜드명",
    }
    return known.get(var, "")

# ─── 7. Description Markdown 생성 ────────────────────────────────────────────
def build_description(campaign, ref_data, body_data):
    name = campaign["campaign_name"]
    ad_code = campaign["ad_code"]
    liquid_body = campaign["liquid_body"]

    # body CSV에서 Liquid 가져오기 (더 정확)
    if ad_code and ad_code in body_data:
        liquid_body = body_data[ad_code]

    fields, personal_vars, logic_lines = analyze_liquid(liquid_body)
    interpretations = interpret_liquid(logic_lines)
    ref = ref_data.get(ad_code, {})

    lines = []

    # 기본 정보
    lines.append("## 캠페인 기본 정보")
    lines.append("")
    lines.append("| 항목 | 내용 |")
    lines.append("|------|------|")
    lines.append(f"| **캠페인명** | {name} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Liquid 원문
    lines.append("## Liquid 문 (원문)")
    lines.append("")
    lines.append("```")
    lines.append(liquid_body)
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Liquid 한글 해석
    lines.append("## Liquid 문 한글 해석")
    lines.append("")
    if interpretations:
        lines.append("| 구문 | 해석 |")
        lines.append("|------|------|")
        for stmt, interp in interpretations:
            stmt_safe = stmt.replace("|", "\\|").replace("`", "'")
            lines.append(f"| `{stmt_safe}` | {interp} |")
    else:
        lines.append("Liquid 조건/제어 로직 없음 (단순 JSON body)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 메시지 본문 상세
    lines.append("## 메시지 본문 상세")
    lines.append("")
    lines.append("| 항목 | 원문 |")
    lines.append("|------|------|")
    title_val = fields.get("title", "").replace("|", "\\|")
    body_val = fields.get("body", "").replace("|", "\\|")
    link_val = fields.get("linkUrl", "").replace("|", "\\|")
    image_val = fields.get("imageUrl", "") or "(비어있음)"
    lines.append(f"| **title** | {title_val} |")
    lines.append(f"| **body** | {body_val} |")
    lines.append(f"| **linkUrl** | {link_val} |")
    lines.append(f"| **bodyURL (imageUrl)** | {image_val} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 개인화 변수 목록
    lines.append("## 개인화 변수 목록")
    lines.append("")
    if personal_vars:
        lines.append("| 변수 | 출처 | 설명 |")
        lines.append("|------|------|------|")
        for v in personal_vars:
            src = classify_var(v)
            desc = get_var_desc(v)
            v_safe = v.replace("|", "\\|")
            lines.append(f"| `{v_safe}` | {src} | {desc} |")
    else:
        lines.append("개인화 변수 없음")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 참고 정보 및 링크
    lines.append("## 참고 정보 및 링크")
    lines.append("")
    lines.append(f"- **(예상) 발송 종료 시간대**: {ref.get('발송종료시간대') or '-'}")
    lines.append(f"- **Sending interval**: {ref.get('sending_interval') or '-'}")
    lines.append(f"- **브랜드 성별 구분**: {ref.get('브랜드성별구분') or '-'}")

    logic = ref.get('개인화설정로직', '').replace('\n', ' / ')
    lines.append(f"- **개인화 설정 로직**: {logic or '-'}")

    cond = ref.get('상세조건', '').replace('\n', ' ')
    lines.append(f"- **상세 조건**: {cond or '-'}")

    braze = ref.get('braze_url', '')
    if braze:
        lines.append(f"- **Braze (웹훅)**: {braze}")
    else:
        lines.append("- **Braze (웹훅)**: -")

    nb = ref.get('notebook_url', '')
    if nb:
        lines.append(f"- **Notebook**: {nb}")
    else:
        lines.append("- **Notebook**: -")

    wf = ref.get('workflows_url', '')
    if wf:
        lines.append(f"- **Workflows**: {wf}")
    else:
        lines.append("- **Workflows**: -")

    return "\n".join(lines)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print("📥 파일 로드 중...")
    ref_data = load_reference_csv()
    body_data = load_body_csv()
    campaigns = parse_markdown()

    print(f"  - 캠페인 {len(campaigns)}개 파싱 완료")
    print(f"  - CSV 참고 데이터 {len(ref_data)}개 로드 완료")
    print(f"  - Body CSV {len(body_data)}개 로드 완료")

    tickets = []
    for c in campaigns:
        desc = build_description(c, ref_data, body_data)
        summary = f"[ABC이관] {c['campaign_name']}"
        tickets.append({
            "index": c["index"],
            "ad_code": c["ad_code"],
            "campaign_name": c["campaign_name"],
            "summary": summary,
            "description": desc,
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(tickets, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(tickets)}개 티켓 데이터 저장 완료: {OUTPUT_FILE}")

    # 미리보기
    print("\n--- 티켓 목록 ---")
    for t in tickets:
        print(f"  {t['index']:2d}. [{t['ad_code']}] {t['campaign_name'][:50]}")

if __name__ == "__main__":
    main()
