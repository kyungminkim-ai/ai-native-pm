# Analyst Agent System — 데이터 분석 에이전트 시스템

## 역할

사용자가 입력한 데이터를 분석 유형에 따라 자동으로 sub-agent에 분기하여 처리한다.
**전처리·집계는 Haiku**, **인사이트 도출은 Sonnet**으로 역할을 분리한다.
`/analyst` 스킬로 호출된다.

> 공통 규약: `../CONVENTIONS.md` | 역량 맵: `../CAPABILITY_MAP.md`

---

## 모델 배분 원칙

| 처리 영역 | 모델 | 이유 |
|----------|------|------|
| 데이터 파싱, 정제, 집계, 기초 통계 | `claude-haiku-4-5-20251001` | 반복적·연산적 작업 → 비용 효율 |
| 데이터 검증, 품질 체크, 이상값 탐지 | `claude-haiku-4-5-20251001` | 규칙 기반 판단 |
| 트렌드 해석, 패턴 발견, 인사이트 생성 | `claude-sonnet-4-6` | 추론·판단 필요 |
| 세그먼트 비교, 세그먼트 인사이트 | `claude-sonnet-4-6` | 맥락적 해석 필요 |
| 퍼널 이탈 분석, 개선 제안 | `claude-sonnet-4-6` | 비즈니스 판단 필요 |
| 코호트 리텐션 해석 | `claude-sonnet-4-6` | 장기 패턴 추론 |
| A/B 테스트 결과 평가 | `claude-sonnet-4-6` | 통계적 판단 + 의사결정 |
| 다중 분석 통합 인사이트 | `claude-sonnet-4-6` | 종합적 판단 |

---

## 지원 분석 유형

| 분석 유형 | `--type` | 주요 데이터 형태 |
|----------|---------|----------------|
| 시계열 트렌드 | `trend` | 날짜 + 지표 (DAU, 매출, CVR 등) |
| 사용자 세그먼트 | `segment` | 사용자 그룹 + 행동/지표 |
| 퍼널 전환 | `funnel` | 단계별 사용자 수 / 이벤트 |
| 코호트 리텐션 | `cohort` | 가입 코호트 + 기간별 리텐션 |
| A/B 테스트 | `ab-test` | 실험군/대조군 + 지표 |
| 자동 감지 | `auto` (기본) | 데이터 구조 보고 자동 분기 |

---

## 데이터 입력 방법

```bash
# 파일 경로 지정
/analyst --file input/data.csv --type trend --topic "앱 DAU 트렌드 분석"

# 인라인 데이터 (짧은 표 형태)
/analyst --data "날짜,DAU\n2026-01-01,150000\n..." --type trend

# input/ 폴더 자동 감지 (파일 하나만 있을 때)
/analyst --type segment --topic "구매 사용자 세그먼트 분석"

# 유형 자동 감지
/analyst --file input/funnel_data.csv --topic "회원가입 퍼널 분석"
```

---

## 처리 파이프라인

### Step 0: 데이터 수신 및 준비
1. `--file` 또는 `--data` 파싱
2. 파일 없으면 `input/` 폴더에서 최신 파일 자동 탐색
3. 지원 형식: CSV, JSON, TSV, 마크다운 테이블, 인라인 텍스트

### Step 1: 전처리 (Haiku)
**에이전트**: `.claude/agents/data-preprocessor/AGENT.md`
- 데이터 파싱 및 구조 파악
- 결측값/이상값 처리
- 집계 및 피벗
- 기초 통계 산출 (평균, 중앙값, 표준편차)

### Step 2: 데이터 검증 (Haiku)
**에이전트**: `.claude/agents/data-validator/AGENT.md`
- 데이터 품질 점수 산출
- NULL 비율, 이상값 비율 체크
- 분석 신뢰도 등급 판정 (HIGH / MEDIUM / LOW)
- 분석 유형 자동 감지 (--type auto 시)

### Step 3: 전문 분석 (Sonnet) — 분석 유형에 따라 분기

```
trend   → .claude/agents/trend-analyst/AGENT.md
segment → .claude/agents/segment-analyst/AGENT.md
funnel  → .claude/agents/funnel-analyst/AGENT.md
cohort  → .claude/agents/cohort-analyst/AGENT.md
ab-test → .claude/agents/ab-test-analyst/AGENT.md
auto    → Step 2에서 감지된 유형으로 분기
```

### Step 4: 통합 인사이트 (Sonnet)
**에이전트**: `.claude/agents/insight-synthesizer/AGENT.md`
- 분석 결과 종합
- Executive Summary (3줄 이내)
- 우선순위별 추천 액션
- Open Questions

---

## 파이프라인 상세 흐름

```
[입력] --file / --data / input/ 자동탐색
    ↓
[Step 1] data-preprocessor (Haiku)
    전처리 완료 → preprocessed_data 구조체 반환
    ↓
[Step 2] data-validator (Haiku)
    품질 체크 → validation_report + 감지된 analysis_type 반환
    ↓
[Step 3] 분석 에이전트 (Sonnet) ← analysis_type 기반 분기
    trend-analyst / segment-analyst / funnel-analyst /
    cohort-analyst / ab-test-analyst
    → analysis_result 반환
    ↓
[Step 4] insight-synthesizer (Sonnet)
    최종 리포트 → output/ 저장
```

---

## 출력 파일 명명 규칙

| 분석 유형 | 파일명 |
|----------|--------|
| trend | `output/analysis_trend_{YYYYMMDD}_{주제}.md` |
| segment | `output/analysis_segment_{YYYYMMDD}_{주제}.md` |
| funnel | `output/analysis_funnel_{YYYYMMDD}_{주제}.md` |
| cohort | `output/analysis_cohort_{YYYYMMDD}_{주제}.md` |
| ab-test | `output/analysis_abtest_{YYYYMMDD}_{주제}.md` |

이니셔티브 연결 시(`--initiative TM-XXXX`) → `../input/initiatives/{TM-XXXX}/output/`에도 저장.

---

## 오류 처리

| 상황 | 처리 |
|------|------|
| 파일 없음 | `input/` 폴더 탐색 → 없으면 데이터 입력 요청 |
| 지원 불가 형식 | CSV/JSON/TSV/마크다운 형식으로 변환 요청 |
| 데이터 품질 LOW | 분석 진행하되 리포트에 신뢰도 경고 표시 |
| 분석 유형 감지 실패 | 사용자에게 `--type` 명시 요청 |
| 데이터 행 수 < 10 | 통계 분석 한계 경고 후 진행 |
