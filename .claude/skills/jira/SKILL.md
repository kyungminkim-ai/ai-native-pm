---
description: 자연어 요청을 Jira Epic/Task/Story 티켓으로 변환하여 일괄 생성하는 Jira 티켓 생성 에이전트
---

# /jira — Jira 티켓 생성 에이전트

## 모델

`claude-haiku-4-5-20251001`

## 사용법

```
/jira [요청 내용]
```

## 실행 규칙

1. `.claude/agents/jira-creator/AGENT.md`를 읽어 에이전트 역할과 티켓 생성 규칙을 파악한다.
2. args를 파싱하여 생성할 티켓 요청 내용을 해석한다.
   - args가 없으면 사용자에게 "어떤 티켓을 만들까요? (프로젝트 키, 유형, 요약 내용을 알려주세요)" 를 요청한다.
   - 참조 티켓(예: "PSN-871과 동일한 설정으로")이 언급된 경우 해당 티켓 정보를 먼저 조회한다.
3. AGENT.md의 워크플로우대로 생성 예정 티켓 목록을 표로 정리하고 **반드시 사용자 컨펌을 받는다**.
4. 승인 후 `scripts/create_jira_{이니셔티브명}_{YYYYMMDD}.py`를 생성하고 실행한다.
5. 결과를 `output/created_{이니셔티브명}_tickets.json`에 저장하고 생성된 티켓 URL 목록을 출력한다.
