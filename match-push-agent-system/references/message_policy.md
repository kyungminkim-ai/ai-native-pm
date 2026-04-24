# 메시지 생성 정책 (Pipeline 2)

출처: [Sub-PRD] 세일즈푸시(11시) 메타데이터 생성 정책 (Confluence 403703281)

---

## I/O 명세

| 항목 | 내용 |
|------|------|
| 입력 | Pipeline 1 출력 DataFrame (`selected=True` 소재) |
| 출력 | Rule-based 컬럼 + V1/V2 메시지 + 광고코드 + push_url 포함 완성 DataFrame |
| LLM 모델 | `claude-sonnet-4-6` |
| 소요 시간 목표 | 전체 300건 기준 ~10분 이내 (병렬 처리 시) |

---

## 처리 단계

각 소재는 아래 6단계를 순서대로 거침.

```
소재 1건
   │
[Step 1] 성별 분류 (Rule-base) → target: 전체/여성/남성
   │
[Step 2] 제목 적합성 판단 (Rule-base)
   │ 적합 → title_source=original
   │ 부적합 → LLM 재생성 → title_source=llm / fallback
   │
[Step 3] V1 BENEFIT 본문 생성 (LLM)
   │ contents_v1, confidence_v1
   │
[Step 4] V2 BRAND 본문 생성 (LLM)
   │ contents_v2, confidence_v2
   │
[Step 5] 광고 코드 생성 (Rule-base)
   │ ad_code (APSCMCD + BASE36 순번)
   │
[Step 6] push_url 생성 (Rule-base)
   │ push_url = landing_url + UTM 파라미터
완성
```

---

## Rule-based 처리

### Step 1: 성별 분류 (target)

```python
GENDER_MAP = {
    "여성": "여성",  # register_team_name에 "여성" 포함
    "남성": "남성",  # register_team_name에 "남성" 포함
    # 그 외 → "전체"
}
```

| 우선순위 | 팀명 패턴 | target |
|---------|---------|--------|
| 1 | "여성" 포함 | 여성 |
| 2 | "남성" 포함 | 남성 |
| 3 | 그 외 / NULL | 전체 |

### Step 2: 제목 적합성 판단

**적합 기준 (original 사용):**

| 기준 | 상세 |
|------|------|
| 길이 | 15자 이상 40자 이하 |
| 의미 | 브랜드명 or 혜택 키워드 포함 |
| 가독성 | 의미 없는 숫자·코드 패턴 아님 |

**부적합 기준 (LLM 재생성):**

| 케이스 | 예시 |
|--------|------|
| NULL 또는 공백 | `""` |
| 15자 미만 | `"세일"`, `"123"` |
| 40자 초과 | URL 형태 등 |
| 의미 없는 값 | `"테스트"`, `"123123"`, `"asdf"` |
| 영문 코드만 존재 | `"INSALES_2Q_0412"` |

**LLM 재생성 실패 시** → `original_title` 그대로 사용 + `title_source="fallback"`

### Step 3: content_type 결정

```python
if "/campaign/" in landing_url:
    content_type = "캠페인"
elif "/content/" in landing_url:
    content_type = "콘텐츠"
else:
    content_type = None
```

### Step 4: priority 결정

```python
# URL 패턴 + 팀명 기반 우선순위
PRIORITY_RULES = {
    # 팀명에 "전사마케팅" 포함 → priority 1 (최우선)
    # 팀명에 "카테고리마케팅" 포함 → priority 2
    # 그 외 → priority 3
}
```

### Step 5: 광고 코드 (ad_code)

- 형식: `APSCMCD` + BASE36 순번 (3자리, 예: `APSCMCD386`)
- 최근 마지막 코드에서 +1씩 자동 채번
- 이력 없을 경우 `input/ad_code_seed.txt`의 시드값 사용

### Step 6: push_url 생성

```python
UTM = "utm_source=app_push&utm_medium=cr&utm_content=mf&utm_campaign={ad_code}&source={ad_code}"
separator = "&" if "?" in landing_url else "?"
push_url = f"{landing_url}{separator}{UTM}"
```

---

## LLM 메시지 생성

### 공통 설정

| 항목 | 값 |
|------|---|
| 모델 | `claude-sonnet-4-6` |
| max_tokens | 512 |
| 출력 형식 | JSON only |
| 재시도 | 최대 3회 (지수 백오프: 1s → 2s → 4s) |
| API 오류 시 | `null` 기록 + `error_flag=True` |

### V1 BENEFIT 본문 규격

| 항목 | 내용 |
|------|------|
| 시작 | 반드시 `(광고) `로 시작 |
| 길이 | 40~60자 (수신거부 문구 제외) |
| 스타일 | 혜택 수치 강조 (할인율 %, 쿠폰, 적립금) |
| 연결 | 복수 혜택은 `+`로 연결 |
| 종결 | 명사형 (`...증정`, `...혜택`) |
| 금지 | 감탄사·과장어 (대박, 놀라운), 명령조, 모호한 표현 |

좋은 예시:
- `(광고) 최대 30% 쿠폰 + 최대 5만원 적립금 + 최대 1만원 결제혜택`
- `(광고) 최대 80% 할인 + 단 하루 25% 쿠폰`

### V2 BRAND 본문 규격

| 항목 | 내용 |
|------|------|
| 시작 | 반드시 `(광고) `로 시작 |
| 길이 | 25~45자 (수신거부 문구 제외) |
| 스타일 | 브랜드/제품 고유성·차별성 감성 표현 |
| 수치 | 최소화 (혜택 나열 금지 — V1과 중복 방지) |
| 금지 | 명령조, 일반 형용사 반복 (좋은, 멋진), 혜택 수치 나열 |

좋은 예시:
- `(광고) 올 블랙보다 시크한 그레이 스티치의 존재감`
- `(광고) 다시 시작되는 그들의 이야기를 담은 굿즈, 무신사 드롭 발매`

### 수신거부 문구 (후처리 추가)

LLM은 본문만 생성하고, 수신거부 문구는 Python이 후처리로 추가:
```python
UNSUBSCRIBE = "수신거부 : 메인 상단 알림 > 설정 > 알림 OFF"
final_content = f"{llm_message}\n{UNSUBSCRIBE}"
```

---

## 출력 컬럼 명세

| 컬럼명 | 타입 | 생성 방식 | 설명 |
|--------|------|----------|------|
| `send_dt` | date | Rule | YYYY-MM-DD |
| `send_time` | string | 고정 | `11:00` |
| `target` | string | Rule | 전체/여성/남성 |
| `priority` | int | Rule | 1~3 (낮을수록 높은 우선순위) |
| `ad_code` | string | Rule | `APSCMCD###` BASE36 |
| `content_type` | string | Rule | 캠페인/콘텐츠 |
| `goods_id` | string | 공란 | 자동화 대상 외 |
| `category_id` | string | Rule | 팀명 임시 매핑 |
| `brand_id` | string | Rule | `sourceBrandId` 직접 복사 |
| `team_id` | string | 공란 | 자동화 대상 외 |
| `braze_campaign_name` | string | 공란 | 자동화 대상 외 |
| `title` | string | LLM/original | 앱푸시 제목 |
| `contents` | string | LLM (V1) | V1 BENEFIT 본문 (수신거부 포함) |
| `contents_v2` | string | LLM (V2) | V2 BRAND 본문 (수신거부 포함) |
| `landing_url` | string | Rule | RAW 직접 복사 |
| `image_url` | string | Rule | RAW `img_url` 직접 복사 |
| `push_url` | string | Rule | UTM 파라미터 포함 URL |
| `feed_url` | string | 공란 | 시트 내 함수 처리 |
| `webhook_contents` | string | 공란 | 시트 내 함수 처리 |
| `stopped` | string | 공란 | 자동화 대상 외 |
| `[검수용] title_source` | string | Rule | original/llm/fallback |
| `[검수용] confidence_v1` | float | LLM | 1.0~5.0 |
| `[검수용] confidence_v2` | float | LLM | 1.0~5.0 |
| `[검수용] error_flag` | bool | Rule | LLM 실패 여부 |
