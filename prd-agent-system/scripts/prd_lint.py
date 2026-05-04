#!/usr/bin/env python3
"""
prd_lint.py — PRD 마크다운 구조 자동 검증 (Phase 3 Step 3-C)

Usage:
    python3 prd-agent-system/scripts/prd_lint.py output/prd_YYYYMMDD_주제.md

Exit codes:
    0 — 전체 통과
    1 — 오류 있음 (에러 로그 출력)
"""
import re
import sys
from pathlib import Path

# ─── 설정 ──────────────────────────────────────────────────────────────────

FORBIDDEN_EXPRESSIONS = [
    "엔지니어와 협의",
    "개발팀과 상의",
    "기술적으로 가능한 범위에서",
    "추후 결정",
    "나중에 정함",
    "알아서 결정",
    "적절히 처리",
]
TBD_PATTERN = re.compile(r'\bTBD\b(?!\s*[-—]\s*\S)')  # 단독 TBD (설명 없는 것만)

EX_PERSPECTIVE_KEYWORDS = {
    "INPUT": ["input", "입력", "빈값", "형식", "허용 범위", "유효성"],
    "AUTH":  ["auth", "권한", "인증", "비로그인", "차단", "접근 불가"],
    "SYS":   ["sys", "타임아웃", "timeout", "api 실패", "서버 오류", "외부 api"],
    "BIZ":   ["biz", "중복", "한도", "이미 완료", "비즈니스", "정책"],
    "RACE":  ["race", "동시", "경쟁", "lock", "재고 경쟁", "동시성"],
}

MILESTONE_MARKERS = ["M1", "M2", "M3", "마일스톤", "Milestone", "개발 :", "QA :"]

# ─── 검사 함수 ─────────────────────────────────────────────────────────────

def check_ac_structure(content: str) -> list[str]:
    """AC-NNN: / Given: / When: / Then: 구조 검사"""
    errors = []
    ac_ids = re.findall(r'AC-(\d{3}):', content)
    for ac_id in ac_ids:
        # AC-NNN: 이후 블록에서 Given/When/Then 존재 여부 확인
        block_match = re.search(
            rf'AC-{ac_id}:.*?(?=AC-\d{{3}}:|\Z)',
            content, re.DOTALL
        )
        if block_match:
            block = block_match.group(0)
            missing = []
            if 'Given:' not in block:
                missing.append('Given')
            if 'When:' not in block:
                missing.append('When')
            if 'Then:' not in block:
                missing.append('Then')
            if missing:
                errors.append(f"AC-{ac_id}: {'/'.join(missing)} 누락")
    return errors


def check_ex_count(content: str) -> tuple[list[str], list[str]]:
    """EX-NNN 최소 5개 + 5가지 관점 각 1개 이상 검사"""
    errors = []
    warnings = []

    ex_ids = re.findall(r'EX-\d{3}', content)
    if len(ex_ids) < 5:
        errors.append(f"EX 시나리오 {len(ex_ids)}개 — 최소 5개 필요 ({5 - len(ex_ids)}개 부족)")

    # 관점 커버리지 검사 (EX 행 전체 텍스트에서 키워드 탐색)
    ex_section = re.search(
        r'(EX-001.*?)(?=##|\Z)', content, re.DOTALL
    )
    ex_text = ex_section.group(1).lower() if ex_section else content.lower()

    missing_perspectives = []
    for perspective, keywords in EX_PERSPECTIVE_KEYWORDS.items():
        found = any(kw in ex_text for kw in keywords)
        if not found:
            missing_perspectives.append(perspective)

    if missing_perspectives:
        errors.append(
            f"EX 관점 누락: {', '.join(missing_perspectives)} "
            f"— 각 관점(INPUT/AUTH/SYS/BIZ/RACE) 최소 1개 필요"
        )

    return errors, warnings


def check_oq_format(content: str) -> list[str]:
    """OQ-NNN 형식 일치 검사"""
    errors = []
    # OQ 언급은 있는데 형식이 틀린 경우
    oq_raw = re.findall(r'OQ[-\s]?(\d+)', content)
    oq_correct = re.findall(r'OQ-\d{3}', content)
    if len(oq_raw) > len(oq_correct):
        errors.append(
            f"OQ 형식 불일치 — OQ-NNN (3자리) 형식 사용 필요. "
            f"발견된 패턴 {len(oq_raw)}개 중 올바른 형식 {len(oq_correct)}개"
        )
    return errors


def check_forbidden_expressions(content: str) -> list[str]:
    """금지 표현 검사"""
    errors = []
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        for expr in FORBIDDEN_EXPRESSIONS:
            if expr in line:
                preview = line.strip()[:80]
                errors.append(f"금지 표현 '{expr}' — L{i}: {preview}")
        if TBD_PATTERN.search(line):
            preview = line.strip()[:80]
            errors.append(f"단독 TBD (설명 없음) — L{i}: {preview}")
    return errors


def check_ex_log_consistency(content: str) -> tuple[list[str], list[str]]:
    """EX 케이스 유형-로그 타입 일관성 경고 (WARN only — 기존 PRD 호환성 유지)"""
    warnings = []

    # BIZ/RACE 케이스에 "오류 로그" 단독 기재 감지
    for match in re.finditer(
        r'\|\s*(EX-\d{3})\s*\|\s*(BIZ|RACE)\s*\|[^\n]*오류 로그[^\n]*',
        content
    ):
        ex_id = re.search(r'EX-\d{3}', match.group(0))
        if ex_id:
            warnings.append(
                f"{ex_id.group()} [{match.group(2)}]: '오류 로그' 단독 기재 — "
                f"비즈니스 결과는 DROP_BIZ_LOG 사용 권장"
            )

    # SYS/AUTH 케이스에 알람/Guardrail 미언급 감지
    for match in re.finditer(
        r'\|\s*(EX-\d{3})\s*\|\s*(SYS|AUTH)\s*\|([^\n]+)',
        content
    ):
        row = match.group(3)
        has_alarm = any(
            kw in row for kw in ['알람', '알림', '온콜', 'Guardrail', 'guardrail', '모니터링', '✅ 필수']
        )
        if not has_alarm:
            warnings.append(
                f"{match.group(1)} [{match.group(2)}]: EXCEPTIONAL 케이스에 알람/Guardrail 미언급"
            )

    return [], warnings


def check_fr_ex_linkage(content: str) -> tuple[list[str], list[str]]:
    """FR-EX 크로스레퍼런스 존재 여부 경고 (WARN only)"""
    warnings = []

    has_ex = bool(re.search(r'EX-\d{3}', content))
    has_fr_ex_link = bool(re.search(r'관련\s*EX.*EX-\d{3}', content))
    has_fr_ex_placeholder = bool(re.search(r'관련\s*EX\s*:\s*-', content))

    if has_ex and not has_fr_ex_link:
        warnings.append(
            "FR-EX 크로스레퍼런스 없음 — "
            "Functional Requirements에 관련 EX ID 연결 권장 (edge-case-analyst Step 4)"
        )
    elif has_fr_ex_placeholder:
        count = len(re.findall(r'관련\s*EX\s*:\s*-', content))
        warnings.append(
            f"FR-EX 플레이스홀더 {count}개 미채움 — "
            f"edge-case-analyst Step 4 출력으로 채울 것"
        )

    return [], warnings


def check_execution_plan(content: str) -> list[str]:
    """7-1 실행 계획 공백 검사"""
    errors = []
    # 7-1 섹션 추출
    section_match = re.search(
        r'##\s*7[-.]1[^\n]*\n(.*?)(?=##\s*7[-.]2|##\s*7[-.]3|\Z)',
        content, re.DOTALL
    )
    if section_match:
        section_content = section_match.group(1).strip()
        if not section_content or len(section_content) < 20:
            errors.append(
                "7-1 Phased Approach 공백 — 최소 M1 마일스톤 구조를 삽입해야 합니다.\n"
                "  [마일스톤 템플릿]\n"
                "  | # | 마일스톤 | 담당 | 시작일 | 완료 목표일 | 상태 |\n"
                "  |---|---------|------|--------|------------|------|\n"
                "  | M1 | {주요 인프라/API 설계} | BE/DS/FE | {미정} | {미정} | Not Started |"
            )
        else:
            has_milestone = any(m in section_content for m in MILESTONE_MARKERS)
            if not has_milestone:
                errors.append(
                    "7-1 실행 계획에 마일스톤(M1~Mx) 구조 없음 — "
                    "마일스톤 번호 또는 담당자 슬롯을 추가해야 합니다."
                )
    return errors


# ─── 메인 ──────────────────────────────────────────────────────────────────

def run_lint(filepath: str) -> int:
    path = Path(filepath)
    if not path.exists():
        print(f"[prd_lint] ERROR: 파일을 찾을 수 없습니다 — {filepath}")
        return 1

    content = path.read_text(encoding='utf-8')
    all_errors: list[str] = []

    # 검사 실행
    ac_errors = check_ac_structure(content)
    ex_errors, _ = check_ex_count(content)
    oq_errors = check_oq_format(content)
    forbidden_errors = check_forbidden_expressions(content)
    plan_errors = check_execution_plan(content)
    _, ex_log_warnings = check_ex_log_consistency(content)
    _, fr_ex_warnings = check_fr_ex_linkage(content)

    all_errors = ac_errors + ex_errors + oq_errors + forbidden_errors + plan_errors
    all_warnings = ex_log_warnings + fr_ex_warnings

    # 결과 출력
    print(f"\n[prd_lint] 검사 대상: {path.name}")
    print("─" * 60)

    categories = [
        ("AC 구조", ac_errors, []),
        ("EX 시나리오", ex_errors, []),
        ("OQ 형식", oq_errors, []),
        ("금지 표현", forbidden_errors, []),
        ("실행 계획", plan_errors, []),
        ("EX 로그 일관성", [], ex_log_warnings),
        ("FR-EX 연결", [], fr_ex_warnings),
    ]

    for category, errors, warnings in categories:
        if errors:
            status = f"❌ FAIL ({len(errors)}건)"
        elif warnings:
            status = f"⚠️  WARN ({len(warnings)}건)"
        else:
            status = "✅ PASS"
        print(f"  {category:<14} {status}")
        for e in errors:
            print(f"    → {e}")
        for w in warnings:
            print(f"    ⚠ {w}")

    print("─" * 60)
    if all_errors:
        print(f"[prd_lint] FAILED — {len(all_errors)}개 오류. 재작성 후 재실행하세요.\n")
        return 1
    else:
        if all_warnings:
            print(f"[prd_lint] PASSED (경고 {len(all_warnings)}건) — 오류 없음, 경고 확인 권장.\n")
        else:
            print("[prd_lint] PASSED — 모든 검사 통과.\n")
        return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 prd_lint.py <prd_file.md>")
        sys.exit(1)
    sys.exit(run_lint(sys.argv[1]))
