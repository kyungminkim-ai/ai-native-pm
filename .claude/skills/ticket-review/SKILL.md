---
description: CSV 파일 또는 JQL 결과를 기반으로 Jira 과제를 검토·클러스터링하고 우선순위 인사이트를 제공하는 과제 검토 에이전트
---

# /ticket-review — 과제 검토 에이전트

## 모델

`claude-haiku-4-5-20251001`

## 사용법

```
/ticket-review [CSV 파일 경로]
```

## 실행 규칙

1. `pgm-agent-system/.claude/agents/ticket-reviewer/AGENT.md`를 읽어 에이전트 역할과 워크플로우를 파악한다.
2. args를 파싱하여 CSV 파일 경로를 추출한다.
   - args에 파일 경로가 있으면 해당 파일을 사용한다.
   - 경로가 없으면 `input/data/` 폴더에서 가장 최근 CSV를 자동 탐지한다.
   - CSV가 없으면 폴더 경로를 안내하고 중단한다.
3. AGENT.md에 정의된 워크플로우(Step 1~5)를 순서대로 실행한다.
4. 산출물은 `pgm-agent-system/output/ticket_review_{YYYYMMDD}.md`에 저장한다.
