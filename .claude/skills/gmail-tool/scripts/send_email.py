"""
gmail-tool — Gmail SMTP 이메일 발송 스크립트

사용법:
  python3 send_email.py \
    --to "a@example.com,b@example.com" \
    --subject "[Weekly Flash] 2026년 3월 1주차" \
    --html-file output/final_email.html

환경변수:
  GMAIL_USER          발신 Gmail 주소 (필수)
  GMAIL_APP_PASSWORD  Gmail 앱 비밀번호 16자리 (필수)

종료 코드:
  0 - 발송 성공
  1 - 인증 오류
  2 - 수신자 주소 오류
  3 - SMTP 연결 / 기타 오류
"""

import argparse
import json
import os
import re
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
LOG_FILE = Path(__file__).parents[4] / "output" / "send_log.json"


# ─── 유틸 ────────────────────────────────────────────────────────────────

def _validate_email(address: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", address.strip()))


def _parse_recipients(raw: str) -> tuple[list[str], list[str]]:
    """쉼표 구분 이메일 문자열을 파싱. (유효 목록, 무효 목록) 반환."""
    addresses = [a.strip() for a in raw.split(",") if a.strip()]
    valid = [a for a in addresses if _validate_email(a)]
    invalid = [a for a in addresses if not _validate_email(a)]
    return valid, invalid


def _append_log(entry: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {"logs": []}
    if LOG_FILE.exists():
        try:
            data = json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {"logs": []}
    data["logs"].append(entry)
    LOG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ─── 발송 함수 ───────────────────────────────────────────────────────────

def send_email(
    recipients: list[str],
    subject: str,
    html_body: str,
    sender: str,
    password: str,
    cc: list[str] | None = None,
) -> None:
    """Gmail SMTP(TLS)로 HTML 이메일 발송. 실패 시 예외 발생."""
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = ", ".join(cc)

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    all_recipients = recipients + (cc or [])

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender, password)
        server.sendmail(sender, all_recipients, msg.as_string())


# ─── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gmail SMTP 이메일 발송")
    parser.add_argument("--to", required=True, help="수신자 이메일 (쉼표 구분)")
    parser.add_argument("--subject", "-s", required=True, help="메일 제목")
    parser.add_argument("--html-file", required=True, help="HTML 본문 파일 경로")
    parser.add_argument("--from", dest="sender", help="발신자 표시명 (기본: GMAIL_USER)")
    parser.add_argument("--cc", help="참조 수신자 (쉼표 구분, 선택)")
    args = parser.parse_args()

    # ── 환경변수 확인 ────────────────────────────────────────
    gmail_user = os.environ.get("GMAIL_USER", "").strip()
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "").strip()

    if not gmail_user or not gmail_pass:
        missing = []
        if not gmail_user:
            missing.append("GMAIL_USER")
        if not gmail_pass:
            missing.append("GMAIL_APP_PASSWORD")
        print(f"[ERROR] 환경변수 미설정: {', '.join(missing)}", file=sys.stderr)
        print("  export GMAIL_USER='your@gmail.com'", file=sys.stderr)
        print("  export GMAIL_APP_PASSWORD='xxxx xxxx xxxx xxxx'", file=sys.stderr)
        sys.exit(1)

    sender = args.sender or gmail_user

    # ── 수신자 검증 ──────────────────────────────────────────
    valid_to, invalid_to = _parse_recipients(args.to)
    if invalid_to:
        print(f"[WARN] 유효하지 않은 수신자 주소 제거됨: {invalid_to}", file=sys.stderr)
    if not valid_to:
        print("[ERROR] 유효한 수신자가 없습니다.", file=sys.stderr)
        sys.exit(2)

    valid_cc: list[str] = []
    if args.cc:
        valid_cc, invalid_cc = _parse_recipients(args.cc)
        if invalid_cc:
            print(f"[WARN] 유효하지 않은 참조 주소 제거됨: {invalid_cc}", file=sys.stderr)

    # ── HTML 파일 로드 ───────────────────────────────────────
    html_path = Path(args.html_file)
    if not html_path.exists():
        print(f"[ERROR] HTML 파일 없음: {html_path}", file=sys.stderr)
        sys.exit(3)
    html_body = html_path.read_text(encoding="utf-8")

    # ── 발송 ────────────────────────────────────────────────
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "subject": args.subject,
        "recipients": valid_to,
        "cc": valid_cc,
        "html_file": str(html_path),
        "status": "failed",
    }

    try:
        send_email(
            recipients=valid_to,
            subject=args.subject,
            html_body=html_body,
            sender=sender,
            password=gmail_pass,
            cc=valid_cc or None,
        )
        log_entry["status"] = "sent"
        _append_log(log_entry)

        print(f"[OK] 이메일 발송 완료")
        print(f"     제목: {args.subject}")
        print(f"     수신: {', '.join(valid_to)}")
        if valid_cc:
            print(f"     참조: {', '.join(valid_cc)}")
        print(f"     로그: {LOG_FILE}")

    except smtplib.SMTPAuthenticationError as e:
        _append_log(log_entry)
        print(f"[ERROR] Gmail 인증 실패: {e}", file=sys.stderr)
        print("  GMAIL_USER와 GMAIL_APP_PASSWORD 환경변수를 확인하세요.", file=sys.stderr)
        print("  앱 비밀번호: Google 계정 → 보안 → 2단계 인증 → 앱 비밀번호", file=sys.stderr)
        sys.exit(1)

    except smtplib.SMTPRecipientsRefused as e:
        _append_log(log_entry)
        print(f"[ERROR] 수신자 거부됨: {e}", file=sys.stderr)
        sys.exit(2)

    except (smtplib.SMTPException, OSError) as e:
        _append_log(log_entry)
        print(f"[ERROR] SMTP 오류: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
