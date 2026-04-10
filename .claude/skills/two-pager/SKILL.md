---
description: 경영진 의사결정용 2-Pager 문서 작성 및 검토를 수행하는 기획 에이전트
---

# /two-pager — 2-Pager 작성 에이전트

## 모델

`claude-sonnet-4-6`

## 사용법

```
/two-pager [아이디어 또는 문제 정의]
/two-pager [TM-XXXX]
/two-pager [주제] --refs [Confluence URL 또는 파일 경로]
```

## 실행 규칙

1. `prd-agent-system/.claude/agents/two-pager-writer/AGENT.md`를 읽어 작성 규칙을 파악한다.
2. `prd-agent-system/.claude/agents/two-pager-reviewer/AGENT.md`를 읽어 검토 규칙을 파악한다.

3. **입력 처리**
   - `TM-XXXX` 형식이면 `input/initiatives/` 폴더에서 이니셔티브 컨텍스트를 로드한다.
   - `--refs` 옵션이 있으면 해당 문서를 confluence-reader 또는 WebFetch로 수집한다.
   - args가 없으면 "어떤 주제로 2-Pager를 작성할까요? 배경이나 해결하려는 문제를 알려주세요." 라고 묻는다.

4. **워크플로우**

```
[컨텍스트 수집]
참조 문서 또는 이니셔티브 KB 로드
        ↓
[Step 1: two-pager-writer 호출]
  - 독자 질문 목록 생성
  - 7개 섹션 초안 작성
  - Self-Check 통과 확인
        ↓
[Step 2: two-pager-reviewer 호출]
  - Silent Read 시뮬레이션
  - 섹션별 재작성 + 코멘트 삽입
  - 검토 요약 생성
        ↓
[파일 저장]
prd-agent-system/output/two_pager_{YYYYMMDD}_{주제}.md
```

5. **PRD 연결은 사용자가 명시적으로 요청할 때만 실행한다.**
   자동으로 `/prd`를 이어서 실행하지 않는다.

6. **산출물 저장**
   - `prd-agent-system/output/two_pager_{YYYYMMDD}_{주제}.md`
   - Confluence 업로드는 사용자 요청 시에만 실행한다.

## 완료 출력 형식

```
✅ 2-Pager 작성 완료

📄 파일: prd-agent-system/output/two_pager_{날짜}_{주제}.md

🔍 검토 요약:
- BLUF: ✅/⚠️
- So what? 테스트: ✅/⚠️
- 데이터 맥락: ✅/⚠️
- 대안 처리: ✅/⚠️
- 전체 판정: [즉시 공유 가능 / 수정 후 공유 / 대폭 수정 필요]

📝 코멘트 {N}개 삽입됨 (수정 필요 항목)

다음 단계:
- /prd 작성: /staff [주제] PRD 써줘
- Confluence 업로드: /staff 2-Pager Confluence에 올려줘
```
