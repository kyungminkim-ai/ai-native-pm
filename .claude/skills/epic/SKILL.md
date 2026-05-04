# /epic — Epic Architect 에이전트

## 사용법

```
/epic [PRD 파일 경로 또는 Confluence URL] [이니셔티브 키(TM-XXXX)]
```

## 실행 규칙

1. `epic-ticket-system/CLAUDE.md`를 읽어 에이전트 역할과 전체 워크플로우를 파악한다.
2. 사용자가 제공한 args를 파싱한다:
   - 첫 번째 arg: PRD 출처 (파일 경로 또는 URL)
   - 두 번째 arg: Jira 이니셔티브 키 (TM-XXXX)
   - args가 부족하면 각각 사용자에게 요청한다.
3. CLAUDE.md에 정의된 워크플로우를 그대로 따라 에픽을 분해하고 Jira 티켓을 생성한다.
