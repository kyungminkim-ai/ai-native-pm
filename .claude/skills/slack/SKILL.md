---
description: Slack 채널 대화 조회, 키워드 검색, 메시지 발송을 수행하는 Slack 협업 에이전트
---

# /slack — Slack 대화 조회 · AI 챗봇 에이전트

## 모델

`claude-haiku-4-5-20251001`

## 사용법
```
/slack --today [#채널]                              ← 오늘 대화 수집 + 요약
/slack --week [#채널]                               ← 이번 주 대화 수집 + 요약
/slack --read [#채널] --date [YYYY-MM-DD]           ← 특정 날짜 대화 조회
/slack --search "[키워드]" [#채널]                  ← 채널 내 키워드 검색
/slack --send [#채널] "[메시지]"                    ← 메시지 발송 (컨펌 필수)
/slack --initiative TM-XXXX                        ← 이니셔티브 관련 채널 자동 탐색
```

## 실행 규칙
1. `slack-agent-system/CLAUDE.md` 읽어 역할 파악
2. args 파싱:
   - `--today` / `--week` / `--date` → read 모드 (조회 + 요약)
   - `--search` → search 모드
   - `--send` → send 모드 (발송 전 반드시 컨펌)
   - args 없음 → 오늘 기본 채널 대화 요약
3. `SLACK_BOT_TOKEN` 환경변수 확인
   - 없으면 Slack 앱 설정 가이드 출력 후 중단
4. `slack-agent-system/CLAUDE.md` 워크플로우 실행
5. 산출물: `slack-agent-system/output/` 저장

## 환경변수 (`.env`에 추가 필요)
```bash
# Slack Bot 연결 — api.slack.com/apps에서 Bot Token 발급
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
SLACK_DEFAULT_CHANNEL=general        # 기본 채널 (# 없이 입력)
```

## 연결 방식 (택 1)
- **방식 A (기본)**: Python 스크립트 `slack-agent-system/scripts/client.py`
- **방식 B (MCP)**: Slack MCP 서버 설정 시 Claude가 직접 Slack 채널 조회 가능
  - 설정 방법: `slack-agent-system/CLAUDE.md` §연결 설정 참조

## 주의 사항
- 메시지 발송(`--send`)은 반드시 사전 컨펌 (되돌리기 불가)
- Bot이 채널에 참여(invite)되어 있어야 메시지 읽기 가능
- 필요 OAuth Scope: `channels:history`, `channels:read`, `users:read`, `chat:write`
