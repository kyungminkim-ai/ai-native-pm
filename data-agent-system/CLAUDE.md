# Data Agent System — 통합 데이터 에이전트

## 역할

3개 레이어로 데이터 조회부터 시각화까지 전 과정을 처리하는 통합 데이터 에이전트.
`/data` 스킬로 호출된다.

> 공통 규약: `../CONVENTIONS.md` | 역량 맵: `../CAPABILITY_MAP.md`

---

## 아키텍처

```
[Layer 1: 조회]          [Layer 2: 분석]                  [Layer 3: 시각화·출력]
─────────────────        ─────────────────────────────    ──────────────────────
crm-querier              data-preprocessor (Haiku)        chart-generator
amplitude-querier   →    data-validator    (Haiku)    →   insight-synthesizer
databricks-querier       trend / segment / funnel          리포트 (.md)
file-input               cohort / ab-test / diagnose
                         insight-synthesizer (Sonnet)
```

---

## 데이터 소스 (`--source`)

| 소스 | 트리거 | 조회 에이전트 |
|------|--------|-------------|
| `crm` | `--source crm` | `crm-querier` (Databricks CRM 전용 쿼리) |
| `amplitude` | `--source amplitude` | `amplitude-querier` (Amplitude MCP) |
| `databricks` | `--source databricks` | `databricks-querier` (자연어/SQL) |
| `file` | `--file [경로]` 또는 기본값 | 직접 파일 로드 |

---

## 분석 유형 (`--type`)

| 값 | 분석 내용 |
|----|---------|
| `trend` | 시계열 트렌드·WoW/MoM·이상 시점 탐지 |
| `segment` | 세그먼트 비교·Star/Risk 세그먼트 분류 |
| `funnel` | 단계별 전환율·이탈 포인트·임팩트 시뮬레이션 |
| `cohort` | 코호트 리텐션·이탈 구간·Plateau 시점 |
| `ab-test` | A/B 실험 결과 평가·통계적 유의성·롤아웃 권고 |
| `diagnose` | 지표 하락·이상 Root Cause 5단계 분석 |
| `auto` | 데이터 구조 보고 자동 감지 (기본값) |

CRM 소스는 아래 추가 모드를 지원:

| CRM 모드 | 파라미터 | 내용 |
|---------|---------|------|
| snapshot | `--snapshot` | 어제 전광판 전체 지표 (Z 쿼리) |
| trend | `--trend [7d/30d/90d]` | 기간별 지표 트렌드 |
| channel | `--channel` | 채널별 발송 성과 비교 |
| consent | `--consent` | 수신 동의 모수 세그먼트 분석 |
| push | `--push` | 앱푸시 발송 압력 분석 |
| diagnose | `--diagnose "[지표명]"` | CRM 지표 이상 Root Cause |

---

## 실행 파이프라인

### Step 0: 연결 및 소스 확인

소스별 연결 확인:
- `crm` / `databricks` → `python3 ../databricks-agent-system/scripts/client.py --check`
- `amplitude` → Amplitude MCP 연결 상태 확인 (`mcp__Amplitude__get_context` 호출)
- `file` → 파일 존재 여부 확인

### Step 1: 데이터 조회 [Layer 1]

소스별 에이전트 호출:

```
--source crm        → .claude/agents/crm-querier/AGENT.md
--source amplitude  → .claude/agents/amplitude-querier/AGENT.md
--source databricks → .claude/agents/databricks-querier/AGENT.md
--file [경로]       → 직접 로드 (Step 2로 이동)
```

**출력**: `raw_data` 구조체 (컬럼·행·메타데이터)

### Step 1.5: CRM 이상 탐지 루프 (crm 소스 전용)

CRM 지표가 아래 임계값을 초과하면 자동으로 추가 쿼리 실행:

| 지표 | 경보 조건 |
|------|---------|
| CTR | < 0.5% |
| STR | < 1.0% |
| push_per_user | > 5 / 일 |
| consent_rate WoW Δ | −2%p 이상 |

경보 발생 시 crm-querier에 drill-down 쿼리 요청 후 Step 2 진행.

### Step 2: 데이터 전처리 [Layer 2 — Haiku]

**에이전트**: `.claude/agents/data-preprocessor/AGENT.md`
- 파싱·결측값 처리·집계·기초 통계 산출
- 출력: `preprocessed` 구조체

### Step 3: 데이터 검증 [Layer 2 — Haiku]

**에이전트**: `.claude/agents/data-validator/AGENT.md`
- 품질 점수·신뢰도 등급 (HIGH / MEDIUM / LOW)
- `--type auto` 시 분석 유형 자동 감지

### Step 4: 전문 분석 [Layer 2 — Sonnet]

분석 유형에 따라 분기:

```
trend   → .claude/agents/trend-analyst/AGENT.md
segment → .claude/agents/segment-analyst/AGENT.md
funnel  → .claude/agents/funnel-analyst/AGENT.md
cohort  → .claude/agents/cohort-analyst/AGENT.md
ab-test → .claude/agents/ab-test-analyst/AGENT.md
diagnose→ .claude/agents/diagnose-analyst/AGENT.md
auto    → Step 3에서 감지된 유형으로 분기
```

### Step 5: 통합 인사이트 [Layer 2 — Sonnet]

**에이전트**: `.claude/agents/insight-synthesizer/AGENT.md`
- Executive Summary (3줄 이내)
- 우선순위별 추천 액션
- Open Questions

### Step 6: 시각화 및 출력 [Layer 3 — Sonnet]

`--chart` 플래그 지정 시 (또는 trend/ab-test 유형은 자동 적용):

**에이전트**: `.claude/agents/chart-generator/AGENT.md`
- 분석 결과에서 집계 테이블 추출
- Chart.js HTML 차트 생성
- 리포트에 차트 경로 삽입

---

## 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `--source [crm\|amplitude\|databricks\|file]` | `file` | 데이터 소스 |
| `--type [유형]` | `auto` | 분석 유형 |
| `--topic "[주제]"` | 자동 생성 | 분석 주제 |
| `--file [경로]` | — | 파일 경로 (`--source file` 자동 설정) |
| `--chart` | trend/ab-test 자동 | 차트 자동 생성 |
| `--initiative TM-XXXX` | — | 이니셔티브 연결 |
| `--start-date YYYY-MM-DD` | 소스별 기본값 | 조회 시작일 |
| `--end-date YYYY-MM-DD` | 어제 | 조회 종료일 |
| CRM: `--snapshot` | — | 어제 CRM 전광판 스냅샷 |
| CRM: `--trend [기간]` | 30d | CRM 트렌드 (7d/30d/90d) |
| CRM: `--channel` | — | 채널 성과 비교 |
| CRM: `--consent` | — | 수신 동의 세그먼트 |
| CRM: `--push` | — | 앱푸시 발송 압력 |
| CRM: `--diagnose "[지표]"` | — | CRM 지표 이상 진단 |

---

## 출력 파일 명명 규칙

| 유형 | 리포트 | 차트 |
|------|--------|------|
| trend | `output/data_trend_{YYYYMMDD}_{주제}.md` | `output/charts/chart_{YYYYMMDD}_{주제}.html` |
| segment | `output/data_segment_{YYYYMMDD}_{주제}.md` | `output/charts/chart_{YYYYMMDD}_{주제}.html` |
| funnel | `output/data_funnel_{YYYYMMDD}_{주제}.md` | — |
| cohort | `output/data_cohort_{YYYYMMDD}_{주제}.md` | — |
| ab-test | `output/data_abtest_{YYYYMMDD}_{주제}.md` | `output/charts/chart_{YYYYMMDD}_{주제}.html` |
| diagnose | `output/data_diagnose_{YYYYMMDD}_{주제}.md` | — |
| crm-* | `output/data_crm_{YYYYMMDD}_{mode}.md` | `output/charts/chart_{YYYYMMDD}_crm_{mode}.html` |

이니셔티브 연결 시(`--initiative TM-XXXX`) → `../input/initiatives/{TM-XXXX}/output/`에도 저장.

---

## 모델 배분

| 처리 | 모델 |
|------|------|
| 조회·전처리·검증 | `claude-haiku-4-5-20251001` |
| 전문 분석·인사이트·차트 | `claude-sonnet-4-6` |

---

## 오류 처리

| 오류 | 처리 |
|------|------|
| Databricks 연결 실패 | Step 0 설정 가이드 출력 후 중단 |
| Amplitude MCP 미연결 | MCP 등록 방법 안내 후 중단 |
| 파일 없음 | `input/` 폴더 탐색 → 없으면 데이터 입력 요청 |
| 쿼리 0행 반환 | "기간 내 데이터 없음" 보고 후 날짜 범위 조정 제안 |
| 데이터 품질 LOW | 분석 진행하되 신뢰도 경고 표시 |
| 분석 유형 감지 실패 | `--type` 명시 요청 |
