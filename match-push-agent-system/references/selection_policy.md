# 소재 선별 자동화 정책 (Pipeline 1)

출처: [Sub-PRD] 세일즈푸시(11시) 소재 선별 자동화 정책 (Confluence 403768249)

---

## I/O 명세

| 항목 | 내용 |
|------|------|
| 입력 | `input/bizest_raw.csv` (비제스트 RAW 소재 요청) |
| 출력 | `selected=True` 소재 DataFrame → Pipeline 2 입력 |
| 선별 리포트 | `output/selection_report_{YYYYMMDD}.csv` (선별+탈락 전체, 사유 포함) |
| 실행 시각 | D-1 09:30 (배치 기준) |
| 예상 입력 건수 | ~1,000건 (전체 RAW) |
| 예상 출력 건수 | 240~320건 (선정 소재) |

---

## 입력 컬럼 (비제스트 RAW)

| 컬럼명 | 설명 |
|--------|------|
| id | 비제스트 소재 고유 ID |
| ad_status | 선정 여부 (원본 컬럼명: 한국어 헤더, `Unnamed: 0` → `ad_status` 리네임) |
| requested_start_date_time | 요청 등록 시각 |
| release_start_date_time | 랜딩 오픈 시각 |
| sourceBrandId | 브랜드 ID (brand_list.csv 매핑 가능) |
| event_name | 이벤트명 |
| main_title | 소재 제목 |
| promotion_content | 프로모션 내용 |
| landing_url | 랜딩 URL |
| img_url | 이미지 URL |
| remarks | 비고 |
| register_team_name | 요청팀 이름 |

---

## 선별 조건 (순서대로 적용)

### 조건 1: 취소 여부 (remarks)

| 항목 | 내용 |
|------|------|
| 대상 필드 | `remarks` |
| 제외 키워드 | `취소`, `CANCEL`, `cancel` (부분 문자열, 대소문자 무시) |
| 탈락 코드 | `CANCELLED` |

### 조건 2: 선정 여부 (ad_status)

| 항목 | 내용 |
|------|------|
| 대상 필드 | `ad_status` (원본: 비제스트 RAW 첫 번째 컬럼) |
| 제외 기준 | `광고진행` 문자열 포함 (예: 광고진행, 광고진행완료 등) |
| 통과 기준 | `광고미진행`, 비어있음, NULL |
| 탈락 코드 | `ALREADY_SELECTED` |
| 목적 | 이미 다른 채널에서 집행 중/완료된 소재 중복 발송 방지 |

### 조건 3: 중복 방지

| 단계 | 기준 키 | 참조 파일 | 탈락 코드 |
|------|---------|----------|----------|
| 3-1. 이력 기반 (id) | 비제스트 `id` | `data/processed_ids.csv` | `ALREADY_PROCESSED` |
| 3-2. URL 발송 이력 | `landing_url` | `data/processed_urls.csv` | `URL_ALREADY_SENT` |
| 3-3. 시트 기반 | `landing_url + sourceBrandId + send_dt` | 당일 시트 내 | `SHEET_DUPLICATE` |

### 조건 4: 발송 윈도우 검증 (전 항목 적용)

| 항목 | 내용 |
|------|------|
| 대상 필드 | `release_start_date_time` |
| 통과 기준 | `D-1 10:00 ≤ release_start_date_time < D-0 10:00` (KST) |
| 목적 | 전일 10시~당일 10시 사이에 오픈된 소재만 선별 |
| 선별 코드 | `LANDING_IN_WINDOW` (잠정 — URL 검증 후 최종 확정) |
| 탈락 코드 | `LANDING_NOT_IN_WINDOW` |
| 적용 범위 | **전 항목 동일 적용** (팀 유형 예외 없음) |

> `SEND_HOUR = 10`, `SEND_WINDOW_START_HOUR = 10`, `SEND_WINDOW_DAYS = 1`
> → 팀 유형에 무관하게 동일 윈도우 적용. 과거 오픈 소재(예: 2주 전)는 자동 제외.

### 조건 5: 랜딩 URL 유효성 검증 (윈도우 통과 항목에 한해 적용)

윈도우를 통과한 소재에 대해 추가로 URL 유효성을 검증한다.
URL 탈락 항목은 **선별 리포트에는 포함**되나 **Pipeline 2 이후로 진행하지 않는다**.

| 탈락 코드 | 조건 | 예시 |
|----------|------|------|
| `URL_MISSING` | `landing_url` 없음 (null/빈값) | — |
| `URL_FORMAT` | `http`로 시작하지 않는 형식 | `nan`, 빈 문자열 |
| `URL_PLACEHOLDER` | URL에 한국어 포함 또는 `TBD` 임시값 | `content/추후기재`, `HTTPS://TBD` |
| `URL_NOT_MUSINSA` | `musinsa.com` 외부 도메인 | Google Drive 등 |
| `URL_NO_ID` | `/content/` 또는 `/campaign/` 경로에 유효 ID 없음 | `/content/`, `/content/1` |

> URL 탈락 항목은 `rejection_reason`에 코드가 기록되며, `selected=False`로 처리된다.

---

## 선별 플로우

```
비제스트 RAW 소재 (전체)
      │
[조건 1] remarks에 취소 키워드 포함?
      → Yes → ❌ CANCELLED
      │ No
[조건 2] ad_status에 '광고진행' 계열 포함?
      → Yes → ❌ ALREADY_SELECTED
      │ No
[조건 3-1] id가 처리 이력(processed_ids.csv)에 존재?
      → Yes → ❌ ALREADY_PROCESSED
      │ No
[조건 3-2] landing_url이 발송 이력(processed_urls.csv)에 존재?
      → Yes → ❌ URL_ALREADY_SENT
      │ No
[조건 3-3] landing_url+brand+send_dt 조합이 당일 시트에 존재?
      → Yes → ❌ SHEET_DUPLICATE
      │ No
[조건 4] D-1 10:00 ≤ release_start_date_time < D-0 10:00?
      → No  → ❌ LANDING_NOT_IN_WINDOW
      │ Yes (발송 윈도우 통과 → 후보군 진입)
[조건 5] landing_url 유효성 검증
      → URL_MISSING       → ❌ (선별 리포트에 포함, Pipeline 2 제외)
      → URL_FORMAT        → ❌ (선별 리포트에 포함, Pipeline 2 제외)
      → URL_PLACEHOLDER   → ❌ (선별 리포트에 포함, Pipeline 2 제외)
      → URL_NOT_MUSINSA   → ❌ (선별 리포트에 포함, Pipeline 2 제외)
      → URL_NO_ID         → ❌ (선별 리포트에 포함, Pipeline 2 제외)
      → 정상              → ✅ LANDING_IN_WINDOW → Pipeline 2 진행
```

---

## 처리 이력 관리

| 파일 | 기록 시점 | 컬럼 |
|------|----------|------|
| `data/processed_ids.csv` | Pipeline 1 완료 시 | `id`, `send_dt`, `processed_at` |
| `data/processed_urls.csv` | 최종 산출물(`campaign_meta_*.csv`) 저장 후 | `landing_url`, `send_dt`, `processed_at` |

- 첫 실행 시 파일 없어도 빈 set으로 초기화 (오류 아님)
- `processed_urls.csv`는 `landing_url` 기준 중복 제거 후 누적 저장

---

## 선별 리포트 (`output/selection_report_{YYYYMMDD}.csv`)

선별 + 탈락 소재 전체를 한 파일로 출력 (선별 먼저, 탈락 나중 정렬):

| 컬럼 | 설명 |
|------|------|
| `ad_status` | 원본 선정 여부 값 |
| `id` | 비제스트 소재 ID |
| `register_team_name` | 요청팀 |
| `sourceBrandId` | 브랜드 ID |
| `main_title` | 소재 제목 |
| `landing_url` | 랜딩 URL |
| `release_start_date_time` | 랜딩 오픈 시각 |
| `requested_start_date_time` | 요청 등록 시각 |
| `remarks` | 비고 |
| `selected` | 선별 여부 (True/False) |
| `selection_reason` | 선별 사유 코드 |
| `rejection_reason` | 탈락 사유 코드 |
| `rejection_detail` | 탈락 세부 내용 |

---

## 예외 처리

| 상황 | 처리 |
|------|------|
| `release_start_date_time` NULL | 발송 윈도우 미충족으로 처리, 마케팅팀 아니면 제외 |
| `ad_status` NULL / 비어있음 | `광고미진행`으로 간주 → 조건 2 통과 |
| `register_team_name` NULL | `is_marketing_team=False` 처리, 조건 5로 판단 |
| `landing_url` NULL | URL 이력 체크 스킵, 시트 키 생성 시 빈 문자열 처리 |
| 전체 RAW 0건 | 경고 로그 출력 (정상 실행 0건과 구분) |
