---
description: 기능 요구사항 정의서(PRD) 및 데이터 파이프라인 PRD 작성, 문제 정의 가정 검증을 수행하는 기획 에이전트
---

# /prd — PRD 생성 에이전트

## 모델

`claude-sonnet-4-6`

## 사용법

```
/prd [rough note 또는 이니셔티브 ID] [--validate]
```

### `--validate` 옵션

PRD 작성 전 **5개 가정 검증 질문(Phase 0)** 을 먼저 실행한다.
아이디어가 아직 rough하거나, 문제 정의부터 함께 다듬고 싶을 때 사용.

```
/prd 앱푸시 타게팅 개선 --validate    ← Phase 0 → Phase 1 → ... 전체 실행
/prd TM-2061                          ← Phase 0 없이 바로 Phase 1 (이니셔티브 컨텍스트 활용)
```

Phase 0은 `--validate` 없이도 Rough Note가 충분히 구체적이지 않으면 자동 실행된다.
(`prd-agent-system/CLAUDE.md` Section 0 실행 조건 참조)

## 실행 규칙

1. `prd-agent-system/CLAUDE.md`를 읽어 에이전트 역할과 전체 워크플로우를 파악한다.
2. 사용자가 제공한 args를 **Rough Note**로 처리한다.
   - args가 없으면 사용자에게 기능 배경/해결 문제를 요청한다.
   - `TM-XXXX` 형식이면 `input/initiatives/` 폴더에서 해당 이니셔티브 컨텍스트를 먼저 로드한다.
   - `--validate` 플래그가 있으면 CLAUDE.md Section 0(Phase 0) 강제 실행.
3. CLAUDE.md에 정의된 워크플로우를 그대로 따라 PRD를 생성한다.
4. 산출물은 `prd-agent-system/output/prd_{YYYYMMDD}_{주제}.md`에 저장한다.
