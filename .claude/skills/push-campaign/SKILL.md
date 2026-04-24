# /push-campaign — 앱푸시 캠페인 소재 선별 & 메시지 생성

## 모델

`claude-sonnet-4-6`

## 개요

[앱푸시 발송 운영] 시트(비제스트 RAW)에서 발송 소재를 선별하고,
캠페인메타엔진 운영 시트 형식으로 메타데이터 + LLM 메시지를 생성하는 스킬.

에이전트 시스템: `match-push-agent-system/`
상세 규칙: `match-push-agent-system/CLAUDE.md`

---

## 사용법

```
/push-campaign
/push-campaign --date 2026-05-01
/push-campaign --date 2026-05-01 --input match-push-agent-system/input/my_raw.csv
```

---

## 실행 규칙

### 1. 입력 파일 확인

```
match-push-agent-system/input/bizest_raw.csv   ← [앱푸시 발송 운영] 시트 (필수)
match-push-agent-system/input/brand_list.csv   ← 브랜드 목록 (필수)
```

send_dt 미지정 → 내일 날짜 자동 사용

### 2. 실행

```bash
cd match-push-agent-system
pip install -r requirements.txt  # 최초 1회
python3 scripts/run.py --date {YYYY-MM-DD}
```

### 3. 완료 보고 형식

```
[push-campaign 완료]

📊 처리 결과:
  선별 소재: {N}건
  LLM 생성 성공: {K}건
  검수 필요: {P}건

📁 산출물:
  match-push-agent-system/output/campaign_meta_{YYYYMMDD}_{HHmmss}.csv

⚠️ 검수 필요 항목: [{id 목록}]
```

---

## 참조

- 오케스트레이터: `match-push-agent-system/CLAUDE.md`
- 소재 선별 정책: `match-push-agent-system/references/selection_policy.md`
- 메시지 생성 정책: `match-push-agent-system/references/message_policy.md`
- 브랜드 가이드라인: `match-push-agent-system/references/brand_guidelines.md`
