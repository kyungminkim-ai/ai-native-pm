# 마케팅 구좌관리 앱푸시 운영 에이전트

## 역할

[앱푸시 발송 운영] 시트(비제스트 RAW)에 올라온 소재 요청을 자동으로 처리하는 에이전트.
소재 선별 → 메타데이터 생성 → LLM 메시지 작성 → 캠페인메타엔진 운영 시트 형식으로 출력.

---

## 목적

| 구분 | 내용 |
|------|------|
| 비즈니스 목표 | 마케터의 소재 선별·메시지 작성 공수 제거 |
| 실험 목표 | LLM이 안정적인 발송 가능 문구를 생성할 수 있는지 검증 |
| 최종 산출물 | 캠페인메타엔진 운영 시트 형식 CSV (채울 수 있는 컬럼 최대 채워서 출력) |

---

## 입력 파일 (input/)

| 파일 | 설명 |
|------|------|
| `bizest_raw.csv` | [앱푸시 발송 운영] 시트 — 소재 요청 원본 |
| `brand_list.csv` | 브랜드 목록 (brand_id → brand_nm, brand_nm_eng 매핑) |
| `category_selector.csv` | 카테고리 코드 목록 |

> 향후: Google Spreadsheet 연동으로 자동 수집 예정 (현재는 파일 업로드 방식)

---

## 실행 방법

```
/push-campaign --date YYYY-MM-DD [--input PATH]
```

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--date` | 내일 날짜 (D-0) | 발송일 (send_dt) |
| `--input` | `input/bizest_raw.csv` | 비제스트 RAW CSV 경로 |

### 날짜 표현 규칙

| 표현 | 해석 |
|------|------|
| 오늘 | 오늘 날짜 |
| 내일 | 오늘 + 1일 |
| 이번 주 | 이번 주 월요일 ~ 일요일 (7일) |
| **다음 주** | **다음 주 월요일 ~ 일요일 (7일)** |
| 다음주 월요일 | 다음 주 첫 번째 월요일 |

> 단일 날짜가 아닌 주 단위 요청 시 → 해당 주 7일 각각 pipeline1을 실행하여 날짜별 선별 결과를 별도 리포트로 출력

### Claude Code 모드 (ANTHROPIC_API_KEY 없을 때)

1. `python3 scripts/run.py --date YYYY-MM-DD` → Pipeline 1 실행 후 `data/pending_jobs_{date}.json` 생성
2. Claude Code가 pending_jobs를 읽고 메시지 생성 → `data/llm_responses_{date}.json` 저장
3. `python3 scripts/run.py --date YYYY-MM-DD` 재실행 → 응답 파일 자동 감지, Pipeline 2-4 완료

---

## 처리 파이프라인

```
[입력] bizest_raw.csv + brand_list.csv
      │
[Pipeline 1 — 소재 선별]
      ├── 취소 여부 필터 (비고란 취소/CANCEL 키워드)
      ├── 랜딩 오픈 시각 검증 (release_start_date_time < 11:00)
      ├── 마케팅팀 예외 처리 (전사마케팅/카테고리마케팅)
      └── 중복 방지 (landing_url + brand + send_dt 조합)
      │
[Pipeline 2 — 메타데이터 & 메시지 생성]
      ├── Rule-based: send_dt, target(성별), priority, content_type, brand_id,
      │              category_id, landing_url, image_url, ad_code, push_url
      └── LLM(Claude): title 검증/재생성, contents V1(혜택강조), V2(브랜드감성)
      │
[Pipeline 3 — 검수 검증 (Validation QA)]
      ├── 필수 필드 누락 체크 (title, contents, landing_url, ad_code)
      ├── title 길이 범위 검증 (15~40자)
      ├── (광고) 접두어 및 수신거부 문구 확인
      ├── push_url UTM 파라미터 정합성 검증
      ├── 할인율 0% 표기 차단
      ├── landing_url https 형식 검증
      ├── ad_code 중복 검사
      └── LLM confidence 임계값 미달 플래그
      │ (행 제거 없이 [검수용] 컬럼에 이슈 내용 기록)
      │
[Pipeline 4 — LLM Red Team 검토]
      ├── 생성 규칙과 독립된 관점에서 LLM이 재검토
      ├── 평가 기준: 정확성·수신자반응·브랜드일관성·차별성·문제여부
      ├── review_score (1.0~5.0), review_verdict (pass/warning/fail)
      ├── review_notes, review_issues 컬럼 추가
      └── warning/fail → needs_review 플래그 상향
      │ (행 제거 없이 [검수용] 컬럼에 기록)
      │
[출력] output/campaign_meta_{YYYYMMDD}_{timestamp}.csv
```

---

## 소재 선별 기준 (Pipeline 1)

1. **취소 제외**: remarks에 `취소`, `CANCEL`, `cancel` 포함 시 제외
2. **랜딩 오픈 검증**: `release_start_date_time < send_dt 11:00` (KST) 조건
3. **마케팅팀 예외**: `register_team_name`에 `전사마케팅` 또는 `카테고리마케팅` 포함 시 랜딩 오픈 여부 무관하게 선별
4. **중복 방지**: `landing_url + sourceBrandId + send_dt` 조합 중복 시 id 오름차순 첫 번째만 유지

상세 정책: `references/selection_policy.md`

---

## 메타데이터 생성 기준 (Pipeline 2)

### Rule-based 컬럼

| 컬럼 | 생성 방식 |
|------|----------|
| `send_dt` | `release_start_date_time` 날짜 부분 추출 |
| `send_time` | 고정 `11:00` |
| `target` | 팀명 기반 성별: 여성→`여성`, 남성→`남성`, 그 외→`전체` |
| `priority` | URL 패턴 + 팀명 기반 우선순위 정수 |
| `ad_code` | `APSCMCD` + BASE36 순번 |
| `content_type` | landing_url 패턴: `/campaign/`→캠페인, `/content/`→콘텐츠 |
| `brand_id` | `sourceBrandId` 직접 복사 |
| `category_id` | 팀명 임시 매핑 테이블 기반 |
| `landing_url` | RAW 직접 복사 |
| `image_url` | RAW `img_url` 직접 복사 |
| `push_url` | `landing_url?utm_source=app_push&utm_medium=cr&...` |

### LLM(Claude API) 생성 컬럼

| 컬럼 | 조건 | 규격 |
|------|------|------|
| `title` | `main_title`이 15~40자 + 브랜드/혜택 키워드 포함이면 원본 사용, 그 외 LLM 재생성 | 15~40자, 명사형 종결 |
| `contents` (V1 BENEFIT) | 모든 선정 소재 | `(광고) ` 시작, 40~60자, 혜택 수치 강조 |
| `contents` (V2 BRAND) | 모든 선정 소재 | `(광고) ` 시작, 25~45자, 브랜드 감성 |

> Phase 1은 V1, V2 모두 생성 후 담당자가 선택. 운영 시트에는 V1을 기본 `contents`로, V2는 별도 컬럼 `contents_v2`로 병기.

상세 정책: `references/message_policy.md`

---

## 출력 형식 (캠페인메타엔진 운영 시트)

```
send_dt, send_time, target, priority, ad_code, content_type,
goods_id, category_id, brand_id, team_id, braze_campaign_name,
title, contents, landing_url, image_url,
push_url, feed_url, webhook_contents, stopped
```

**검수용 컬럼 (담당자 검토 후 Braze 등록 시 제외):**
```
[검수용] contents_v2, [검수용] title_source,
[검수용] confidence_v1, [검수용] confidence_v2,
[검수용] error_flag, [검수용] needs_review, [검수용] validation_notes,
[검수용] review_score, [검수용] review_verdict,
[검수용] review_notes, [검수용] review_issues
```

> `goods_id`, `team_id`, `braze_campaign_name`, `feed_url`, `webhook_contents`, `stopped`은 자동화 대상 외 컬럼 — 공란 또는 시트 내 함수 처리
> `contents`는 V1(혜택강조) 기본 적용, V2(브랜드감성)는 `[검수용] contents_v2`로 병기

---

## 오류 처리

| 상황 | 처리 |
|------|------|
| Claude API 3회 실패 | `title/contents=null`, `error_flag=True`, 이후 소재 계속 처리 |
| 입력 파일 없음 | 오류 메시지 출력 후 종료 |
| 선별 소재 0건 | 경고 메시지 출력 (정상 0건과 구분) |
| send_dt 미지정 | 내일 날짜 자동 사용 |

---

## 향후 확장 (Phase 2+)

- Google Spreadsheet API 연동 (현재 파일 업로드 → 자동 읽기/쓰기)
- Databricks 연동 (비제스트 RAW 직접 쿼리)
- Slack 검수 알림 자동화
- 성과 데이터 피드백 → RAG 기반 메시지 개선
