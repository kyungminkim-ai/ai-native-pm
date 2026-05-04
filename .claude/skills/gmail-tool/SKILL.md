# gmail-tool — Skill Spec

## 역할

Weekly Flash 보고서를 Gmail로 발송하는 스킬.
마크다운 → 이메일 HTML 변환(`md_to_html.py`)과 Gmail SMTP 발송(`send_email.py`) 두 스크립트로 구성된다.

---

## 사전 준비

### 환경변수 설정

```bash
export GMAIL_USER="your-address@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"   # Gmail 앱 비밀번호 (16자리)
```

Gmail 앱 비밀번호 발급 경로:
`Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호`

> 일반 Gmail 비밀번호는 사용 불가. 반드시 앱 비밀번호를 사용할 것.

---

## 원본 보존 원칙

> Confluence 페이지를 이메일로 변환할 때는 LLM이 본문을 재작성하지 않는다.
> `source_page.xhtml`이 있으면 반드시 `xhtml_to_email_html.py`를 사용한다.
> `md_to_html.py`는 마크다운 전용 문서(xhtml 없는 경우)에만 사용한다.

---

## 스크립트 명세

### 1. xhtml_to_email_html.py — Confluence XHTML → 이메일 HTML 변환 (우선 사용)

```
사용법:
  python3 .claude/skills/gmail-tool/scripts/xhtml_to_email_html.py \
    --input output/source_page.xhtml \
    --title "페이지 제목" \
    --source-url "https://..." \
    --output output/final_email.html

파라미터:
  --input   -i   Confluence XHTML 파일 또는 fetch_page.py --json 출력 파일 (필수)
  --output  -o   저장할 HTML 파일 경로 (기본: stdout)
  --title   -t   페이지 제목 (JSON 입력 시 자동 추출)
  --source-url -u  Confluence 원문 URL (푸터 링크용)

동작:
  - Confluence 매크로(ac:*, ri:*) 제거
  - 본문 텍스트·구조(테이블·헤딩·불릿)는 원본 그대로 보존
  - 이메일 클라이언트 호환 인라인 CSS만 주입
  - Confluence 패널(panel 매크로) → Notion 스타일 콜아웃으로 자동 변환
    · panelIcon 값에 따라 이모지·배경색 자동 결정
    · 커스텀 bgColor 파라미터가 있으면 배경색 우선 적용
    · table 레이아웃(이메일 클라이언트 호환)으로 렌더링

패널 아이콘 → 콜아웃 스타일 매핑:
  :info:    → ℹ️  배경 #EAF3FF (파랑)
  :check:   → ✅  배경 #EDFAF1 (초록)
  :warning: → ⚠️  배경 #FFFAE6 (노랑)
  :error:   → ❌  배경 #FFF0F0 (빨강)
  :tip:     → 💡  배경 #FFFDF0 (주황)
  :note:    → 📝  배경 #F3F0FF (보라)
  기타      → 💬  배경 #F4F5F7 (회색)

종료 코드:
  0 - 성공  1 - 입력 파일 없음  2 - 변환 오류
```

### 2. md_to_html.py — 마크다운 → 이메일 HTML 변환 (fallback)

```
사용법:
  python3 .claude/skills/gmail-tool/scripts/md_to_html.py \
    --input output/weekly_flash_v1.md \
    --output output/final_email.html

파라미터:
  --input   -i   변환할 마크다운 파일 경로 (필수)
  --output  -o   저장할 HTML 파일 경로 (기본: stdout)
  --title   -t   <title> 태그용 제목 (선택, 없으면 md 첫 h1 사용)

출력:
  인라인 CSS가 적용된 완전한 HTML 문서 (<!DOCTYPE html> 포함)
  이메일 클라이언트 호환성을 위해 외부 CSS/JS 없음

종료 코드:
  0 - 성공
  1 - 입력 파일 없음
  2 - 변환 오류
```

### 2. send_email.py — Gmail SMTP 발송

```
사용법:
  python3 .claude/skills/gmail-tool/scripts/send_email.py \
    --to "a@example.com,b@example.com" \
    --subject "[Weekly Flash] 2026년 3월 1주차" \
    --html-file output/final_email.html

파라미터:
  --to           수신자 (쉼표 구분, 필수)
  --subject  -s  메일 제목 (필수)
  --html-file    HTML 본문 파일 경로 (필수)
  --from         발신자 표시명 (선택, 기본: GMAIL_USER)
  --cc           참조 수신자 (선택, 쉼표 구분)

환경변수:
  GMAIL_USER          발신 Gmail 주소
  GMAIL_APP_PASSWORD  Gmail 앱 비밀번호

종료 코드:
  0 - 발송 성공
  1 - 인증 오류 (GMAIL_USER / GMAIL_APP_PASSWORD 문제)
  2 - 수신자 주소 오류
  3 - SMTP 연결 또는 기타 오류
```

---

## 호출 패턴 (mail-specialist 기준)

```
# [우선] Confluence 페이지 → HTML (source_page.xhtml 있을 때)
python3 .claude/skills/gmail-tool/scripts/xhtml_to_email_html.py \
  --input output/source_page.xhtml \
  --title "Auxia x Musinsa — Weekly Flash Report (26-03-06)" \
  --source-url "https://musinsa-oneteam.atlassian.net/wiki/spaces/.../pages/335872388" \
  --output output/final_email.html

# [fallback] 마크다운 → HTML (xhtml 없을 때만)
python3 .claude/skills/gmail-tool/scripts/md_to_html.py \
  --input output/weekly_flash_v1.md \
  --output output/final_email.html

# 발송 (사용자 승인 후)
python3 .claude/skills/gmail-tool/scripts/send_email.py \
  --to "team@example.com" \
  --subject "[Weekly Flash] 2026년 3월 1주차" \
  --html-file output/final_email.html
```

---

## 오류 대응표

| 오류 | 원인 | 해결 |
|------|------|------|
| `GMAIL_USER not set` | 환경변수 미설정 | `.env` 파일 또는 `export` 명령으로 설정 |
| `Authentication failed` | 앱 비밀번호 오류 | Google 계정에서 앱 비밀번호 재발급 |
| `SMTPRecipientsRefused` | 잘못된 수신자 주소 | 이메일 형식 확인 (`@` 포함) |
| `Connection refused` | 방화벽 또는 네트워크 | SMTP 포트 587 허용 여부 확인 |
