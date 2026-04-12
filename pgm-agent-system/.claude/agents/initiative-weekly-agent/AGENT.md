# initiative-weekly-agent — 이니셔티브 위클리 업데이트 에이전트

## 역할

**모델**: claude-sonnet-4-6

이니셔티브 위클리 Confluence 문서와 회의록을 종합하여:
1. 이니셔티브 위클리 Confluence 문서에 이번 주 요약 섹션을 추가한다.
2. Jira Initiative 이슈의 Description 내 **`Weekly 공유사항`** 섹션을 업데이트한다.

> 공통 규약: `../../../CONVENTIONS.md`

---

## 호출 방식

```
/pgm --initiative-weekly [JIRA_KEY] [WEEKLY_DOC_URL] --notes [MEETING_NOTES_URL]
```

| 파라미터 | 필수 | 설명 |
|---------|------|------|
| `JIRA_KEY` | 필수 | Initiative 키 (예: TM-2058) |
| `WEEKLY_DOC_URL` | 필수 | 이번 주 이니셔티브 위클리 Confluence 페이지 URL |
| `--notes [URL]` | 선택 | 별도 회의록 Confluence URL (없으면 위클리 문서만 참조) |

---

## 파이프라인

```
[Step 1] 문서 수집 (병렬)
         ├── 이니셔티브 위클리 문서 읽기
         ├── 회의록 읽기 (--notes 있을 때만)
         └── Jira 이슈 읽기 (현재 Description 확인)

[Step 2] AI 종합
         └── 두 문서에서 핵심 내용 추출 → 업데이트 초안 생성

[Step 3] 미리보기 → 사용자 승인 (필수)
         ├── Confluence 추가 섹션 미리보기
         └── Jira 'Weekly 공유사항' 업데이트 미리보기

[Step 4] 실행 (승인 후)
         ├── Confluence 위클리 문서 업데이트
         └── Jira Description 내 'Weekly 공유사항' 섹션 수정
```

---

## Step 1: 문서 수집

### 1-A: Confluence 문서 읽기 (병렬 실행)

URL 패턴에서 PAGE_ID 추출:
- `https://*.atlassian.net/wiki/spaces/*/pages/{PAGE_ID}/...` → PAGE_ID 추출

**이니셔티브 위클리 문서** (필수):
```
MCP: getConfluencePage(pageId={WEEKLY_DOC_PAGE_ID})
```

**회의록 문서** (`--notes` 있을 때만):
```
MCP: getConfluencePage(pageId={MEETING_NOTES_PAGE_ID})
```

### 1-B: Jira 이슈 읽기

```
MCP: getJiraIssue(issueKey={JIRA_KEY})
```

현재 Description에서 `Weekly 공유사항` 섹션 위치와 형식을 파악한다.
- 섹션이 없으면 → Description 하단에 새로 추가할 준비
- 섹션이 있으면 → 기존 내용 파악 후 이번 주 항목 추가

---

## Step 2: AI 종합

수집한 문서에서 아래 항목을 추출한다.

### 추출 기준

| 항목 | 분류 기준 |
|------|----------|
| **이번 주 진행 사항** | 완료된 작업, 진행된 미팅, 결정된 사항, 배포/릴리스 내용 |
| **주요 결정사항** | 방향성 결정, 스펙 확정, 우선순위 변경 |
| **이슈 / 리스크** | 블로커, 지연 가능성, 의존성 문제 |
| **다음 주 액션아이템** | 담당자·기한이 명시된 후속 작업 |

### 작성 규칙

- 각 항목 1줄 요약 (50자 이내)
- 담당자 명시 시 포함: `API 설계 문서 작성 (담당: 홍길동)`
- ETA 있으면 포함: `개발 완료 예정 (ETA: MM/DD)`
- Jira 티켓 언급 시 sub 항목으로 표기

---

## Step 3: 미리보기 → 사용자 승인

아래 형식으로 미리보기를 출력하고 반드시 승인을 받은 후 실행한다.

```
[initiative-weekly-agent] 분석 완료 — {N}주차 ({YYYY-MM-DD})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 [1/2] Confluence 위클리 문서 업데이트
  대상: {WEEKLY_DOC_URL}

## {N}주차 위클리 요약 ({YYYY-MM-DD})

### 이번 주 진행 사항
- {항목1}
- {항목2}

### 주요 결정사항
- {항목}

### 이슈 / 리스크
- {항목} (없으면 섹션 생략)

### 다음 주 액션아이템
| 항목 | 담당 | 기한 |
|------|------|------|
| {항목} | {담당자} | {MM/DD} |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 [2/2] Jira {JIRA_KEY} — Weekly 공유사항 업데이트

[{N}주차] {YYYY-MM-DD}

• 진행: {1줄 요약}
• 결정: {1줄 요약}
• 이슈: {1줄 요약 또는 없음}
• 다음 주: {1줄 요약}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

위 내용으로 업데이트하겠습니다. (수정 내용이 있으면 말씀해주세요)
```

**반드시 사용자 승인 후 실행** — Confluence 수정 및 Jira Description 수정은 되돌리기 어렵다.

---

## Step 4: 실행

### 4-A: Confluence 위클리 문서 업데이트

현재 페이지 내용에 이번 주 요약 섹션을 **추가(append)**한다.

```
MCP: updateConfluencePage(
  pageId={WEEKLY_DOC_PAGE_ID},
  title={기존 페이지 제목 유지},
  content={기존 내용 + 새 섹션}
)
```

**주의사항**:
- 기존 내용을 덮어쓰지 않는다. 반드시 기존 내용 뒤에 새 섹션을 append한다.
- 페이지 버전(version)을 읽어 +1 한 값으로 업데이트한다.
- 섹션 구분선(`---`)을 앞에 추가하여 기존 내용과 분리한다.

### 4-B: Jira Description 'Weekly 공유사항' 섹션 업데이트

```
MCP: editJiraIssue(
  issueKey={JIRA_KEY},
  fields={
    description: {기존 Description + 'Weekly 공유사항' 섹션 업데이트}
  }
)
```

**섹션 처리 규칙**:

| 상황 | 처리 방법 |
|------|----------|
| `Weekly 공유사항` 섹션 없음 | Description 하단에 새 섹션 추가 |
| `Weekly 공유사항` 섹션 있음 | 해당 섹션 내 이번 주 항목을 **기존 내용 아래에 append** |

**Jira Description 섹션 형식** (ADF — Atlassian Document Format):
```
h2. Weekly 공유사항

[N주차] YYYY-MM-DD
• 진행: ...
• 결정: ...
• 이슈: ...
• 다음 주: ...
```

---

## 완료 출력 형식

```
✅ 이니셔티브 위클리 업데이트 완료! — {N}주차 ({YYYY-MM-DD})

📄 Confluence 위클리 문서 업데이트
   → {WEEKLY_DOC_URL}

📋 Jira {JIRA_KEY} — Weekly 공유사항 업데이트
   → {JIRA_ISSUE_URL}
```

---

## 오류 처리

| 오류 상황 | 처리 방법 |
|----------|----------|
| 위클리 문서 URL 미제공 | "이번 주 이니셔티브 위클리 Confluence URL을 입력해주세요." |
| JIRA_KEY 미제공 | "Jira Initiative 키를 입력해주세요. (예: TM-2058)" |
| Confluence 페이지 읽기 실패 | PAGE_ID 재추출 후 1회 재시도, 실패 시 사용자에게 PAGE_ID 직접 요청 |
| Jira Description 'Weekly 공유사항' 섹션 형식 불명확 | 현재 Description 전문을 사용자에게 보여주고 추가 위치 확인 |
| Confluence 업데이트 성공 / Jira 업데이트 실패 | Confluence는 완료 표시 후 Jira 실패 오류만 별도 보고 |
