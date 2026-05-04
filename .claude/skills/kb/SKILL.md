---
name: kb
description: 마크다운 파일을 input/kb/에 저장·인덱싱하고, 쿼리·익스포트하는 지식베이스 스킬
model: claude-haiku-4-5
triggers:
  - /kb
  - 지식베이스
  - KB에 추가
  - KB 검색
  - KB 익스포트
---

# /kb — Knowledge Base 스킬

## 역할

`input/kb/` 폴더를 지식베이스로 운영한다.
- 원본 텍스트(Slack 대화, 문서 등)를 구조화된 마크다운으로 저장
- INDEX.md 갱신으로 전체 KB 파악
- 자연어 질문으로 관련 문서 검색
- NotebookLM 업로드용 정제 파일 익스포트

운영 상세는 `input/kb/README.md` 참조.

---

## 모델

`claude-haiku-4-5` (단순 파일 처리 작업이므로 Haiku 충분)

---

## 커맨드 정의

### `/kb add`

**입력**: 사용자가 붙여넣은 원본 텍스트 (Slack 대화, 문서, 메모 등)

**동작**:
1. 텍스트를 분석해 아래 항목을 추출·추론
   - `date`: 대화/문서 날짜 (없으면 오늘)
   - `source`: slack | doc | note | meeting | confluence
   - `channel`: Slack 채널명 (source=slack인 경우)
   - `participants`: 참여자 이름 (추론 가능한 경우)
   - `initiative`: 관련 TM-XXXX (언급된 경우)
   - `tags`: 핵심 키워드 3-5개
   - `privacy`: 내용 민감도에 따라 추론 (기본값: `internal`)
   - `summary`: 1-2문장 요약
2. frontmatter 포함 마크다운 파일 생성
3. 저장 경로: `input/kb/{source}/{YYYYMMDD}_{채널명 또는 주제}.md`
4. 저장 후 파일 경로와 frontmatter 요약 보고

**출력 예시**:
```
저장 완료: input/kb/slack/20260420_match-platform_CEP전략.md

📋 메타데이터:
- 날짜: 2026-04-20
- 출처: Slack #match-platform
- 태그: CEP, Braze, 세그먼트
- Privacy: internal
- 요약: CEP 전략 방향 논의 — Braze vs Auxia 비교, 세그먼트 기준 확정
```

---

### `/kb index`

**동작**:
1. `input/kb/` 전체 마크다운 파일 스캔
2. 각 파일의 frontmatter 읽어 항목 추출
3. `input/kb/INDEX.md` 생성/덮어쓰기

**INDEX.md 구조**:
```markdown
# KB Index
> 마지막 갱신: YYYY-MM-DD

## 최근 추가 (30일 이내)
| 파일 | 날짜 | 출처 | 태그 | 요약 |
|------|------|------|------|------|
| ... | ... | ... | ... | ... |

## 이니셔티브별
### TM-2058
- 20260420_match-platform_CEP전략.md — CEP 전략 논의

## 태그별
### Braze
- ...

## 전체 목록 (날짜 역순)
| 파일 | 날짜 | 출처 | privacy | 요약 |
```

---

### `/kb query "[질문]"`

**입력**: 자연어 질문

**동작**:
1. `input/kb/INDEX.md` 로드
2. 질문과 관련성 높은 파일 식별 (태그·요약·이니셔티브 기반)
3. 관련 파일 내용 읽기
4. 답변 생성 + 출처 인용

**출력 형식**:
```
[KB 답변]

{답변 내용}

📎 참조 문서:
- input/kb/slack/20260420_match-platform_CEP전략.md (2026-04-20)
- input/kb/docs/20260305_Auxia_미팅요약.md (2026-03-05)
```

initiative ID(TM-XXXX)로 질문하면 해당 이니셔티브 관련 파일만 필터.

---

### `/kb export [--tag TAG] [--initiative TM-XXXX] [--since YYYY-MM-DD]`

**동작**:
1. `input/kb/` 스캔 (기본값: privacy=public, internal만 포함 / team 제외)
2. 옵션 필터 적용
3. 파일들을 날짜순으로 합쳐 단일 마크다운 생성
4. 저장: `output/kb_export_YYYYMMDD.md`

**출력 파일 구조**:
```markdown
# Knowledge Base Export
> 생성일: YYYY-MM-DD | 포함 파일: N개 | 기간: YYYY-MM-DD ~ YYYY-MM-DD

---

## [날짜] [출처] [주제]
> 태그: xxx | 요약: xxx

[본문]

---
```

**사용 예시**:
```
/kb export                          # 전체 (team 제외)
/kb export --tag MATCH              # MATCH 태그 파일만
/kb export --initiative TM-2058     # 특정 이니셔티브
/kb export --since 2026-04-01       # 4월 이후 파일만
```

---

## 다른 스킬에서 KB 참조하는 방법

다른 스킬이 KB 컨텍스트가 필요할 때 아래 패턴을 사용한다.

```python
# 1. INDEX.md 로드
Read("input/kb/INDEX.md")

# 2. 관련 파일 식별 후 읽기
Read("input/kb/slack/20260420_match-platform_CEP전략.md")

# 3. 컨텍스트로 활용
```

**스킬별 자동 참조 트리거**:
| 스킬 | KB 참조 조건 | 쿼리 방식 |
|------|------------|---------|
| `/prd` | initiative ID 있을 때 | 해당 TM-XXXX 관련 파일 |
| `/pgm` | Weekly Flash 작성 시 | 최근 2주 파일 |
| `/analyst` | 배경 컨텍스트 필요 시 | 분석 주제 관련 태그 |
| `/two-pager` | `--refs` 없을 때 | 주제 관련 파일 |

---

## 파일 컨벤션 (참조용)

```yaml
---
date: 2026-04-20            # 필수
source: slack               # 필수: slack|doc|note|meeting|confluence|report
channel: match-platform     # source=slack일 때만
participants: [경민, 현우]   # 옵션 (익명화 가능)
initiative: TM-2058         # 옵션
tags: [CEP, Braze]          # 필수, 3-5개
privacy: internal           # 필수: public|internal|team
summary: "한 줄 요약"        # 필수
---
```

---

## 오류 처리

| 상황 | 처리 |
|------|------|
| frontmatter 없는 파일 | index 시 `unknown` 태그로 포함, 경고 출력 |
| INDEX.md 없음 | query 전 자동으로 `/kb index` 실행 |
| 관련 파일 없음 | "KB에 관련 문서 없음. `/kb add`로 추가하세요." |
| privacy=team 파일 export 시도 | 자동 제외, 제외된 파일 수 보고 |
