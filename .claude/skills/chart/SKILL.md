---
description: 데이터 파일(CSV)을 Chart.js 기반 인터랙티브 HTML 차트로 변환하는 시각화 스킬. TG/CG 비교·CTR 트렌드·이벤트 마커를 포함한 정형 디자인 출력.
---

# /chart — 차트 생성 스킬

## 모델

`claude-sonnet-4-6`

## 사용법

```
/chart --data [경로] --x [컬럼] --y "[컬럼1,컬럼2]"
/chart --preset ab-compare --data [경로] --x [컬럼] --y "[컬럼1,컬럼2]"
/chart --preset ab-compare --data [경로] --x [컬럼] --y "[컬럼1,컬럼2]" \
       --events "A:2026-03-05:PoC 런칭" --events "B:2026-03-17:Push 런칭"
```

---

## 파라미터

### 필수

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| `--data [경로]` | CSV 파일 경로 | `--data input/ctr_daily.csv` |
| `--x [컬럼명]` | x축 컬럼 | `--x date` |
| `--y "[컬럼1,컬럼2,...]"` | y축 컬럼 (쉼표 구분, 복수) | `--y "tg_ctr,cg_ctr"` |

### 선택 — 스타일

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `--type [line\|bar\|ab-compare]` | 차트 유형 | `line` |
| `--topic "[제목]"` | 차트 설명 텍스트 (aria-label, 파일명 slug에 사용) | 파일명 기반 자동 생성 |
| `--series "[이름]:[색]:[solid\|dashed]"` | 시리즈 스타일 (반복 사용 가능) | 프리셋 또는 자동 색상 |
| `--events "[라벨]:[x값]:[설명]"` | 이벤트 마커 (반복 사용 가능) | 없음 |
| `--y-min [값]` | y축 최솟값 | 데이터 기반 자동 |
| `--y-max [값]` | y축 최댓값 | 데이터 기반 자동 |
| `--y-format [%\|#]` | y축 단위 (% → `1.0%`, # → 숫자) | `#` |
| `--date-range "[시작]~[종료]"` | 차트 제목용 날짜 범위 표시 | 없음 |

### 선택 — 출력

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `--output [html]` | 출력 형식 | `html` |
| `--initiative TM-XXXX` | 이니셔티브 연결 (출력 경로 분기) | 없음 |

---

## 프리셋

프리셋은 `--series` 기본값, 색상 체계, 포맷 등을 한 번에 적용한다.
`--series`를 명시하면 프리셋 기본값이 오버라이드된다.

| 프리셋 | 설명 | 기본 시리즈 |
|--------|------|------------|
| `--preset ab-compare` | TG/CG 비교 (아래 디자인 스펙과 동일) | TG `#378ADD` solid / CG `#888780` dashed |
| `--preset ctr-trend` | CTR 시계열 단일 라인 | `#378ADD` solid, y-format % 자동 적용 |
| `--preset segment-bar` | 세그먼트 막대 비교 | Star `#378ADD` / Growth `#72BE44` / Risk `#E5533C` / Dormant `#888780` |

---

## 출력 경로

```
output/charts/chart_{YYYYMMDD}_{주제slug}.html
```

`--initiative TM-XXXX` 지정 시:
```
output/charts/TM-XXXX/chart_{YYYYMMDD}_{주제slug}.html
```

---

## 실행 규칙

### Step 0. args 파싱

- `--data` 값을 파일 경로로 파싱
- `--x` → x축 컬럼명
- `--y` → 쉼표로 분리하여 y축 컬럼명 배열
- `--series` → 반복 등장할 수 있음 → `[{label, color, style}]` 배열로 수집
- `--events` → 반복 등장할 수 있음 → `[{label, xValue, desc}]` 배열로 수집
- `--preset` → 없으면 기본 line 타입 + 자동 색상 팔레트 적용
- `--y-format %` → y축 callback에 `%` 포맷 적용

### Step 1. 데이터 읽기

Read 도구로 CSV 파일 읽기 → 헤더 파싱 → `--x` 컬럼을 `labels` 배열로, `--y` 컬럼들을 각각 숫자 배열로 추출.

`--events`의 `xValue`가 날짜 문자열인 경우, `labels` 배열에서 해당 값의 인덱스를 찾아 `idx`로 변환.

### Step 2. 시리즈 구성

`--series` 파라미터가 있으면 해당 값 사용.
없으면 프리셋 기본값 또는 아래 자동 색상 팔레트 적용:

```
시리즈 1: #378ADD solid
시리즈 2: #888780 dashed
시리즈 3: #72BE44 solid
시리즈 4: #E5533C solid
```

### Step 3. HTML 생성

아래 **디자인 스펙**을 엄격히 따라 HTML 파일을 생성한다. 스펙에 없는 스타일 임의 추가 금지.

#### 디자인 스펙 (정형 템플릿)

```html
<!-- Chart.js CDN -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>

<!-- 외부 래퍼 -->
<div style="padding: 1rem 0;">

  <!-- 커스텀 범례 (차트 위) -->
  <div style="display:flex;flex-wrap:wrap;gap:16px;margin-bottom:12px;font-size:12px;
              color:var(--color-text-secondary,#888780);align-items:center;">
    <!-- 시리즈마다 반복 -->
    <!-- solid 시리즈: -->
    <span style="display:flex;align-items:center;gap:5px;">
      <span style="width:22px;height:3px;background:{color};display:inline-block;border-radius:2px;"></span>
      {시리즈명}
    </span>
    <!-- dashed 시리즈: -->
    <span style="display:flex;align-items:center;gap:5px;">
      <span style="width:22px;height:3px;background:{color};display:inline-block;
                   border-radius:2px;position:relative;">
        <span style="position:absolute;top:-2px;left:0;right:0;
                     border-top:3px dashed {color};"></span>
      </span>
      {시리즈명}
    </span>
    <!-- 이벤트 마커가 있으면 아래 항목 추가 -->
    <span style="display:flex;align-items:center;gap:5px;">
      <span style="width:10px;height:10px;background:#FAC775;display:inline-block;border-radius:2px;"></span>
      주요 이벤트
    </span>
  </div>

  <!-- 차트 컨테이너 -->
  <div style="position:relative;width:100%;height:320px;">
    <canvas id="chartCanvas" role="img" aria-label="{topic}"></canvas>
  </div>

  <!-- 이벤트 범례 (차트 아래, 이벤트 있을 때만) -->
  <div id="eventLegend"
       style="margin-top:16px;display:flex;flex-wrap:wrap;gap:8px;
              font-size:11px;color:var(--color-text-secondary,#888780);">
    <!-- JS로 동적 생성 -->
  </div>
</div>
```

#### Chart.js 설정 스펙 (정형)

```javascript
// 이벤트 마커 플러그인 (이벤트 있을 때만 포함)
const eventPlugin = {
  id: 'eventLines',
  afterDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    events.forEach(ev => {
      const x = scales.x.getPixelForValue(ev.idx);
      ctx.save();
      // 수직 점선
      ctx.beginPath();
      ctx.moveTo(x, chartArea.top);
      ctx.lineTo(x, chartArea.bottom);
      ctx.strokeStyle = 'rgba(186,117,23,0.5)';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.stroke();
      ctx.setLineDash([]);
      // 원형 라벨
      ctx.fillStyle = '#EF9F27';
      ctx.beginPath();
      ctx.arc(x, chartArea.top + 8, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#412402';
      ctx.font = '500 9px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(ev.label, x, chartArea.top + 8);
      ctx.restore();
    });
  }
};

// Chart 설정
new Chart(document.getElementById('chartCanvas'), {
  type: 'line',                              // bar 타입이면 'bar'
  plugins: events.length ? [eventPlugin] : [],
  data: {
    labels,                                  // x축 배열
    datasets: [
      // 시리즈마다 반복
      {
        label: '{시리즈명}',
        data: {데이터배열},
        borderColor: '{color}',
        backgroundColor: '{color에 0.08 알파 적용}',
        borderWidth: 2,
        borderDash: [],                      // dashed면 [5, 3]
        pointRadius: 0,
        fill: false,
        tension: 0.3
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => {
            const val = ctx.parsed.y.toFixed(2);
            return ctx.dataset.label + ': ' + val + (yFormat === '%' ? '%' : '');
          }
        }
      }
    },
    scales: {
      x: {
        ticks: {
          autoSkip: true,
          maxTicksLimit: 12,
          maxRotation: 0,
          color: '#888780',
          font: { size: 11 }
        },
        grid: { color: 'rgba(136,135,128,0.15)' }
      },
      y: {
        min: {yMin},                         // 지정 없으면 생략
        max: {yMax},                         // 지정 없으면 생략
        ticks: {
          callback: v => {
            if (yFormat === '%') return v.toFixed(1) + '%';
            return v;
          },
          color: '#888780',
          font: { size: 11 }
        },
        grid: { color: 'rgba(136,135,128,0.15)' }
      }
    }
  }
});

// 이벤트 범례 동적 생성
const legend = document.getElementById('eventLegend');
events.forEach(ev => {
  const span = document.createElement('span');
  span.style.cssText = 'display:flex;align-items:center;gap:4px;margin-right:8px;';
  span.innerHTML = `<span style="width:16px;height:16px;border-radius:50%;background:#EF9F27;
    display:inline-flex;align-items:center;justify-content:center;font-size:9px;
    font-weight:500;color:#412402;flex-shrink:0;">${ev.label}</span> ${ev.desc}`;
  legend.appendChild(span);
});
```

### Step 4. 파일 저장

`output/charts/` 디렉터리가 없으면 Bash로 생성 후 Write 도구로 HTML 파일 저장.

파일명: `chart_{YYYYMMDD}_{주제slug}.html`
- 주제 slug: `--topic` 값을 소문자·공백→`_`·한글 제거 없이 그대로 사용 (최대 40자)

### Step 5. 완료 보고

```
[분석팀] 차트 생성 완료

📊 {topic}
📁 output/charts/chart_{YYYYMMDD}_{slug}.html

시리즈: {시리즈명 목록}
이벤트 마커: {이벤트 수}개
```

---

## 사용 예시

```bash
# 이 디자인과 동일한 TG/CG CTR 트렌드
/chart --preset ab-compare \
  --data input/auxia_poc_ctr.csv \
  --x date --y "tg_ctr,cg_ctr" \
  --series "TG:#378ADD:solid" --series "CG:#888780:dashed" \
  --events "A:2026-03-05:PoC 런칭" \
  --events "B:2026-03-17:Push 전체 런칭" \
  --events "C:2026-03-26:TG 트래픽 100%" \
  --y-min 0.3 --y-max 1.5 --y-format % \
  --topic "Auxia PoC CTR 일별 추이 (TG vs CG)"

# CTR 트렌드 단일 라인
/chart --preset ctr-trend \
  --data input/weekly_ctr.csv \
  --x week --y "ctr" \
  --topic "주차별 앱푸시 CTR 트렌드"

# 세그먼트 막대 비교
/chart --preset segment-bar \
  --data input/segment_metrics.csv \
  --x segment --y "purchase_rate,retention_rate" \
  --topic "세그먼트별 구매율·리텐션 비교"

# /analyst 결과 연동 (분석 후 차트 추가)
# analyst 리포트의 집계 테이블을 CSV로 저장 →
/chart --data analyst-agent-system/output/trend_data.csv \
  --x date --y "value" \
  --topic "DAU 트렌드" --initiative TM-2061
```

---

## /analyst 연동

`/analyst` 실행 결과 리포트에 차트 경로를 자동 첨부하려면:

```bash
# 1. analyst 실행
/analyst --file input/data.csv --type trend --topic "CTR 분석"

# 2. analyst 리포트 내 집계 테이블 → CSV 수동 저장 또는 자동 추출 후
/chart --data analyst-agent-system/output/aggregated.csv \
  --x date --y "tg,cg" --preset ab-compare
```

향후 `/analyst --chart` 플래그로 자동 연동 지원 예정.
