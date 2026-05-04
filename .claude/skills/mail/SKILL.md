# /mail — Confluence → Gmail 발송 에이전트

## 사용법

```
/mail [Confluence URL 또는 마크다운 파일 경로] --to [수신자 이메일]
```

## 실행 규칙

1. `.claude/agents/mail-specialist/AGENT.md`와 `.claude/agents/doc-specialist/AGENT.md`를 읽어 역할을 파악한다.
2. args를 파싱하여 입력 소스와 수신자를 분리한다.
   - args가 없으면 "어떤 문서를 누구에게 보낼까요? (Confluence URL 또는 파일 경로와 수신자 이메일을 알려주세요)" 를 요청한다.
   - 입력이 Confluence URL / 페이지 ID이면 **doc-specialist** 에이전트를 먼저 호출하여 내용을 추출한다.
   - 입력이 `.md` 파일 경로이면 doc-specialist 단계를 건너뛰고 mail-specialist로 바로 진행한다.
3. `mail-specialist` 에이전트를 호출하여 HTML 변환 → 사용자 승인 → Gmail 발송 워크플로우를 실행한다.
4. **발송 전 반드시 사용자 승인을 받는다.** (제목·수신자·미리보기 경로 표시)
5. 발송 완료 후 `output/send_log.json`에 로그를 기록한다.
