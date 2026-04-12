---
description: 시장·경쟁·사용자 리서치 기반 Product Discovery 분석, 웹/앱 UI 화면 분석 및 설계서 생성을 수행하는 디스커버리 에이전트
---

# /discovery — Product Discovery Intelligence 에이전트

## 모델

`claude-sonnet-4-6`

## 사용법

```
/discovery [탐색 주제] [옵션]

옵션:
  --mode competitor  경쟁사 분석 모드 (기본값): 시장 분석 + 화이트스페이스 + 페르소나 + 가상 인터뷰
  --mode reference   레퍼런스 분석 모드: Best Practice + UX 패턴 + Gap 분석

  --input {폴더경로}  로컬 파일 제공 시 (CSV 리뷰, md 문서, png 스크린샷 등)

  --ref all          외부 벤더 레퍼런스 전체 수집 (Amplitude + Braze + Shopify 자동 선택)
  --ref amplitude    Amplitude GitHub Docs만 수집 (제품 기능/API 문서 참조용)
  --ref braze        Braze GitHub Docs만 수집
  --ref shopify      Shopify App Store 벤치마크만 수집

  --data amplitude   Amplitude MCP로 내부 실사용 데이터 수집 (행동 데이터 기반 Discovery 강화)
                     → --ref amplitude(외부 문서)와 다름: 실제 이벤트/퍼널/코호트 데이터 조회

  --initiative TM-XXXX  이니셔티브 컨텍스트 로드
```

> **`--ref amplitude` vs `--data amplitude` 구분**
> - `--ref amplitude`: Amplitude 공식 문서(GitHub)에서 제품 기능·설계 방식 참조 → 벤치마킹·레퍼런스 분석에 사용
> - `--data amplitude`: Amplitude MCP로 **우리 서비스의 실제 행동 데이터** 조회 → 현황 파악·가설 검증에 사용

## 실행 규칙

1. `discovery-intelligence-system/CLAUDE.md`를 읽어 에이전트 역할과 전체 워크플로우를 파악한다.

2. args를 파싱한다:
   - 탐색 주제가 없으면 시장/제품 도메인과 해결하려는 문제를 사용자에게 요청한다.
   - `--mode`가 없으면 주제에서 자동 판단 (경쟁사/시장/화이트스페이스 → competitor, 벤치마킹/UX/레퍼런스 → reference).
   - `--input` 폴더가 지정되면 `data-processor` 스킬로 파일을 먼저 분류하고 `input_manifest.json`을 생성한다.
   - `TM-XXXX`가 포함되면 `input/initiatives/` 폴더에서 이니셔티브 컨텍스트를 로드한다.
   - `--ref` 옵션이 있으면 Phase 0(외부 지식 수집)을 먼저 실행한다.

3. CLAUDE.md에 정의된 모드별 워크플로우를 실행한다:
   - **Competitor 모드**: Phase 0(선택) → Phase 1(시장분석 · 병렬) → Phase 2~5(페르소나 · 인터뷰 · 합성 · 보고서)
   - **Reference 모드**: Phase 0(선택) → Phase R(레퍼런스 분석) → 보고서
4. **[레지스트리 등록]** 보고서 저장 직후 등록한다:
   ```bash
   python3 scripts/registry.py register --type discovery --path discovery-intelligence-system/output/{파일명}.md --topic "{탐색 주제}"
   ```

## 예시

```
# Competitor 모드 (기본)
/discovery 무신사 앱 리텐션 향상을 위한 개인화 푸시 전략 --ref all
/discovery 패션 버티컬 커머스 상품 추천 화이트스페이스 --initiative TM-2061
/discovery 한국 리셀 시장 분석

# Reference 모드
/discovery 결제 UX 개선 --mode reference --input ./input/screenshots/
/discovery Braze 캠페인 캔버스 설계 방식 --mode reference --ref braze

# 로컬 데이터 활용 (경쟁사 리뷰 CSV + 외부 레퍼런스 병행)
/discovery 경쟁사 A 분석 --input ./input/competitor_reviews/ --ref amplitude
```
