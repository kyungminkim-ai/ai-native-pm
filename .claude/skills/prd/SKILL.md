---
description: 기능 요구사항 정의서(PRD) 및 데이터 파이프라인 PRD 작성, 문제 정의 가정 검증을 수행하는 기획 에이전트
---

# /prd — PRD 생성 에이전트

## 모델

`claude-sonnet-4-6`

## 사용법

```
/prd [rough note 또는 이니셔티브 ID] [--validate] [--data amplitude]
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

### `--data amplitude` 옵션

문제 정의(Phase 0~1) 단계에서 **Amplitude MCP를 통해 실제 지표를 수집**하여 PRD의 현황 데이터를 보강한다.
"현재 전환율이 X%" 같은 가정을 실제 데이터로 검증하고 PRD 배경 섹션에 자동 삽입한다.

```
/prd 앱푸시 타게팅 개선 --validate --data amplitude
  → Phase 0 가정 검증 시 Amplitude에서 현재 CTR, 전환율 등 실측값 조회 후 반영

/prd TM-2061 --data amplitude
  → 이니셔티브 관련 이벤트 현황을 Amplitude에서 수집하여 문제 정의 보강
```

## 실행 규칙

1. `prd-agent-system/CLAUDE.md`를 읽어 에이전트 역할과 전체 워크플로우를 파악한다.
2. 사용자가 제공한 args를 **Rough Note**로 처리한다.
   - args가 없으면 사용자에게 기능 배경/해결 문제를 요청한다.
   - `TM-XXXX` 형식이면 `input/initiatives/` 폴더에서 해당 이니셔티브 컨텍스트를 먼저 로드한다.
   - `--validate` 플래그가 있으면 CLAUDE.md Section 0(Phase 0) 강제 실행.
3. CLAUDE.md에 정의된 워크플로우를 그대로 따라 PRD를 생성한다.
4. 산출물은 `prd-agent-system/output/prd_{YYYYMMDD}_{주제}.md`에 저장한다.
5. **[레지스트리 등록]** 각 주요 산출물 저장 직후 아래 명령으로 레지스트리에 등록한다:
   ```bash
   # Phase 3 완료 후 (prd 초안)
   python3 scripts/registry.py register --type prd --path prd-agent-system/output/prd_{YYYYMMDD}_{주제}.md --topic "{주제}"
   # Phase 5 완료 후 (1회차 보강본 _v2)
   python3 scripts/registry.py register --type prd-v2 --path prd-agent-system/output/prd_{YYYYMMDD}_{주제}_v2.md --topic "{주제}"
   # Phase 5 2회차 완료 후 (_v3, 해당 시)
   python3 scripts/registry.py register --type prd-v3 --path prd-agent-system/output/prd_{YYYYMMDD}_{주제}_v3.md --topic "{주제}"
   ```
   레지스트리 가이드: `REGISTRY_GUIDE.md`
