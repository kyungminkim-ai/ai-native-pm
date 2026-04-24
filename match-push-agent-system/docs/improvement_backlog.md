# 앱푸시 캠페인 자동화 시스템 — 개선 백로그

> 작성일: 2026-04-24
> 현재 구현 상태: Pipeline 1(선별) + Pipeline 2(메시지 생성) + Pipeline 3(검수 검증) + 실행 로그

---

## 우선순위 기준

- **🔴 High** — 지금 당장 발송 품질에 영향. 수동 보정 공수 크거나 리스크 있음
- **🟡 Medium** — 운영 효율화. 누적될수록 효과가 커지는 항목
- **🟢 Low** — 자동화 고도화. Phase 2+ 연동 이후 의미가 생기는 항목

---

## 🔴 High — 빠른 적용 권장

### H-1. contents 길이 검증 추가 (Pipeline 3)

**문제:** V1(40~60자), V2(25~45자) 길이 규칙이 프롬프트에만 있고 Pipeline 3 검증에서 빠져 있음.
LLM이 규칙을 벗어난 문구를 생성해도 `needs_review` 플래그가 뜨지 않음.

**제안:**
```python
# pipeline3.py _check_row() 에 추가
contents_text = contents.replace("(광고) ", "").split("\n")[0]  # 수신거부 전까지
if contents_text and not (40 <= len(contents_text) <= 60):
    issues.append(f"contents_len_{len(contents_text)}chars(expected 40-60)")
```

**예상 효과:** 길이 위반 문구 사전 차단, 수동 검수 시간 감소

---

### H-2. goods_id 자동 추출 (Pipeline 2)

**문제:** `goods_id` 컬럼이 항상 공란 → Braze 등록 시 담당자가 매번 수동 입력.

**제안:** `landing_url` 패턴에서 상품 ID 파싱 시도.

```python
# rules.py 에 추가
import re

def extract_goods_id(landing_url: str) -> str:
    """URL에서 상품 ID 추출. 예: /goods/12345 → '12345'"""
    patterns = [
        r'/goods/(\d+)',
        r'goods_no=(\d+)',
        r'/product/(\d+)',
    ]
    for pat in patterns:
        m = re.search(pat, landing_url or "")
        if m:
            return m.group(1)
    return ""
```

**예상 효과:** goods_id 자동 채움율 50~70% (URL 패턴에 상품 ID가 있는 경우)

---

### H-3. 이미지 URL 유효성 검사 (Pipeline 3)

**문제:** `image_url`을 RAW에서 그대로 복사하므로, 삭제되거나 만료된 이미지 URL이 발송될 수 있음.
이미지 없는 푸시는 CTR에 직접 영향.

**제안:** HTTP HEAD 요청으로 이미지 존재 여부 확인 (타임아웃 2초).

```python
# pipeline3.py 에 추가
import requests

def _is_image_reachable(url: str, timeout: int = 2) -> bool:
    if not url or not url.startswith("http"):
        return False
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return r.status_code < 400
    except Exception:
        return False
```

**주의:** 네트워크 I/O가 추가되므로 건수 많을 경우 병렬 처리 권장 (`concurrent.futures`).
**예상 효과:** 이미지 깨진 상태로 발송되는 케이스 사전 차단

---

## 🟡 Medium — 운영 누적 효과가 큰 항목

### M-1. cross-day 브랜드 발송 이력 경고

**문제:** 현재 중복 체크는 당일(`send_dt`) 기준으로만 동작.
같은 브랜드를 며칠 연속 발송해도 시스템이 감지하지 못해 브랜드 피로도 관리가 안 됨.

**제안:** `logs/` 디렉터리의 실행 로그를 집계해 최근 7일 내 동일 `brand_id` 발송 횟수를 카운트.
2회 이상이면 Pipeline 3에서 `brand_frequency_high(N회)` 경고 추가.

```python
# run_logger.py 또는 pipeline3.py 에 추가
def load_recent_brand_counts(logs_dir: Path, days: int = 7) -> dict:
    """최근 N일 logs/*.json에서 brand_id별 발송 횟수 집계."""
    cutoff = datetime.now() - timedelta(days=days)
    counts = {}
    for log_file in logs_dir.glob("run_*.json"):
        with open(log_file) as f:
            log = json.load(f)
        if datetime.fromisoformat(log.get("started_at", "")) < cutoff:
            continue
        p2 = log.get("pipeline2") or {}
        for brand_id in p2.get("brand_ids_processed", []):
            counts[brand_id] = counts.get(brand_id, 0) + 1
    return counts
```

**예상 효과:** 브랜드 피로도 관리, 오픈율 장기 방어

---

### M-2. 카테고리 매핑 정확도 개선

**문제:** 현재 팀명 키워드 매칭으로 카테고리 코드를 결정 (`아웃도어`→`017` 등).
팀명이 바뀌거나 신규 팀이 생기면 `category_id = ""` 공란이 됨.

**제안 A:** `landing_url` 경로에서 카테고리 코드 직접 파싱.
무신사 URL 패턴: `musinsa.com/category/001` 형태면 `001` 추출 가능.

**제안 B:** `category_selector.csv`를 활용해 URL path + 팀명 2단계 매칭 로직 구현.

```python
# rules.py get_category_id() 개선안
def get_category_id(team_name: str, landing_url: str = "") -> str:
    # 1차: URL에서 카테고리 코드 직접 파싱
    m = re.search(r'/category/(\d{3})', landing_url or "")
    if m:
        return m.group(1)
    # 2차: 기존 팀명 키워드 매핑 fallback
    return _team_name_to_category(team_name)
```

**예상 효과:** `category_id` 공란율 감소, Braze 타겟팅 정확도 향상

---

### M-3. 할인율 수치 일관성 검증

**문제:** LLM이 생성한 contents에 `50% 할인`이라고 써도 실제 `promotion_content`와 수치가 다를 수 있음.
과장 광고 리스크.

**제안:** 생성된 문구에서 % 숫자를 추출해 원본 `promotion_content`의 수치와 비교.

```python
# pipeline3.py 에 추가
def _check_discount_consistency(contents: str, promotion_content: str) -> bool:
    """contents의 할인율 숫자가 promotion_content 내 숫자와 일치하는지 확인."""
    pct_in_contents = set(re.findall(r'(\d+)\s*%', contents))
    pct_in_source   = set(re.findall(r'(\d+)\s*%', promotion_content or ""))
    if not pct_in_contents:
        return True  # 숫자 없으면 체크 불필요
    return bool(pct_in_contents & pct_in_source)  # 교집합이 있어야 함
```

이슈 코드: `discount_pct_mismatch`

**예상 효과:** 허위 광고 문구 사전 차단

---

### M-4. 실행 통계 트렌드 리포트

**문제:** `logs/run_*.json`이 쌓여도 개별 파일을 열어봐야 해서 패턴 파악이 어려움.

**제안:** `scripts/report_logs.py` 추가 — 누적 로그를 집계해 주간 트렌드 CSV 출력.

```
send_dt, total_input, selected, rejected_cancelled, rejected_dedup,
rejected_landing, llm_v1_success_rate, llm_v2_success_rate,
title_original_rate, title_fallback_rate, p3_pass_rate
```

```bash
python3 scripts/report_logs.py --days 30 > output/log_report_20260424.csv
```

**예상 효과:** 선별률/LLM 성공률 트렌드 파악 → 프롬프트 튜닝 근거

---

## 🟢 Low — Phase 2+ 이후 의미가 생기는 항목

### L-1. Slack 검수 알림 자동화

**문제:** 실행 완료 후 담당자가 output 폴더를 직접 열어 확인해야 함.

**제안:** 실행 완료 시 `needs_review` 항목 목록을 Slack DM 또는 채널로 자동 발송.

```python
# run.py finalize 단계에 추가
if reviews > 0:
    slack_notify(f"[앱푸시 자동화] {send_dt} 검수 필요 {reviews}건: {needs_review_ids[:5]}...")
```

**의존:** `/slack` 스킬 연동 또는 Slack Webhook 설정 필요

---

### L-2. LLM 메시지 다양성 (3-variant + 자동 선택)

**문제:** 현재 V1/V2 2개만 생성 후 담당자가 선택 → 선택 피로 존재.

**제안:** 동일 소재에 대해 V1·V2·V3 3개 변형 생성 후 LLM이 자체 스코어링해 가장 높은 점수 1개를 `contents`로 자동 선택. 나머지 2개는 `[검수용]`으로 병기.

**예상 효과:** 담당자 선택 부담 제거, 메시지 품질 향상

---

### L-3. 성과 피드백 루프 (RAG 기반 메시지 개선)

**문제:** 현재 LLM은 과거 캠페인 성과 데이터 없이 생성.
실제로 오픈율이 높았던 문구 패턴을 참조하면 품질 향상 가능.

**제안:** Databricks 연동 후 `campaign_performance` 테이블에서 CTR 상위 문구를 few-shot 예시로 프롬프트에 주입.

```python
# prompts.py build_v1_benefit_prompt() 개선안
top_examples = fetch_top_messages(brand_id=brand_id, top_k=3)  # Databricks
prompt += f"\n\n[참고 — 해당 브랜드 CTR 상위 문구 예시]\n{top_examples}"
```

**의존:** Databricks 연동 (Phase 2+), 성과 데이터 파이프라인 구축 필요

---

### L-4. 브랜드 가이드라인 개인화

**문제:** 현재 `brand_guidelines.md`는 모든 브랜드에 동일 규칙 적용.
특정 브랜드는 별도 금지어나 톤앤매너가 있을 수 있음.

**제안:** `brand_list.csv`에 `tone_guide` 컬럼 추가 → 브랜드별 가이드를 프롬프트에 동적 주입.

```csv
brand_id,brand_nm,brand_nm_eng,tone_guide
nike,나이키,Nike,"스포츠 전문 어투. '최고', '챔피언' 키워드 활용 가능"
adidas,아디다스,adidas,"감성적 어투. 수치보다 라이프스타일 강조"
```

**예상 효과:** 브랜드별 메시지 일관성 향상, 브랜드사 만족도 향상

---

## 구현 순서 권고

```
Phase 1 (현재) : Pipeline 1·2·3 + 실행 로그 ✅ 완료
                 
Phase 1.5      : H-1 contents 길이 검증
                 H-2 goods_id 자동 추출
                 H-3 이미지 URL 유효성 검사
                 M-3 할인율 수치 일관성 검증

Phase 2        : Google Spreadsheet 연동
                 M-1 cross-day 브랜드 발송 이력
                 M-2 카테고리 매핑 개선
                 M-4 실행 통계 트렌드 리포트
                 L-1 Slack 알림

Phase 3        : Databricks 연동
                 L-2 3-variant 자동 선택
                 L-3 성과 피드백 루프
                 L-4 브랜드 가이드라인 개인화
```
