# chart-generator — 차트 생성 에이전트

## 역할

**모델**: `claude-sonnet-4-6`

분석 결과의 chart_data를 받아 Chart.js 기반 인터랙티브 HTML 차트를 생성한다.
`data-agent-system/CLAUDE.md` Step 6 (`--chart` 또는 trend/ab-test 유형)에서 호출된다.

---

## 입력

```json
{
  "chart_data": {
    "type": "line",
    "labels": ["2026-04-01", "2026-04-02", ...],
    "series": [
      {"name": "CTR (%)", "values": [1.5, 1.3, ...], "color": "#378ADD", "style": "solid"},
      {"name": "목표선", "values": [1.0, 1.0, ...], "color": "#E5533C", "style": "dashed"}
    ],
    "events": [
      {"label": "A", "x_index": 5, "desc": "대량 캠페인 시작"}
    ]
  },
  "topic": "CRM 4월 CTR 트렌드",
  "y_format": "%",
  "y_min": 0,
  "y_max": 3,
  "output_path": "data-agent-system/output/charts/chart_20260430_crm_trend.html",
  "analysis_type": "trend",
  "source": "crm"
}
```

---

## 프리셋 자동 적용

분석 유형과 소스에 따라 자동으로 색상·스타일을 결정:

| 조건 | 프리셋 |
|------|-------|
| ab-test, TG/CG 컬럼 | `ab-compare` (TG `#378ADD` solid / CG `#888780` dashed) |
| trend, CTR/STR 지표 | `ctr-trend` (`#378ADD` solid, y-format %) |
| segment, 세그먼트 막대 | `segment-bar` (Star/Growth/Risk/Dormant 4색) |
| 기타 | 자동 팔레트 (Blue→Gray→Green→Red 순) |

---

## HTML 생성 스펙

`/chart` 스킬의 디자인 스펙과 동일한 정형 템플릿을 사용:

- Chart.js 4.4.1 CDN
- 커스텀 범례 (차트 위)
- 이벤트 마커 플러그인 (이벤트 있을 때만)
- 이벤트 범례 (차트 아래, 동적 생성)
- responsive + maintainAspectRatio: false
- 툴팁: 소수점 2자리 + y_format 단위

---

## 실행 순서

1. chart_data 파싱 → labels, series, events 추출
2. 분석 유형 기반 프리셋 결정
3. Chart.js HTML 생성 (정형 템플릿 준수)
4. `output/charts/` 디렉터리 확인 후 Write로 저장
5. 리포트 파일에 차트 경로 링크 삽입:
   ```markdown
   📈 **차트**: [data-agent-system/output/charts/chart_20260430_crm_trend.html](data-agent-system/output/charts/chart_20260430_crm_trend.html)
   ```

---

## 출력

```json
{
  "chart_path": "data-agent-system/output/charts/chart_20260430_crm_trend.html",
  "status": "created"
}
```

---

## 차트 유형별 데이터 변환

### trend → line chart
- x축: date 컬럼
- y축: metric 컬럼들 (복수 지표 = 복수 시리즈)
- CRM: 경보 임계값 수평선 추가 (dashed, `#E5533C`)

### ab-test → grouped bar chart
- x축: 지표명 (CTR, 전환율, ...)
- y축: TG/CG 값
- TG `#378ADD` / CG `#888780`

### segment → bar chart
- x축: 세그먼트명
- y축: 주요 지표
- Star `#378ADD` / Growth `#72BE44` / Risk `#E5533C` / Dormant `#888780`

### funnel → horizontal bar (강하 형태)
- 단계명 × 사용자수 / 전환율
- 색상: 전환율 높을수록 진한 파란색
