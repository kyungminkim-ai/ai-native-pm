# Notion Tool — Skill 호출 규약

## 개요

Notion API와 통신하는 공통 스킬.
`client.py`(인증/공통), `search.py`(검색), `fetch_page.py`(페이지 읽기),
`write_page.py`(페이지 생성/업데이트), `query_db.py`(DB 조회/업데이트)로 구성된다.

## 필수 환경변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `NOTION_API_TOKEN` | Notion Internal Integration Token | `secret_abc...` |

선택 변수:
- `NOTION_DEFAULT_PAGE_ID` — 기본 부모 페이지 ID (write_page.py에서 parent 미지정 시 사용)

---

## search.py 호출 규약

```bash
python3 .claude/skills/notion-tool/scripts/search.py \
  --query "검색어" \
  [--filter page|database]   # 미지정 시 둘 다 검색
  [--limit 10]               # 기본값: 10
```

**출력 (stdout):**
```json
{
  "query": "검색어",
  "total": 3,
  "results": [
    {
      "id": "page-id",
      "title": "페이지 제목",
      "type": "page",
      "url": "https://notion.so/...",
      "last_edited": "2026-03-07"
    }
  ]
}
```

**`output/notion_context.json`에도 동일 내용 저장.**

---

## fetch_page.py 호출 규약

```bash
python3 .claude/skills/notion-tool/scripts/fetch_page.py \
  --page-id "PAGE_ID_OR_URL" \
  [--output output/notion_page.md]   # 기본값: stdout
  [--depth 2]                        # 중첩 블록 깊이 (기본값: 2)
```

**출력:** 페이지 내용을 마크다운으로 변환하여 출력.

---

## write_page.py 호출 규약

```bash
python3 .claude/skills/notion-tool/scripts/write_page.py \
  --title "페이지 제목" \
  --content output/draft.md \       # 마크다운 파일 경로
  [--parent-id PAGE_OR_DB_ID]       # 부모 페이지/DB ID
  [--page-id EXISTING_PAGE_ID]      # 기존 페이지 업데이트 시
  [--icon "📄"]                     # 이모지 아이콘 (선택)
```

**출력 (stdout):**
```
[CREATE] 페이지 생성 완료
URL: https://notion.so/...
PAGE_ID: abc123
```
또는:
```
[UPDATE] 페이지 업데이트 완료
URL: https://notion.so/...
```

---

## query_db.py 호출 규약

```bash
# DB 조회
python3 .claude/skills/notion-tool/scripts/query_db.py \
  --db-id "DATABASE_ID" \
  [--filter '{"property": "Status", "select": {"equals": "In Progress"}}'] \
  [--sort '{"property": "Created", "direction": "descending"}'] \
  [--limit 20]

# DB 아이템 업데이트
python3 .claude/skills/notion-tool/scripts/query_db.py \
  --update-page-id "PAGE_ID" \
  --properties '{"Status": {"select": {"name": "Done"}}}'
```

**출력 (stdout):**
```json
{
  "database_id": "...",
  "total": 5,
  "results": [
    {
      "id": "page-id",
      "title": "아이템 제목",
      "properties": { ... },
      "url": "https://notion.so/..."
    }
  ]
}
```

---

## 에이전트 활용 패턴

### Notion → 에이전트 입력
```bash
# 1. 페이지 읽기
python3 .claude/skills/notion-tool/scripts/fetch_page.py --page-id URL_OR_ID --output output/notion_page.md
# 2. 읽은 내용을 에이전트 컨텍스트로 활용
```

### 에이전트 → Notion 저장
```bash
# 1. draft.md 생성 (에이전트가 작성)
# 2. Notion 페이지로 저장
python3 .claude/skills/notion-tool/scripts/write_page.py --title "제목" --content output/draft.md --parent-id PARENT_ID
```

### Notion DB 현황 조회
```bash
python3 .claude/skills/notion-tool/scripts/query_db.py --db-id DATABASE_ID --limit 50
```

---

## 오류 처리 규칙

1. `client.py`는 모든 HTTP 오류에 대해 **1회 자동 재시도** 후 실패 시 예외 발생.
2. 401 오류: `[AUTH ERROR]` — API 토큰 확인 안내.
3. 404 오류: `[NOT FOUND]` — 페이지 ID 또는 DB ID 확인 + Integration 공유 여부 확인 안내.
4. 로그는 `output/notion_skill.log`에 append 기록.

> **중요:** Notion API는 페이지가 Integration에 공유(Share)되어 있어야 접근 가능.
> 접근 오류 시: 해당 페이지 → Share → Integration 이름 검색 후 초대 필요.
