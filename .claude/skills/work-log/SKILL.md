# /work-log — 주간 작업 로그 자동 정리 에이전트

## 사용법

```
/work-log
/work-log --week-offset -1   # 지난 주
/work-log --no-jira          # Jira/Confluence 수집 없이 프롬프트 로그만 정리
```

## 역할

이번 주 Claude와의 대화 내역(프롬프트 로그)과 Jira/Confluence 활동 데이터를 결합하여
PM 관점의 주간 작업 회고 문서를 자동 생성한다.

---

## 실행 규칙

### Step 1. 프롬프트 로그 수집

1. 아래 Python 스크립트를 실행하여 이번 주 세션 파일 목록과 사용자 프롬프트를 수집한다.

```python
import json, os, glob
from datetime import date, timedelta

# 이번 주 월요일 계산
today = date.today()
monday = today - timedelta(days=today.weekday())
week_start = monday.isoformat()

base = os.path.expanduser("~/.claude/projects/")
# 현재 프로젝트 경로에 맞는 폴더 자동 탐지
project_dirs = glob.glob(base + "*pm-studio*/")

skip_prefixes = ('<', 'This session is being continued', 'Tool loaded',
                 'Called the Read', 'Result of calling', 'Note:', 'Base directory')

results = []
for project_dir in project_dirs:
    for fp in glob.glob(project_dir + "*.jsonl"):
        with open(fp) as f:
            first = f.readline()
            try:
                obj = json.loads(first)
                ts = obj.get('timestamp', '')
                if ts[:10] < week_start:
                    continue
                date_str = ts[:10]
            except:
                continue
        session_prompts = []
        with open(fp) as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if obj.get('type') == 'user':
                        content = obj.get('message', {}).get('content', '')
                        texts = []
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and c.get('type') == 'text':
                                    texts.append(c.get('text', ''))
                        elif isinstance(content, str):
                            texts.append(content)
                        for text in texts:
                            text = text.strip()
                            if len(text) < 15: continue
                            if any(text.startswith(p) for p in skip_prefixes): continue
                            session_prompts.append(text[:400])
                except:
                    pass
        if session_prompts:
            results.append({'date': date_str, 'file': os.path.basename(fp), 'prompts': session_prompts})

results.sort(key=lambda x: x['date'])
print(json.dumps(results, ensure_ascii=False, indent=2))
```

2. 수집된 프롬프트를 날짜별로 그룹화하고 **작업 테마**를 도출한다.
   - 테마 예시: PRD 작업, 에이전트 구축, 데이터 분석, 보고서 작성, 시스템 정비 등

### Step 2. Jira/Confluence 데이터 수집 (--no-jira 없을 때)

`scripts/weekly_digest.py`를 실행하여 이번 주 Jira/Confluence 활동 데이터를 수집한다.

```bash
python3 scripts/weekly_digest.py
```

이미 `output/weekly_digest_{YYYYMMDD}.json`이 존재하면 재실행하지 않고 해당 파일을 사용한다.

### Step 3. 주간 작업 로그 문서 생성

아래 구조로 `output/work_log_{YYYYMMDD}.md`를 생성한다.

```markdown
# 주간 작업 로그 — {week_start} ~ {week_end}
> 생성일: {today} | PM: {email}

## 이번 주 요약

| 항목 | 수치 |
|------|------|
| 총 대화 세션 | N건 |
| Jira 담당 티켓 | N건 |
| Jira 생성 티켓 | N건 |
| Confluence 수정 | N건 |
| Confluence 생성 | N건 |

## 프롬프트 로그 (날짜별)

### {날짜}
- 요청 1: ...
- 요청 2: ...

## 작업 테마별 정리

### [테마명] (N건)
**주요 요청:**
- ...

**결과물:**
- ...

## 회고 & 인사이트

- 이번 주 가장 많이 반복된 작업 패턴:
- AI 활용으로 아낀 예상 시간:
- 개선이 필요한 부분:

## 다음 주 예상 작업
- [ ] ...
```

---

## 출력

- `output/work_log_{YYYYMMDD}.md` — 주간 작업 로그 (마크다운)
- 완료 후 터미널에 요약 출력

---

## 참고

- 프롬프트 로그는 `~/.claude/projects/*pm-studio*/*.jsonl` 파일에서 수집
- Jira/Confluence 데이터는 `scripts/weekly_digest.py` 활용
- 환경변수: `CONFLUENCE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN`
