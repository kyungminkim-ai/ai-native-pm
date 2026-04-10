---
description: 데이터 파일·Databricks 쿼리 결과를 기반으로 트렌드·세그먼트·퍼널·코호트·A-B테스트 분석 및 지표 하락 원인 진단을 수행하는 데이터 분석 에이전트
---

# /analyst — 데이터 분석 에이전트

## 모델

`claude-haiku-4-5-20251001`

## 개요

데이터를 넣으면 분석 유형에 따라 sub-agent를 자동 분기하여 인사이트 리포트를 생성한다.
전처리·집계는 Haiku, 인사이트 도출은 Sonnet으로 역할을 분리한다.

---

## 사용법

```
/analyst --file [파일경로] --type [분석유형] --topic "[분석 주제]"
/analyst --file [파일경로] --topic "[분석 주제]"          ← 유형 자동 감지
/analyst --type trend --topic "[주제]"                    ← input/ 폴더 자동 탐색
/analyst --file [경로] --initiative TM-XXXX               ← 이니셔티브 연결
```

## 분석 유형 (`--type`)

| 값 | 분석 내용 | 주요 데이터 형태 |
|----|----------|----------------|
| `trend` | 시계열 트렌드, WoW/MoM, 이상 시점 탐지 | 날짜 + 지표 |
| `segment` | 세그먼트별 비교, Star/Risk 세그먼트 분류 | 그룹 + 지표 |
| `funnel` | 단계별 전환율, 이탈 포인트, 임팩트 시뮬레이션 | 단계 + 사용자 수 |
| `cohort` | 코호트 리텐션, 이탈 구간, Plateau 시점 | 코호트 + 기간 + 리텐션율 |
| `ab-test` | A/B 실험 결과 평가, 롤아웃 권고 | 그룹 + 지표 |
| `diagnose` | 지표 하락/이상 원인 분석, Root Cause 5단계 | 이상 시점 + 관련 지표 |
| `auto` | 데이터 구조 보고 자동 분기 (기본값) | — |

### `diagnose` 타입 — Root Cause 분석 방법론

지표 하락, 캠페인 성과 이상, 전환율 급변 등 **"왜 이런 결과가 나왔나"** 를 체계적으로 파고드는 5단계 프로세스.
증상만 보고 빠른 결론을 내리는 것을 방지한다.

**5단계 실행 순서:**

```
Step 1. 증상 정의 (Symptom Mapping)
   - 어떤 지표가, 언제부터, 얼마나 변했는가?
   - 기준선(베이스라인) 설정: 직전 4주 평균 or 전년 동기
   - 이상 범위 정량화: "-23% WoW", "p95 → p5 수준"

Step 2. 패턴 분류 (Pattern Recognition)
   - 갑자기? vs 서서히? (Spike vs Drift)
   - 특정 세그먼트만? vs 전체? (Localized vs Systemic)
   - 특정 채널/시간/기기만? → 필터 분해

Step 3. 가설 생성 (Hypothesis Generation)
   - 가설 최소 3개, 각각 검증 가능한 형태로 작성
   - 예: "H1: 특정 캠페인 오디언스 품질 저하"
        "H2: 앱 업데이트 이후 UX 변경"
        "H3: 외부 경쟁사 프로모션 영향"

Step 4. 가설 검증 (Hypothesis Testing)
   - 데이터로 각 가설 지지/기각 판단
   - 3개 가설 모두 기각 시 → 추가 가설 생성 후 재검증
   - 가장 강하게 지지되는 가설을 Root Cause 후보로 선정

Step 5. 진단 보고 (Diagnosis Report)
   - Root Cause: {가설명} — 신뢰도 High/Mid/Low
   - 기여 요인: 복합 원인이면 기여도 % 추정
   - 권고 액션: 즉시 / 단기(1주) / 중기(1달) 구분
   - 모니터링 지표: 개선 여부를 확인할 지표 2~3개
```

**트리거 예시:**
```bash
/analyst --type diagnose --topic "3월 3주차 앱푸시 CTR 23% 하락 원인 분석"
/analyst --file input/campaign_metrics.csv --type diagnose --topic "리텐션 캠페인 성과 이상"
/analyst --type diagnose --topic "신규 가입자 D7 리텐션 급락" --initiative TM-2061
```

## 입력 데이터 형식

- **파일**: CSV, JSON, TSV (UTF-8 또는 EUC-KR)
- **위치**: `analyst-agent-system/input/` 폴더에 파일 저장 후 `--file input/파일명` 지정
- **인라인**: 짧은 데이터는 `--data "col1,col2\nval1,val2"` 형태로 직접 입력

## 출력

- **리포트**: `analyst-agent-system/output/analysis_{type}_{YYYYMMDD}_{주제}.md`
- **구조**: Executive Summary → 핵심 인사이트 → 추천 액션 → 분석 상세 → Open Questions

---

## 실행 규칙

1. `analyst-agent-system/CLAUDE.md` 읽어 전체 파이프라인 파악
2. args 파싱:
   - `--file [경로]` → 파일 로드
   - `--data "[인라인]"` → 인라인 파싱
   - 없으면 `analyst-agent-system/input/` 폴더 탐색
   - `--type [유형]` → 분석 유형 지정 (없으면 `auto`)
   - `--topic "[주제]"` → 분석 주제 (없으면 "데이터 분석")
   - `--initiative TM-XXXX` → 이니셔티브 컨텍스트 연결
3. `analyst-agent-system/CLAUDE.md` Step 0~4 순서대로 파이프라인 실행
4. 산출물: `analyst-agent-system/output/` 저장

## 사용 예시

```bash
# 트렌드 분석
/analyst --file input/dau_data.csv --type trend --topic "3월 DAU 트렌드 분석"

# 세그먼트 분석 (유형 자동 감지)
/analyst --file input/user_segment.csv --topic "구매 사용자 세그먼트 분석"

# 퍼널 분석 + 이니셔티브 연결
/analyst --file input/signup_funnel.csv --type funnel --topic "회원가입 퍼널" --initiative TM-2061

# A/B 테스트 결과 평가
/analyst --file input/ab_result.csv --type ab-test --topic "신규 추천 알고리즘 실험"

# 코호트 리텐션
/analyst --file input/cohort.csv --type cohort --topic "1분기 신규 가입자 리텐션"
```
