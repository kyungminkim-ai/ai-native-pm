---
description: Databricks CRM·Amplitude·파일 데이터를 조회·분석·시각화하는 통합 데이터 에이전트. 조회→분석→차트 3레이어 파이프라인.
---

# /data — 통합 데이터 에이전트

## 모델

`claude-sonnet-4-6`

## 사용법

```bash
# ── CRM 전광판 (Databricks) ─────────────────────────────────
/data --source crm --snapshot                     ← 어제 CRM 전광판 스냅샷
/data --source crm --trend 30d                    ← 최근 30일 트렌드
/data --source crm --channel                      ← 채널별 발송 성과
/data --source crm --consent                      ← 수신 동의 모수 분석
/data --source crm --push                         ← 앱푸시 발송 압력
/data --source crm --diagnose "CTR"               ← CRM 지표 이상 진단

# ── Amplitude MCP ────────────────────────────────────────────
/data --source amplitude --type funnel --topic "홈→상품→결제 전환"
/data --source amplitude --type trend  --topic "최근 4주 DAU 트렌드"
/data --source amplitude --type cohort --topic "1분기 신규 가입자 리텐션"
/data --source amplitude --type ab-test --topic "앱푸시 메시지 실험"
/data --source amplitude --type diagnose --topic "3월 구매전환율 급락"

# ── Databricks 범용 쿼리 ─────────────────────────────────────
/data --source databricks --query "최근 30일 신규 가입자 채널별 추이"
/data --source databricks --table team.marketing.X --type trend --topic "테이블 분석"

# ── 파일 ────────────────────────────────────────────────────
/data --file input/data.csv --type trend --topic "DAU 트렌드"
/data --file input/ab_result.csv --type ab-test --topic "추천 알고리즘 실험"

# ── 차트 자동 생성 (--chart 플래그) ─────────────────────────
/data --source amplitude --type trend --topic "DAU" --chart
/data --file input/cohort.csv --type cohort --topic "리텐션" --initiative TM-2061
```

---

## 파이프라인 개요

```
Layer 1: 조회      Layer 2: 분석                   Layer 3: 시각화
──────────         ──────────────────────────────  ────────────────
crm-querier        preprocessor → validator        chart-generator
amplitude-querier  ↓                               ↓
databricks-querier trend / segment / funnel        HTML 차트
file               cohort / ab-test / diagnose     Markdown 리포트
                   ↓
                   insight-synthesizer
```

---

## 실행 규칙

1. `data-agent-system/CLAUDE.md`를 읽어 전체 파이프라인(Step 0~6)을 파악한다.

2. args 파싱:
   - `--source [crm|amplitude|databricks|file]` → 데이터 소스 결정
   - `--type [유형]` → 분석 유형 (없으면 `auto`)
   - `--topic "[주제]"` → 분석 주제 (없으면 자동 생성)
   - `--file [경로]` → 파일 경로 (`--source file` 자동 설정)
   - `--chart` → Layer 3 차트 생성 활성화
   - `--initiative TM-XXXX` → 이니셔티브 컨텍스트 연결
   - CRM 전용: `--snapshot` / `--trend [기간]` / `--channel` / `--consent` / `--push` / `--diagnose "[지표]"`

3. `data-agent-system/CLAUDE.md`의 Step 0~6 파이프라인을 순서대로 실행:
   - **Step 0**: 소스 연결 확인
   - **Step 1**: 데이터 조회 (Layer 1 에이전트 호출)
   - **Step 1.5**: CRM 소스 시 이상 탐지 루프
   - **Step 2~3**: 전처리·검증 (Haiku)
   - **Step 4**: 전문 분석 (Sonnet, 유형별 분기)
   - **Step 5**: 통합 인사이트 (Sonnet)
   - **Step 6**: 차트 생성 (Layer 3, `--chart` 또는 trend/ab-test 자동)

4. 산출물 저장:
   - 리포트: `data-agent-system/output/data_{type}_{YYYYMMDD}_{주제}.md`
   - 차트: `data-agent-system/output/charts/chart_{YYYYMMDD}_{주제}.html`
   - `--initiative` 지정 시: `input/initiatives/{TM-XXXX}/output/`에도 복사

---

## 소스별 의존 도구

| 소스 | 필요 |
|------|------|
| `crm` | Databricks 환경변수 + `crm-analysis-agent-system/scripts/queries.py` |
| `amplitude` | Amplitude MCP 연결 (`mcp__Amplitude__*` 도구) |
| `databricks` | Databricks 환경변수 + `databricks-agent-system/scripts/client.py` |
| `file` | 없음 (로컬 파일) |

---

## 출력 예시

```
[데이터팀] 완료

📊 분석: CTR 30일 트렌드 (crm)
📁 리포트: data-agent-system/output/data_crm_20260430_trend_30d.md
📈 차트:   data-agent-system/output/charts/chart_20260430_crm_trend.html

Executive Summary
- CTR 4월 평균 1.2%, 전월 대비 −0.3%p 하락 (경보 수준 미달)
- 앱푸시 채널 CTR이 전체 하락을 견인 (1.8% → 1.1%)
- 월요일 CTR 스파이크 패턴 유지 중 → 주간 소화 캠페인 정상 작동
```

---

## 기존 스킬과의 관계

| 기존 스킬 | 동작 | 내부 처리 |
|---------|------|----------|
| `/crm-analysis` | 그대로 동작 | `/data --source crm`과 동일 |
| `/analyst` | 그대로 동작 | `/data --source [amplitude|file]`과 동일 |
| `/databricks` | 그대로 동작 | `/data --source databricks`와 동일 |

기존 스킬도 계속 사용 가능. `/data`는 세 소스를 하나의 인터페이스로 통합한 진입점.
