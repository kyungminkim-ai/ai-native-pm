---
description: Confluence 검색·조회·작성·업데이트를 위한 MCP 도구 호출 규약 (다른 스킬/에이전트가 내부적으로 참조하는 인프라 스킬)
---

# Confluence Tool — Skill 호출 규약

## 모델

`claude-haiku-4-5-20251001`

## 개요

Confluence REST API와 통신하는 공통 스킬.  
`client.py`(인증/공통), `search.py`(검색), `upload.py`(업로드) 세 스크립트로 구성된다.

## 필수 환경변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `CONFLUENCE_URL` | Confluence 베이스 URL | `https://musinsa-oneteam.atlassian.net` |
| `CONFLUENCE_EMAIL` | 계정 이메일 | `kyungmin.kim@musinsa.com` |
| `CONFLUENCE_API_TOKEN` | Atlassian API 토큰 | `ATATT3x...` |
| `CONFLUENCE_SPACE_KEY` | 기본 Space 키 (upload.py 필수) | `DEV` |

선택 변수:
- `CONFLUENCE_PARENT_PAGE_ID` — 하위 페이지 생성 시 부모 페이지 ID

---

## search.py 호출 규약

```bash
python3 .claude/skills/confluence-tool/scripts/search.py \
  --query "검색어" \
  [--space SPACE_KEY]   # 미지정 시 spaces.json priority 순서대로
  [--limit 10]          # 기본값: 10
  [--list-spaces]       # 접근 가능한 전체 Space 목록 출력
```

**출력 (stdout):**
```json
{
  "query": "검색어",
  "total": 3,
  "results": [
    {
      "id": "123456",
      "title": "페이지 제목",
      "space": "DEV",
      "url": "https://...",
      "excerpt": "...관련 내용 발췌...",
      "lastModified": "2026-02-01"
    }
  ]
}
```

**`output/context.json`에도 동일 내용 저장.**

**반환 코드:**
- `0` — 성공 (results가 빈 배열이어도 성공)
- `1` — 인증 오류 또는 네트워크 오류

---

## upload.py 호출 규약

```bash
python3 .claude/skills/confluence-tool/scripts/upload.py \
  --title "페이지 제목" \
  --space SPACE_KEY \
  [--parent-id 12345]   # 부모 페이지 ID
  [--draft output/draft.html]  # 기본값: output/draft.html
```

**사전 조건:** `output/draft.html`에 Confluence Storage Format(XHTML)이 저장되어 있어야 함.

**출력 (stdout):**
```
[CREATE] 페이지 생성 완료
URL: https://musinsa-oneteam.atlassian.net/wiki/spaces/DEV/pages/123456
```
또는:
```
[UPDATE] 페이지 업데이트 완료 (버전: 3 → 4)
URL: https://...
```

**반환 코드:**
- `0` — HTTP 200/201 성공
- `1` — 오류 (상세 메시지는 stderr)

---

## fetch_comments.py 호출 규약

```bash
python3 .claude/skills/confluence-tool/scripts/fetch_comments.py \
  --page-id PAGE_ID \
  [--output output/comments.md]   # 파일 저장 (미지정 시 stdout)
  [--json]                         # JSON 형식 출력
```

**출력 (기본 마크다운):**
```markdown
# 댓글 목록 — 페이지 제목
URL: https://...

## [1] 홍길동 (2026-03-10)
댓글 내용...

## [2] 김철수 (2026-03-11)
댓글 내용...
```

**반환 코드:**
- `0` — 성공 (댓글 없어도 성공)
- `1` — 인증 오류 또는 페이지 없음

---

## 오류 처리 규칙

1. `client.py`는 모든 HTTP 오류에 대해 **1회 자동 재시도** 후 실패 시 예외 발생.
2. 401 오류: `[AUTH ERROR]` 접두사와 함께 토큰 만료 가능성 안내.
3. 404 오류: Space 키 또는 페이지 ID 미존재로 안내.
4. 로그는 `output/confluence_skill.log`에 append 기록.
