---
description: 경쟁사 포지셔닝 매핑, 타겟 페르소나 정의, 고객 여정 지도를 생성하는 시장 리서치 에이전트
---

# /market-research — 시장 리서치 에이전트

## 모델

`claude-sonnet-4-6`

## 사용법

```
/market-research [시장명 또는 주제] [옵션]

옵션:
  --focus [persona|competitor|journey|all]  분석 초점 (기본: all)
    persona    : 타겟 페르소나 정의 (Jobs-to-be-Done 기반)
    competitor : 경쟁사 포지셔닝 매핑 (2x2 매트릭스)
    journey    : 고객 여정 지도 (5단계)
    all        : 위 3가지 전체

  --initiative TM-XXXX  이니셔티브 컨텍스트 로드
  --segment [B2C|B2B|글로벌|국내]  타겟 세그먼트 힌트
  --ref [discovery|confluence]  기존 분석 파일 참조 (레지스트리 자동 탐색)
```

> **`/discovery`와의 차이**
> - `/discovery`: 기회·화이트스페이스 발굴 중심 (어디에 기회가 있나?)
> - `/market-research`: 시장 구조 파악 중심 (누가, 어떻게, 왜 사는가?)
> 둘은 보완 관계 — 새 기능 기획 시 `/market-research` 먼저 → `/discovery`로 기회 구체화

## 실행 규칙

1. args를 파싱한다:
   - 주제가 없으면 "어떤 시장/제품에 대한 리서치인지" 한 줄로 질문한다.
   - `TM-XXXX`가 있으면 `input/initiatives/{이니셔티브}/context.md`를 로드한다.
   - `--ref discovery`가 있으면 `output/_registry.json`에서 최신 discovery 파일을 참조한다.

2. `--focus` 옵션에 따라 아래 분석을 수행한다:

   ### Persona 분석 (`--focus persona` 또는 `--focus all`)

   Teresa Torres Jobs-to-be-Done 기반 페르소나 2~3개:

   각 페르소나 구조:
   ```
   이름 + 한 줄 설명
   ─────────────────
   인구통계  : 나이대, 직업, 라이프스타일
   목표      : 이 제품/기능으로 이루고 싶은 것 (Functional / Social / Emotional)
   Pain Point: 현재 겪는 불편함 구체적으로
   트리거    : 어떤 상황에서 이 서비스를 찾게 되나
   사용 맥락 : 언제, 어디서, 어떤 기기로
   무신사 연관: 무신사 앱에서의 행동 패턴 추정
   ```

   ### 경쟁사 포지셔닝 (`--focus competitor` 또는 `--focus all`)

   1. 주요 경쟁사 3~5개 식별 (국내 + 글로벌 균형)
   2. 포지셔닝 매트릭스: 주제에 맞는 2개 축 자동 선택
      - 예: 가격 × 품질 / 편의성 × 다양성 / 개인화 × 속도 등
   3. 각 경쟁사 요약 표:

   | 경쟁사 | 강점 | 약점 | 핵심 차별점 | 무신사 대비 |
   |------|------|------|------------|-----------|

   4. **화이트스페이스**: 경쟁사가 비어있는 포지셔닝 공간 2~3개 도출

   ### 고객 여정 지도 (`--focus journey` 또는 `--focus all`)

   5단계 고객 여정 (무신사 앱 사용 흐름 기준):

   | 단계 | 인지 | 탐색 | 구매 | 사용 | 재구매/이탈 |
   |------|------|------|------|------|------------|
   | 터치포인트 | | | | | |
   | 감정 상태 | 😐→😮 | | | | |
   | Pain Point | | | | | |
   | 기회 포인트 | | | | | |
   | 현재 해결책 | | | | | |

   **핵심 인사이트**: 가장 큰 이탈/기회 포인트 Top 3

3. 출력 파일을 저장한다:
   ```
   output/market-research/market_research_{YYYYMMDD}_{주제}.md
   ```

4. 레지스트리에 등록한다:
   ```bash
   python3 scripts/registry.py register \
     --type market-research \
     --path output/market-research/market_research_{YYYYMMDD}_{주제}.md \
     --topic "{주제}"
   ```

## 예시

```
# 전체 분석 (페르소나 + 경쟁사 + 고객 여정)
/market-research 패션 버티컬 커머스 개인화 추천

# 글로벌 시장 타겟
/market-research 무신사 글로벌 진출 --segment 글로벌

# 이니셔티브 연계 + 페르소나만
/market-research --initiative TM-2061 --focus persona

# 경쟁사 분석만
/market-research 국내 리셀 플랫폼 --focus competitor

# 기존 Discovery 결과 참조
/market-research 앱 리텐션 향상 --ref discovery --focus journey
```

## 연계 패턴

```
# 기획 전 시장 파악
/market-research → /discovery → /prd

# GTM 포지셔닝 강화
/market-research --focus competitor → /gtm

# 전략 논의 보강
/market-research → /strategy
```
