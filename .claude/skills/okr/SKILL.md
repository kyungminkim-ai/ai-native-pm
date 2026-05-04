---
description: OKR 초안 수립, 기존 Jira Initiative와 정합성 검토, Key Result 측정 방법 제안을 수행하는 OKR 에이전트
---

# /okr — OKR 수립 에이전트

## 모델

`claude-sonnet-4-6`

## 사용법

```
/okr [분기 목표 텍스트 또는 이니셔티브 키] [옵션]

옵션:
  --draft          OKR 초안 생성 (기본)
  --review {경로}  기존 OKR 파일 검토 및 개선 제안
  --align TM-XXXX  특정 이니셔티브와 KR 정합성 검토
  --quarter [Q1|Q2|Q3|Q4]  대상 분기 (기본: 현재 분기 자동 감지)
  --team [팀명]   특정 팀 단위 OKR (기본: MATCH 팀 전체)
```

## 실행 규칙

1. args를 파싱한다:
   - `TM-XXXX`가 포함되면 `input/initiatives/{이니셔티브}/context.md`와 `meta.json`을 로드해 목표를 파악한다.
   - `--review {경로}`가 있으면 해당 파일을 읽고 검토 모드로 진행한다.
   - 분기 목표 텍스트가 없으면 "어떤 방향의 OKR을 수립할지" 한 줄로 질문한다.
   - `--quarter`가 없으면 현재 날짜 기준으로 분기를 자동 판단한다.

2. **`--draft` 모드** (기본):

   ### Phase 1 — Objective 수립

   Marty Cagan INSPIRED 기반: 비즈니스 목표 → 제품 목표 연계

   Objective 조건 체크리스트 (각 O 생성 시 자동 검증):
   - [ ] 정성적이고 고무적인가? (숫자 없음)
   - [ ] 시간 범위가 명확한가? (분기 단위)
   - [ ] 팀이 실제로 영향을 줄 수 있는 범위인가?
   - [ ] 상위 비즈니스 목표와 연결되는가?

   Objective 초안 2~3개 제안 → 사용자가 1개 선택하거나 조합

   ### Phase 2 — Key Results 정의

   Objective당 KR 2~4개, John Doerr Measure What Matters 기준:

   각 KR 구조:
   ```
   KR #N: [동사] [지표명]을 [기준값]에서 [목표값]으로 [기간까지]
   
   - 유형: Moonshot(70% 달성=성공) / Roofshot(100% 달성 목표)
   - 측정 방법: Amplitude 이벤트 / Databricks 테이블 / Jira 티켓 수
   - 기준값 근거: 현재 데이터 or 추정값 (근거 명시)
   - 주간 체크인: 매주 확인할 선행 지표
   ```

   KR 품질 자동 검증:
   - [ ] 숫자가 포함되어 있는가?
   - [ ] 기준값(baseline)이 있는가?
   - [ ] PM 팀이 직접 영향을 줄 수 있는가? (outcome vs output 구분)
   - [ ] 측정 방법이 명확한가?

   ### Phase 3 — 실행 연계

   1. **Jira 이니셔티브 매핑**: 현재 진행 중인 TM-XXXX 티켓과 KR 연결
      ```
      KR #1 → TM-XXXX (이니셔티브명), TM-YYYY (이니셔티브명)
      KR #2 → TM-ZZZZ (이니셔티브명)
      커버 안 되는 KR → 신규 이니셔티브 필요 여부 표시
      ```

   2. **주간 체크인 형식** (`/pgm` 플래시 연계 제안):
      ```
      매주 Flash Report에 포함할 OKR 현황 섹션:
      O: [목표]
        KR1: X% (목표 Y% | 예상 달성률 Z%)
        KR2: X건 (목표 Y건)
      ```

   3. **분기 말 회고 기준**: KR 달성 판단 기준 미리 정의

3. **`--review` 모드**:
   - 기존 OKR 파일을 읽고 아래 기준으로 검토:
     - **강도 평가**: Ambitious vs Realistic (너무 쉬운/어려운 KR 식별)
     - **측정 가능성**: 숫자·기준값 누락 여부, 측정 방법 불명확 여부
     - **커버리지 갭**: 현재 이니셔티브 중 OKR에 반영 안 된 항목
     - **Output vs Outcome**: 활동량 지표(출시 N개) → 결과 지표로 전환 제안
   - 개선 제안은 구체적 수정안 포함

4. 출력 파일을 저장한다:
   ```
   output/okr/okr_{YYYYMMDD}_{팀}_{분기}.md
   ```

## 예시

```
# 분기 OKR 신규 수립
/okr 2026 Q2 MATCH 팀 OKR 수립해줘

# 이니셔티브 기반 OKR
/okr --align TM-2061 --quarter Q2

# 기존 OKR 검토 및 개선
/okr --review output/okr/okr_20260401_MATCH_Q2.md

# 주제 기반 OKR 초안
/okr 리텐션 개선을 핵심 목표로 OKR 짜줘

# 특정 팀 단위
/okr --team MATCH --quarter Q3
```

## 연계 패턴

```
# OKR → 이니셔티브 연계 확인
/okr --draft → TM-XXXX 이니셔티브 매핑 → /task-ticket (신규 과제 생성)

# 주간 성과 연계
/okr --draft → /pgm (Flash Report에 OKR 현황 섹션 추가)

# 분기 시작 파이프라인
/market-research → /strategy → /okr --draft → /jira (에픽 분해)
```
