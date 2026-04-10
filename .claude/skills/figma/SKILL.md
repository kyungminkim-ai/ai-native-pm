---
description: Figma URL에서 화면을 분석하여 디자인 스펙 문서 생성, PRD 초안 작성, Before/After 비교, UX 카피 추출을 수행하는 디자인 에이전트
---

# /figma — Figma 화면 분석 · 디자인 스펙 에이전트

## 모델

`claude-haiku-4-5-20251001`

## 사용법
```
/figma [Figma URL]                                  ← 파일/프레임 기본 분석
/figma [Figma URL] --spec                           ← 화면 설계서(스펙 문서) 생성
/figma [Figma URL] --prd                            ← 화면 기반 PRD 초안 생성
/figma [Figma URL] --compare [비교 URL]             ← 두 디자인 비교 (이전/이후)
/figma [Figma URL] --copy                           ← UX 카피 텍스트 추출
/figma [Figma URL] --initiative TM-XXXX             ← 이니셔티브 연결
```

## 실행 규칙
1. `figma-agent-system/CLAUDE.md` 읽어 역할 및 에이전트 구조 파악
2. args 파싱:
   - URL만 → analyze 모드 (figma-reader → screen-analyst)
   - `--spec` → spec 모드 (figma-reader → screen-analyst → spec-writer)
   - `--prd` → prd 모드 (spec 모드 결과 → prd-agent-system 연계)
   - `--compare` → compare 모드 (두 URL 각각 analyze → screen-analyst 비교)
   - `--copy` → copy 모드 (figma-reader 텍스트 추출만)
3. `FIGMA_ACCESS_TOKEN` 환경변수 확인
   - 없으면 토큰 발급 가이드 출력 후 중단
4. `figma-agent-system/CLAUDE.md` 해당 모드 Step 실행 (에이전트 순차 호출)
5. 산출물: `figma-agent-system/output/` 저장

## 에이전트 구조
```
/figma 스킬 (오케스트레이터)
  ├── figma-reader   (Haiku)  — Figma API 데이터 수집
  ├── screen-analyst (Sonnet) — 화면 구조 분석·플로우 추론
  └── spec-writer    (Sonnet) — 화면 설계서 작성
```
에이전트 스펙: `figma-agent-system/.claude/agents/{agent}/AGENT.md`

## 환경변수 (`.env`에 추가 필요)
```bash
# Figma API 연결 — figma.com/settings > Personal Access Tokens에서 발급
FIGMA_ACCESS_TOKEN=figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Figma URL 형식
```
https://www.figma.com/design/{file_key}/{title}?node-id={node_id}
→ file_key: 파일 전체
→ node-id: 특정 프레임/컴포넌트
```

## 연결 방식
- **방식 A (기본)**: Python 스크립트 `figma-agent-system/scripts/client.py` (REST API v1)
- Figma MCP 서버는 공식 미지원 — REST API 직접 호출 방식 사용

## 연계 스킬
- `--prd` 옵션 사용 시 → `/prd` 스킬과 자동 연계 (화면 분석 결과 → PRD 입력)
- `--spec` 결과 → `confluence-writer`로 자동 저장 제안
