# PN-01 관심상품 × 보유쿠폰 가격 넛징

이 폴더는 Databricks 노트북 소스입니다(`# Databricks notebook source` 형식). 매일 Job 이 00 → 01 → 02 → 03 → 04 순서로 실행합니다.

- 위젯과 Job 파라미터를 쓰지 않습니다. 기준일은 각 노트북이 시작할 때 KST 오늘로 계산합니다. 나머지 값은 코드 상수입니다.
- 04 는 `DELIVERY_MODE = "LIVE"` 로 고정돼 있습니다. TEST·PREVIEW 는 상수를 바꿔 수동으로 실행할 때만 씁니다.
- 결과 알림은 시크릿 `kyungmin_inbox_report / slack_webhook_pn01_apppush` 에 넣은 Incoming Webhook 으로만 보냅니다(환경변수는 읽지 않습니다).

## 배포 전 1회

```bash
databricks secrets put-secret kyungmin_inbox_report slack_webhook_pn01_apppush --string-value '<PN-01 Webhook URL>'
```

Webhook URL 은 저장소에 커밋하지 않습니다.
