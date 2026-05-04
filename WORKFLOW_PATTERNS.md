# PM Studio — 복합 워크플로우 패턴

> 비서실장이 복합 요청 처리 시 참조하는 실행 순서 가이드.
> 자주 발생하는 패턴을 정의하여 일관된 실행을 보장한다.

---

## Pattern A: 기획 → 실행 파이프라인

```
[Discovery] → PRD 작성 → Red Team 검증 → Epic 분해 → Jira 등록
```

**트리거**: "TM-XXXX 기획 시작해줘", "PRD 써서 에픽 분해하고 Jira에 올려줘"

**실행 순서**:
1. `/discovery --initiative TM-XXXX` (선택: 배경 리서치)
2. `/prd TM-XXXX` → PRD 파일 생성
3. `/red {PRD 파일 경로}` → Red Team 검증
4. `/epic {PRD 파일 경로} TM-XXXX` → 목록 컨펌 후 Jira 등록

---

## Pattern B: 주간 성과 보고 파이프라인

```
/pgm --full → /report → (선택) /mail
```

**트리거**: "이번 주 성과 정리해줘", "주간 플래시 + 회의록 다 만들어줘"

**실행 순서**:
1. `/pgm --full [JIRA_KEY] [CONFLUENCE_URL]` → Flash Report + 회의록 + Weekly 코멘트
2. `/report {flash_md 경로}` → C레벨 검토 (선택)
3. `/mail {flash_md 경로} --to {수신자}` → 메일 발송 (선택, 컨펌 필수)

**단계별 단독 실행**:
- Flash Report만: `/pgm [JIRA_KEY]`
- 회의록 + Jira 코멘트만: `/pgm --weekly [CONFLUENCE_URL]`

---

## Pattern C: 지식 관리 파이프라인

```
Confluence 검색 → 인사이트 요약 → (선택) Confluence 저장
```

**트리거**: "~에 대해 알려줘", "찾아줘", "정리해서 올려줘"

**실행 순서**:
1. `confluence-reader` agent → 검색 및 요약
2. (선택) `confluence-writer` agent → Confluence 저장 (컨펌 필수)

---

## Pattern D: 런치 파이프라인

```
Discovery → PRD 작성 → GTM 브리프 → Confluence 저장
```

**트리거**: "~을 출시하려면 뭐가 필요해", "신기능 기획 처음부터 시작하자"

**실행 순서**:
1. `/discovery [주제]` → 시장/제품 분석
2. `/prd` → PRD 작성 (Discovery 결과 참조)
3. `/gtm {PRD 파일 경로}` → GTM 브리프
4. `confluence-writer` agent → 문서 저장 (컨펌 필수)

---

## Pattern E: 문서 공유 파이프라인

```
문서 조회 → 이메일 변환 → 발송 승인 → Gmail 발송
```

**트리거**: "이 문서 ~에게 메일로 보내줘", "Confluence 페이지 공유해줘"

**실행 순서**:
1. `confluence-reader` agent 또는 로컬 파일 확인
2. `/mail {문서 경로 또는 URL} --to {수신자}` → 제목·수신자·미리보기 컨펌 후 발송

---

## Pattern F: 과제 관리 파이프라인 (PGM 전용)

```
/ticket-review → (선택) /epic → Jira 등록
```

**트리거**: "이번 분기 MATCH 과제 정리해줘", "CSV 분석해서 에픽으로 올려줘"

**실행 순서**:
1. `/ticket-review` → CSV 또는 JQL로 과제 분류
2. 분류 결과 확인 후 선택적으로 `/epic` 실행

---

## Pattern G: 회의 관리 파이프라인

```
/meeting → (선택) /pgm --weekly {Confluence URL}
```

**트리거**: "회의록 써줘", "미팅 정리해줘", "회의 준비해줘", "캘린더에 올려줘"

**실행 순서**:
1. `/meeting --input {노트} --initiative TM-XXXX [--calendar]`
   → 회의록 초안 작성 → 미리보기 → Confluence 업로드 → (선택) 캘린더 등록
2. (선택) `/pgm --weekly {Confluence URL}` → 회의록 → Jira Initiative 코멘트 게시

**자주 쓰는 조합**:
```
# 회의록만
/meeting --input notes.txt --title "Auxia 정기 미팅"

# 회의록 + 캘린더
/meeting --input notes.txt --title "Auxia 정기 미팅" --calendar

# 회의록 + Jira 코멘트 (전체 미팅 사이클)
/meeting --input notes.txt --initiative TM-2055
→ (업로드 완료 후) /pgm --weekly {반환된 Confluence URL}
```

---

---

## Pattern H: 데이터 기반 기획 파이프라인

```
/databricks --analyze → /prd → /red → /epic
```

**트리거**: "데이터 보고 기획해줘", "지표 분석 후 PRD 써줘", "Databricks에서 {테이블} 분석해서 기획으로 연결해줘"

**실행 순서**:
1. `/databricks --analyze {table} "{분석 주제}" --initiative TM-XXXX` → 데이터 분석 리포트
2. 분석 리포트를 Rough Note로 사용 → `/prd TM-XXXX`
3. `/red {PRD 파일}` → 검증
4. (선택) `/epic {PRD 파일}` → Jira 등록

---

## Pattern I: Slack → 회의록 파이프라인

```
/slack --today/#채널 → /meeting 또는 /pgm --weekly
```

**트리거**: "슬랙 대화 정리해줘", "오늘 논의된 거 회의록으로 만들어줘"

**실행 순서**:
1. `/slack --today #match-pm` → 오늘 대화 수집 + Action Item 추출
2. 요약 결과 → `/meeting --input {slack_summary.md}` → Confluence 업로드
3. (선택) `/pgm --weekly {Confluence URL}` → Jira Initiative 코멘트 게시

**단독 활용**:
```
# 이번 주 주요 결정사항 파악
/slack --week #match-pm

# 특정 주제 관련 대화 찾기
/slack --search "캠페인" #match-pm
```

---

## Pattern J: Figma → 기획 파이프라인

```
/figma [URL] --prd → /red → /epic
```

**트리거**: "이 Figma 파일 기준으로 PRD 써줘", "디자인 보고 기획서 만들어줘"

**실행 순서**:
1. `/figma [URL]` → 화면 구조 파악 (필요 시)
2. `/figma [URL] --prd` → 화면 분석 → PRD 초안 자동 생성
3. `/red {PRD 파일}` → Red Team 검증
4. (선택) `/figma [URL] --spec` → 개발팀 전달용 화면 설계서

**화면 설계서 단독 생성**:
```
/figma [URL] --spec
→ 완성 후 Confluence 저장 제안
```

---

## Pattern K: 신기능 기획 풀 파이프라인

```
/market-research → /discovery → /prd → /red → /gtm
     시장 구조         기회 발굴    PRD    검증    런치 계획
```

**트리거**: "처음부터 전체 기획해줘", "시장 파악부터 런치 계획까지", "신기능 기획 풀 사이클"

**실행 순서**:
1. `/market-research [시장명] --focus all` → 페르소나 + 경쟁사 + 고객 여정 파악
2. `/discovery [주제] --initiative TM-XXXX` → 기회 발굴 + 화이트스페이스 확인
3. `/prd TM-XXXX` → PRD 작성 (1, 2 결과를 Rough Note로 활용)
4. `/red {PRD 경로}` → Red Team 검증
5. `/gtm --prd {PRD 경로} --stage launch` → GTM 체크리스트 + 채널 전략

**단계별 단독 실행**:
- 시장 구조만: `/market-research [시장명]`
- 기회 발굴만: `/discovery [주제]`
- 런치 계획만: `/gtm --prd {PRD 경로}`

**병렬 가능**: Step 1 + Step 2 (market-research + discovery는 독립 실행 가능)

---

## Pattern L: 분기 시작 OKR 파이프라인

```
/market-research → /strategy → /okr → /jira (에픽 분해)
     시장 구조         방향 논의    OKR    이니셔티브 등록
```

**트리거**: "분기 시작해보자", "Q2 OKR 수립해줘", "이번 분기 목표 잡아줘"

**실행 순서**:
1. `/market-research --focus competitor` → 경쟁 구도 + 기회 포인트 파악 (선택)
2. `/strategy "이번 분기 우선순위 어떻게 가져가야 해?"` → 방향성 논의
3. `/okr --draft --quarter Q{N}` → Objective + Key Results 초안
4. 사용자 OKR 검토 및 확정
5. `/jira` → 확정된 KR 기반 이니셔티브 · 에픽 생성

**OKR 확정 후 주간 연계**:
```
/pgm [JIRA_KEY]  →  Flash Report에 OKR 현황 섹션 자동 포함
```

**병렬 가능**: Step 1 + Step 2 (독립 실행 가능)

---

## 병렬 실행 가능 조합

| 병렬 가능 | 조건 |
|---------|------|
| `/pgm --full` 내 publisher + minutes-generator | analysed_report.json 생성 후 |
| `/pgm --full` 내 jira-parser + confluence 페이지 로드 | 독립적, 동시 실행 가능 |
| `confluence-reader` + 다른 검색 | 서로 독립 |
| `/databricks --explore` + `confluence-reader` | 서로 독립 |
| `/market-research` + `/discovery` | 서로 독립 (Pattern K Step 1+2 병렬 가능) |
| `/market-research` + `/strategy` | 서로 독립 (Pattern L Step 1+2 병렬 가능) |
| `/slack --today` + `/databricks --query` | 서로 독립 |
| `figma-reader` + `schema-explorer` | 서로 독립 (figma --prd 시 병렬 가능) |

---

## TM-XXXX 이니셔티브 컨텍스트 로드

요청에 `TM-XXXX` 형식이 포함되면:

1. `input/initiatives/index.md`에서 매칭 이니셔티브 확인
2. 해당 폴더의 `context.md`·`meta.json`·`decisions.md` 로드
3. `meta.json`의 `confluence.primary_space`를 기본 Space로 사용
4. 산출물을 해당 이니셔티브의 `output/` 폴더에도 저장

```
input/initiatives/
├── index.md                   ← 전체 이니셔티브 목록
└── 2026Q2/
    └── {이니셔티브-ID}_{이름}/
        ├── meta.json          ← 티켓 메타 (Space, 기간, 상태)
        ├── context.md         ← 배경·목표·성공지표
        ├── decisions.md       ← 의사결정 로그
        └── output/            ← 생성 산출물
```

---

## State Layer — 팀 컨텍스트 로드

이니셔티브 ID 없이 일반 요청이 들어올 때, `input/state/product_context.md`를 참조하여
현재 집중 분기·이니셔티브·북극성 지표·핵심 가설을 컨텍스트로 활용한다.

```
input/state/
├── product_context.md    ← 현재 제품 컨텍스트 (분기별 업데이트)
└── decisions/            ← PM 의사결정 로그
    ├── _template.md      ← 의사결정 기록 템플릿
    └── YYYY-MM-DD-{주제}.md  ← 개별 의사결정 파일
```

### 의사결정 기록 패턴

**트리거**: "이 결정 기록해줘", "PRD 방향 결정 남겨줘", "오늘 논의 결과 저장해줘"

**실행 순서**:
1. `input/state/decisions/_template.md` 기반으로 파일 생성
2. 파일명: `YYYY-MM-DD-{결정-주제}.md` (예: `2026-05-04-타겟팅-자동화-범위.md`)
3. 맥락·결정 내용·대안·근거 작성 후 저장

**원칙**: 결정은 실시간 기록. `chronicle` 스킬의 주간 회고 시 자동 참조됨.
