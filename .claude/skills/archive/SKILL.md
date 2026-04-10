---
description: 30일 이상 된 산출물 파일을 archive/ 폴더로 정리하는 아카이브 에이전트
---

# /archive — 결과물 아카이브 에이전트

## 모델

`claude-haiku-4-5-20251001`

## 개요

30일 이상 된 output 파일을 `output/_archive/{YYYY-MM}/` 폴더로 자동 이동하는 정리 스킬.
요청 즉시 미리보기 → 사용자 확인 → 실행 순으로 동작한다.

---

## 사용법

```
/archive              # 30일 기준 미리보기
/archive --run        # 실제 이동 실행
/archive --days 60    # 기준일 변경
/archive --target output  # 특정 폴더만
```

---

## 실행 규칙

1. **미리보기 먼저** — 항상 dry-run 결과를 사용자에게 보여준다.
2. **사용자 확인 필수** — 실제 이동 전 "이 파일들을 아카이브할까요?" 확인을 받는다.
3. **구조 보존** — 원본 폴더 계층 구조를 `_archive/` 하위에 그대로 유지.

---

## 실행 방법

```bash
# Step 1: 미리보기
python3 /Users/musinsa/Documents/agent_project/pm-studio/scripts/archive_manager.py \
  --dry-run --days 30

# Step 2: 사용자 확인 후 실행
python3 /Users/musinsa/Documents/agent_project/pm-studio/scripts/archive_manager.py \
  --run --days 30
```

---

## 대상 폴더

- `output/` (루트)
- `prd-agent-system/output/`
- `figma-agent-system/output/`
- `gtm-agent-system/output/`
- `pgm-agent-system/output/`
- `report-agent-system/output/`
- `epic-ticket-system/output/`
- `ux-copywriter-system/output/`

---

## 제외 항목

- `logs/`, `flash/`, `weekly/`, `reports/`, `artifacts/` 폴더
- `.json`, `.log` 파일 (설정/메타 파일)
- `.DS_Store`, `.gitkeep`

---

## 출력 위치

```
output/_archive/{YYYY-MM}/output/{원본파일명}
output/_archive/{YYYY-MM}/prd-agent-system/output/{원본파일명}
...
```
