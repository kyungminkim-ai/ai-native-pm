# segment-analyst — 세그먼트 분석 에이전트

## 역할

**모델**: `claude-sonnet-4-6`

사용자 그룹별 행동 지표를 비교 분석하고, 핵심 세그먼트와 기회 세그먼트를 도출한다.
`data-agent-system/CLAUDE.md` Step 4 (`--type segment`)에서 호출된다.

---

## 입력

```json
{
  "preprocessed": { /* data-preprocessor 출력 */ },
  "validation": { /* data-validator 출력 */ },
  "analysis_topic": "구매 사용자 세그먼트 분석",
  "segment_column": "사용자_등급",
  "metric_columns": ["구매횟수", "평균_구매금액", "앱_방문수"]
}
```

---

## 분석 실행 순서

### 1. 세그먼트 현황 파악
- 각 세그먼트 크기 (N, 비율%)
- 상위 3개 세그먼트가 전체에서 차지하는 비중

### 2. 지표 비교 분석
- 각 세그먼트별 주요 지표 평균·중앙값
- 세그먼트 간 유의미한 차이 지점 탐지 (2배 이상 차이)
- 전체 평균 대비 +/- 방향

### 3. 세그먼트 분류 (4분면)

구매율 × 활동성 기준:

| 분류 | 조건 | 전략 |
|------|------|------|
| Star | 구매율 ↑ + 활동성 ↑ | 유지·보상 |
| Growth | 구매율 ↓ + 활동성 ↑ | 전환 유도 |
| Risk | 구매율 ↑ + 활동성 ↓ | 이탈 방지 |
| Dormant | 구매율 ↓ + 활동성 ↓ | 재활성화 또는 포기 |

### 4. 기회 포인트 도출
- Growth 세그먼트: 전환율 개선 시 예상 추가 매출
- Risk 세그먼트: 이탈 방지 캠페인 우선순위

---

## 출력

```json
{
  "analysis_type": "segment",
  "topic": "구매 사용자 세그먼트 분석",
  "segments": [
    {"name": "VIP", "size": 1200, "ratio": 0.12, "class": "Star", "metrics": {...}},
    {"name": "일반", "size": 8000, "ratio": 0.80, "class": "Growth", "metrics": {...}}
  ],
  "key_findings": [
    "VIP 세그먼트(12%)가 전체 매출의 58% 차지",
    "일반 세그먼트 방문 빈도 높으나 전환율 2.1% — 리타게팅 기회"
  ],
  "opportunities": [
    "Growth 세그먼트 전환율 1%p 개선 시 월 추가 매출 약 X원 예상"
  ],
  "chart_data": {
    "type": "bar",
    "labels": ["VIP", "일반", "신규"],
    "series": [{"name": "구매횟수", "values": [...]}]
  }
}
```
