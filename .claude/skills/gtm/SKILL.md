---
description: 신기능·제품·캠페인 런치 전 GTM 체크리스트, ICP 정의, 채널 전략, 성공 지표를 생성하는 GTM 플래닝 에이전트
---

# /gtm — Go-to-Market 플래닝 에이전트

## 모델

`claude-sonnet-4-6`

## 사용법

```
/gtm [기능명 또는 PRD 경로] [옵션]

옵션:
  --prd {경로}      PRD 파일 경로 (자동 탐색 대신 명시적 지정)
  --initiative TM-XXXX  이니셔티브 컨텍스트 로드
  --stage [early|mid|launch]  런치 단계 (기본: launch)
    early : 초기 탐색 — ICP + 포지셔닝 중심
    mid   : 준비 단계 — 채널 전략 + 메시지 중심
    launch: 런치 직전 — 타임라인 + Go/No-Go 기준 중심
  --channel [all|push|email|display|organic]  집중 채널 지정 (기본: all)
```

## 실행 규칙

1. args를 파싱한다:
   - `--prd`가 없으면 `output/_registry.json`에서 최신 `prd` 파일을 자동 선택한다.
     레지스트리가 없으면 사용자에게 PRD 경로 또는 기능 설명을 요청한다.
   - `TM-XXXX`가 포함되면 `input/initiatives/` 폴더에서 이니셔티브 컨텍스트를 로드한다.
   - `--stage`가 없으면 PRD 내용에서 런치 단계를 자동 판단한다.

2. PRD 또는 컨텍스트를 읽고 아래 4단계 GTM 플랜을 작성한다:

   ### Phase 1 — 제품 포지셔닝

   - **Unique Value Proposition (UVP)**: 1문장, "우리는 [타겟]에게 [문제]를 [방식]으로 해결한다"
   - **ICP (Ideal Customer Profile)**: 인구통계 + 행동 패턴 + 심리 특성 + 사용 맥락
   - **경쟁 포지셔닝**: 경쟁사 대비 차별점 (무신사 사용자 관점에서 현실적으로)

   ### Phase 2 — 채널 전략

   무신사 MATCH 실행 가능 채널 기준:

   | 채널 | 역할 | 핵심 메시지 | 콜투액션 | 우선순위 |
   |------|------|------------|---------|---------|
   | 앱푸시 | ... | ... | ... | 1순위 |
   | 이메일 | ... | ... | ... | 2순위 |
   | 디스플레이 | ... | ... | ... | 3순위 |
   | 유기적 트래픽 | ... | ... | ... | 4순위 |

   `--channel` 옵션이 지정되면 해당 채널만 상세 작성한다.

   ### Phase 3 — 런치 타임라인

   T-4주 ~ T+2주 체크리스트:

   | 시점 | 마일스톤 | PM | 마케팅 | 개발 | 디자인 |
   |------|---------|----|----|----|----|
   | T-4주 | ... | ... | ... | ... | ... |
   | T-2주 | ... | ... | ... | ... | ... |
   | T-1주 | ... | ... | ... | ... | ... |
   | 런치 당일 | ... | ... | ... | ... | ... |
   | T+1주 | ... | ... | ... | ... | ... |
   | T+2주 | ... | ... | ... | ... | ... |

   **Go/No-Go 기준** (런치 당일 최종 판단):
   - Go 조건: 반드시 충족해야 하는 것 3개
   - No-Go 조건: 이 중 하나라도 해당하면 연기

   ### Phase 4 — 성공 지표

   - **North Star Metric**: 단일 핵심 지표 (런치 성공을 가장 잘 대변하는 것)
   - **Leading Indicators** (선행 지표, 주 단위 모니터링): 3개
   - **Lagging Indicators** (후행 지표, 월 단위 평가): 3개
   - **Amplitude 이벤트 연계**: 각 지표를 어떤 이벤트로 추적할지 제안
   - **모니터링 주기**: 런치 후 D+1 / D+7 / D+30 체크포인트

3. 출력 파일을 저장한다:
   ```
   output/gtm/gtm_{YYYYMMDD}_{주제}.md
   ```

4. 레지스트리에 등록한다:
   ```bash
   python3 scripts/registry.py register \
     --type gtm \
     --path output/gtm/gtm_{YYYYMMDD}_{주제}.md \
     --topic "{주제}"
   ```

## 예시

```
# PRD 자동 탐색 (레지스트리에서 최신 PRD 선택)
/gtm 무신사 개인화 푸시 기능

# PRD 명시적 지정
/gtm --prd prd-agent-system/output/prd_20260425_push.md

# 이니셔티브 연계
/gtm --initiative TM-2061 --stage launch

# 특정 채널 집중
/gtm 신규 글로벌 서비스 런치 --channel email

# 초기 탐색 단계 (포지셔닝만)
/gtm 리셀 거래 신뢰도 기능 --stage early
```

## 연계 패턴

```
# 런치 파이프라인
/discovery → /prd → /red → /gtm

# 포지셔닝 강화 후 GTM
/market-research → /strategy → /gtm --stage early

# GTM 완성 후 채널 실행
/gtm → /push-campaign (앱푸시 소재 자동 생성)
```
