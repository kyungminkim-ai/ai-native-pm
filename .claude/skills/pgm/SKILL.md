---
description: Weekly Flash 보고서 생성, 회의록 기반 Jira Initiative 코멘트 작성, 이니셔티브 주간 현황 정리를 수행하는 PGM(Program Management) 에이전트
---

# /pgm — PGM Command Center

## 모델

`claude-sonnet-4-6`

## 사용법

```
/pgm [JIRA_KEY] [메모]                        ← Flash Report만
/pgm --weekly [CONFLUENCE_URL]                 ← 회의록 → Jira 코멘트만
/pgm --full [JIRA_KEY] [CONFLUENCE_URL] [메모] ← 전체 통합 실행
```

## 모드 설명

| 모드 | 커맨드 | 출력 |
|------|--------|------|
| **flash** (기본) | `/pgm MATCH "메모 내용"` | Flash Report (MD + Docs + Gmail) |
| **weekly** | `/pgm --weekly https://confluence-url` | Jira Initiative Weekly 코멘트 게시 |
| **full** | `/pgm --full MATCH https://confluence-url "메모"` | flash + 회의록 + Jira 코멘트 전부 |

## 실행 규칙

1. `pgm-agent-system/CLAUDE.md`를 읽어 에이전트 역할과 전체 워크플로우를 파악한다.

2. **args 파싱**:
   - `--weekly [URL]` → weekly 모드. URL에서 Confluence PAGE_ID 추출.
   - `--full [JIRA_KEY] [URL] [메모]` → full 모드. 각 인자 분리.
   - 나머지 → flash 모드. 첫 번째 대문자 토큰이 JIRA_KEY, 나머지는 메모.
   - args가 없으면 사용자에게 Jira 프로젝트 키(및 회의록 URL)를 요청.

3. **체크포인트 확인** (Step 0):
   - `pgm-agent-system/output/.pipeline_state.json` 확인
   - 오늘 날짜의 실행 기록이 있으면 재실행 모드 (완료 단계 스킵)

4. `pgm-agent-system/CLAUDE.md`에 정의된 워크플로우(Step 1~5)를 실행한다.

5. 최종 산출물은 `pgm-agent-system/output/` 폴더에 저장, `_artifacts.json` 갱신.

## 빠른 실행 예시

```
# 이번 주 Flash Report
/pgm MATCH "Auxia 미팅 결과: 프로모 캘린더 공유 완료"

# 회의록만 Jira에 반영
/pgm --weekly https://musinsa-oneteam.atlassian.net/wiki/spaces/PE/pages/12345678

# 전체 통합 (Flash + 회의록 + Jira 코멘트)
/pgm --full MATCH https://musinsa-oneteam.atlassian.net/wiki/spaces/PE/pages/12345678
```
