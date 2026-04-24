# /push-campaign — 앱푸시 캠페인 소재 선별 & 메시지 생성

## 모델

`claude-sonnet-4-6`

## 개요

마케팅 구좌관리 요청(비제스트 RAW)에서 발송 가능한 소재를 선별하고,
캠페인메타엔진 운영 시트 형식으로 메타데이터 + LLM 메시지를 생성하는 스킬.

---

## 사용법

```
/push-campaign
/push-campaign --date 2026-05-01
/push-campaign --date 2026-05-01 --input input/my_raw.csv
```

---

## 실행 규칙

### Step 0: 입력 파일 확인
```python
# 필수 파일 존재 여부 확인
INPUT_FILES = [
    "input/bizest_raw.csv",    # 비제스트 RAW (필수)
    "input/brand_list.csv",    # 브랜드 목록 (필수)
]
# category_selector.csv는 선택 (없으면 category_id 공란)
```

send_dt 미지정 시 → 내일 날짜(D+1) 자동 사용

### Step 1: Pipeline 1 — 소재 선별
```bash
python3 scripts/run.py --stage pipeline1 --date {YYYY-MM-DD} --input {CSV_PATH}
# 출력: data/pipeline1_output_{date}.csv
```

선별 기준 (순서대로 적용):
1. remarks에 취소 키워드 → 제외
2. 처리 이력 중복 → 제외
3. 시트 기입력 중복 → 제외
4. 마케팅팀(전사마케팅/카테고리마케팅) → 무조건 선별
5. release_start_date_time < send_dt 11:00 → 선별
6. 그 외 → 제외

완료 후 선별 통계 출력:
```
[Pipeline 1 완료]
전체 소재: {N}건
선별: {M}건 / 제외: {N-M}건
제외 사유: 취소={a}건, 미오픈={b}건, 중복={c}건
```

### Step 2: Pipeline 2~4 — 메시지 생성 + 검수 + Red Team
```bash
python3 scripts/run.py --stage all --date {YYYY-MM-DD}
# 입력: data/pipeline1_output_{date}.csv (Pipeline 1 결과)
# 출력: output/campaign_meta_{YYYYMMDD}_{timestamp}.csv
```

개별 파이프라인 단계 실행:
```bash
python3 scripts/run.py --stage pipeline2 --date {YYYY-MM-DD}  # 메타데이터 & 메시지 생성
python3 scripts/run.py --stage pipeline3 --date {YYYY-MM-DD}  # 검수 검증
python3 scripts/run.py --stage pipeline4 --date {YYYY-MM-DD}  # LLM Red Team 검토
```

Pipeline 2 처리 (소재별):
1. Rule-based 컬럼 생성 (send_dt, target, priority, content_type, brand_id, ad_code 등)
2. 제목 적합성 판단 → 부적합 시 LLM 재생성
3. V1 BENEFIT 본문 생성 (LLM)
4. V2 BRAND 본문 생성 (LLM)

> Pipeline 2 중간 결과는 파일로 저장되지 않음. `--stage all`로 Pipeline 1 → 4를 한 번에 실행 권장.

Pipeline 3 처리 (검수 검증 QA):
- 필수 필드 누락, title 길이, (광고) 접두어, UTM 정합성, 0% 차단 등 검증
- 행 제거 없이 `[검수용]` 컬럼에 이슈 기록

Pipeline 4 처리 (LLM Red Team):
- 생성 규칙과 독립된 관점에서 LLM이 재검토
- `review_score`(1.0~5.0), `review_verdict`(pass/warning/fail) 컬럼 추가
- warning/fail → `[검수용] needs_review` 플래그 상향

### Step 3: 검수 요약 보고
스킬 완료 후 다음 형식으로 사용자에게 보고:

```
[push-campaign 완료]

📊 처리 결과:
  전체 소재: {N}건 → 선별: {M}건
  LLM 생성 성공: {K}건 / 실패: {N-K}건
  검수 필요 (confidence < 3.0): {P}건

📁 산출물:
  output/campaign_meta_{YYYYMMDD}_{timestamp}.csv

⚠️ 검수 필요 항목: [{목록}]
```

---

## 에러 처리

| 상황 | 처리 |
|------|------|
| 필수 입력 파일 없음 | 오류 메시지 + 파일 위치 안내 후 중단 |
| 선별 소재 0건 | 경고 출력 후 빈 CSV 생성 |
| Claude API 3회 연속 실패 | `error_flag=True` 표시, 해당 소재만 스킵 |
| 잘못된 날짜 형식 | 형식 오류 안내 (YYYY-MM-DD 요구) |

---

## 참조 문서

- 소재 선별 정책: `references/selection_policy.md`
- 메시지 생성 정책: `references/message_policy.md`
- 무신사 브랜드 가이드: `references/brand_guidelines.md`
- 오케스트레이터: `CLAUDE.md`
