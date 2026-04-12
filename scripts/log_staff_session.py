#!/usr/bin/env python3
"""
/staff 세션 로그 업데이터 — Claude가 직접 호출

Usage:
  # 세션 시작 (SESSION_ID 반환)
  python3 scripts/log_staff_session.py --start "요청 내용"

  # 세션 완료 기록
  python3 scripts/log_staff_session.py \\
    --end 20260324_103045 \\
    --summary "Campaign Meta Engine PRD 작성" \\
    --skills "/staff,/prd,/red" \\
    --outputs "prd_20260324_xxx.md,redteam_20260324_xxx.md" \\
    --status completed \\
    --tokens-in 12000 \\
    --tokens-out 3500 \\
    --model claude-sonnet-4-6

Log schema (JSONL):
  {
    "id": "20260324_103045",
    "start_ts": "2026-03-24T10:30:45+09:00",
    "end_ts":   "2026-03-24T10:52:10+09:00",
    "request":  "요청 내용 (최대 500자)",
    "summary":  "한 줄 요약",
    "skills":   ["/staff", "/prd", "/red"],   <- 항상 /staff 첫 번째
    "outputs":  ["prd_20260324_xxx.md"],
    "output_types": ["prd", "confluence-page"],  <- 산출물 유형 (아래 목록 참조)
    "status":   "completed",
    "model":    "claude-sonnet-4-6",
    "tokens_in":  12000,
    "tokens_out": 3500,
    "cost_usd":   0.087,                      <- tokens 입력 시 자동 계산
    "duration_sec": 1285                      <- start/end 차이 자동 계산
  }

output_types 허용 값:
  prd             — PRD 문서 (신규 작성)
  prd-edit        — PRD 수정/보완
  2-pager         — 2-Pager 의사결정 문서
  confluence-page — Confluence 페이지 생성
  confluence-edit — Confluence 페이지 수정
  jira-ticket     — Jira 티켓 생성
  diagram         — 다이어그램 (mermaid, flowchart 등)
  meeting-notes   — 회의록
  analysis        — 분석 보고서 / 인사이트
  strategy        — 전략 문서 / 자문
  report          — C레벨 보고서
  markdown-doc    — 일반 마크다운 문서
  script          — Python / 코드 스크립트
  design-spec     — 화면 설계서 (Figma 기반)
  agent-skill     — 에이전트 / 스킬 설계·수정

비용 계산 기준 (2026-03 기준, 1M tokens):
  Sonnet 4.6 : input $3.00  / output $15.00
  Opus 4.6   : input $15.00 / output $75.00
  Haiku 4.5  : input $0.80  / output $4.00
체크포인트 사용법:
  # 작업 중간 상태 저장 (세션 ID 필요)
  python3 scripts/log_staff_session.py \\
    --checkpoint 20260324_103045 \\
    --cp-progress "Phase 2 완료, Phase 3 진행 중" \\
    --cp-decisions "지표: DAU 기준, 스코프: 앱푸시 전용" \\
    --cp-next "requirement-writer 호출 → ux-logic-analyst"

  # 저장된 체크포인트 조회
  python3 scripts/log_staff_session.py --resume 20260324_103045
"""
import json
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
LOG_PATH = Path(__file__).parent.parent / "output" / "logs" / "staff_sessions.jsonl"
CHECKPOINT_PATH = Path(__file__).parent.parent / "output" / "logs" / "staff_checkpoints.jsonl"

# 모델별 비용 (USD per 1M tokens)
MODEL_PRICING = {
    "claude-sonnet-4-6": {"input": 3.00,  "output": 15.00},
    "claude-opus-4-6":   {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5":  {"input": 0.80,  "output": 4.00},
}
DEFAULT_MODEL = "claude-haiku-4-5"


def now_kst():
    return datetime.now(KST).isoformat()


def session_id():
    return datetime.now(KST).strftime("%Y%m%d_%H%M%S")


def calc_cost(model, tokens_in, tokens_out):
    pricing = MODEL_PRICING.get(model)
    if not pricing or (tokens_in == 0 and tokens_out == 0):
        return None
    return round(
        tokens_in  / 1_000_000 * pricing["input"]
        + tokens_out / 1_000_000 * pricing["output"],
        6,
    )


def calc_duration(start_ts, end_ts):
    try:
        start = datetime.fromisoformat(start_ts)
        end   = datetime.fromisoformat(end_ts)
        return int((end - start).total_seconds())
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="/staff 세션 로그 기록")
    parser.add_argument("--start", help="세션 시작: 요청 내용")
    parser.add_argument("--end",   help="세션 종료: SESSION_ID")
    parser.add_argument("--summary", default="", help="세션 요약 (한 줄)")
    parser.add_argument("--skills",  default="",
                        help="사용 스킬, /staff 포함 쉼표 구분 (예: /staff,/prd,/red)")
    parser.add_argument("--outputs", default="", help="산출물 파일 (쉼표 구분)")
    parser.add_argument("--output-types", default="", dest="output_types",
                        help="산출물 유형 (쉼표 구분, 예: prd,confluence-page)")
    parser.add_argument("--status",  default="completed",
                        choices=["started", "completed", "failed", "interrupted"])
    parser.add_argument("--model",      default="", help=f"사용 모델 (기본: {DEFAULT_MODEL})")
    parser.add_argument("--tokens-in",  type=int, default=0, dest="tokens_in",
                        help="입력 토큰 수 (선택)")
    parser.add_argument("--tokens-out", type=int, default=0, dest="tokens_out",
                        help="출력 토큰 수 (선택)")
    # 체크포인트
    parser.add_argument("--checkpoint", metavar="SESSION_ID",
                        help="작업 중간 상태 저장: SESSION_ID 지정")
    parser.add_argument("--cp-progress", default="", dest="cp_progress",
                        help="현재 진행 상황 (예: 'Phase 2 완료, Phase 3 진행 중')")
    parser.add_argument("--cp-decisions", default="", dest="cp_decisions",
                        help="지금까지 결정된 사항 (예: '지표: DAU, 스코프: 앱푸시')")
    parser.add_argument("--cp-next", default="", dest="cp_next",
                        help="다음 수행할 작업 (예: 'requirement-writer 호출')")
    parser.add_argument("--resume", metavar="SESSION_ID",
                        help="저장된 체크포인트 조회: SESSION_ID 지정")
    args = parser.parse_args()

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # ── 세션 시작 ──────────────────────────────────────────────────────────────
    if args.start:
        sid = session_id()
        entry = {
            "id":           sid,
            "start_ts":     now_kst(),
            "end_ts":       None,
            "request":      args.start[:500],
            "summary":      args.summary,
            "skills":       [],
            "outputs":      [],
            "output_types": [],
            "status":       "started",
            "model":        args.model or DEFAULT_MODEL,
            "tokens_in":    0,
            "tokens_out":   0,
            "cost_usd":     None,
            "duration_sec": None,
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"SESSION_ID={sid}")

    # ── 세션 완료 ──────────────────────────────────────────────────────────────
    elif args.end:
        sid = args.end
        lines   = []
        updated = False

        if LOG_PATH.exists():
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        lines.append(line)
                        continue

                    if entry["id"] == sid and entry["status"] == "started":
                        end_ts     = now_kst()
                        model      = args.model or entry.get("model") or DEFAULT_MODEL
                        tokens_in  = args.tokens_in  or entry.get("tokens_in",  0)
                        tokens_out = args.tokens_out or entry.get("tokens_out", 0)

                        entry.update({
                            "end_ts":       end_ts,
                            "status":       args.status,
                            "model":        model,
                            "tokens_in":    tokens_in,
                            "tokens_out":   tokens_out,
                            "cost_usd":     calc_cost(model, tokens_in, tokens_out),
                            "duration_sec": calc_duration(entry["start_ts"], end_ts),
                        })
                        if args.summary:
                            entry["summary"] = args.summary
                        if args.skills:
                            entry["skills"] = [s.strip() for s in args.skills.split(",") if s.strip()]
                        if args.outputs:
                            entry["outputs"] = [o.strip() for o in args.outputs.split(",") if o.strip()]
                        if args.output_types:
                            entry["output_types"] = [t.strip() for t in args.output_types.split(",") if t.strip()]
                        elif "output_types" not in entry:
                            entry["output_types"] = []
                        updated = True

                    lines.append(json.dumps(entry, ensure_ascii=False))

            with open(LOG_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

        if updated:
            print(f"OK: Session {sid} → {args.status}")
        else:
            # 시작 기록 없을 때 fallback: 완료 엔트리 직접 생성
            model      = args.model or DEFAULT_MODEL
            tokens_in  = args.tokens_in
            tokens_out = args.tokens_out
            entry = {
                "id":           sid,
                "start_ts":     now_kst(),
                "end_ts":       now_kst(),
                "request":      args.summary or "(unknown)",
                "summary":      args.summary,
                "skills":       [s.strip() for s in args.skills.split(",")  if s.strip()],
                "outputs":      [o.strip() for o in args.outputs.split(",") if o.strip()],
                "output_types": [t.strip() for t in args.output_types.split(",") if t.strip()],
                "status":       args.status,
                "model":        model,
                "tokens_in":    tokens_in,
                "tokens_out":   tokens_out,
                "cost_usd":     calc_cost(model, tokens_in, tokens_out),
                "duration_sec": None,
            }
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(f"OK: New entry created for {sid}")

    # ── 체크포인트 저장 ────────────────────────────────────────────────────────
    elif args.checkpoint:
        CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
        cp = {
            "session_id": args.checkpoint,
            "ts":         now_kst(),
            "progress":   args.cp_progress,
            "decisions":  args.cp_decisions,
            "next":       args.cp_next,
        }
        with open(CHECKPOINT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(cp, ensure_ascii=False) + "\n")
        print(f"CHECKPOINT saved for session {args.checkpoint}")

    # ── 체크포인트 조회 ────────────────────────────────────────────────────────
    elif args.resume:
        sid = args.resume
        if not CHECKPOINT_PATH.exists():
            print(f"No checkpoints found.")
            sys.exit(0)
        checkpoints = []
        with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    cp = json.loads(line)
                    if cp.get("session_id") == sid:
                        checkpoints.append(cp)
                except json.JSONDecodeError:
                    continue
        if not checkpoints:
            print(f"No checkpoints found for session {sid}.")
        else:
            latest = checkpoints[-1]
            print(f"=== Checkpoint for session {sid} (latest of {len(checkpoints)}) ===")
            print(f"Saved at:  {latest.get('ts', '-')}")
            print(f"Progress:  {latest.get('progress', '-')}")
            print(f"Decisions: {latest.get('decisions', '-')}")
            print(f"Next:      {latest.get('next', '-')}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
