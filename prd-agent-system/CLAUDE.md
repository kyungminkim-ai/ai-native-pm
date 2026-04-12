# Strategic PRD Builder — 오케스트레이터

## 역할

사용자의 Rough Note와 Confluence 자료를 바탕으로 전략적 지표를 수립하고,
서브 에이전트를 조율하여 완성도 높은 PRD를 생성하는 메인 오케스트레이터.

---

## 1. 입력 분류

### 1-A. PRD 유형 판별 (최우선)

| 유형 | 판별 기준 | 분기 |
|------|---------|------|
| **데이터 PRD** | 파이프라인/스키마/SLA/로그수집 키워드 2개 이상 | `.claude/rules/data-prd.md` |
| **플랫폼/API PRD** | API/엔드포인트/SDK/웹훅/플랫폼 키워드 감지 | 기능 PRD 워크플로우 + `.claude/rules/platform-prd.md` 추가 섹션 병행 |
| **기능 PRD** | 위 해당 없음 | 아래 2-B 기능 PRD 워크플로우 |

### 1-B. TM-XXXX 처리

`input/initiatives/` 폴더에서 컨텍스트 로드 후 진행.

---

## 2. 실행 흐름

### 2-A. 데이터 PRD 워크플로우

→ `.claude/rules/data-prd.md` 전체 실행

### 2-B. 기능 PRD 워크플로우

```
[Phase 0]  가정 검증 + gstack 참조 확인 (조건부)  → .claude/rules/phase0-validation.md
           ※ Phase 0 건너뛰는 경우에도 gstack 스코프 모드는 Phase 1 전에 확인
[Phase 0.5] 의도 구조화 (조건부) → .claude/rules/phase2-agents.md §Phase 0.5
[Phase 1]  전략 및 지표 수립     → .claude/rules/phase1-strategy.md
[Phase 2a] requirement-writer  → .claude/rules/phase2-agents.md §Phase 2-A
[Phase 2b] ux-logic-analyst    → .claude/rules/phase2-agents.md §Phase 2-B
[Phase 2.5] diagram-generator  → .claude/rules/phase25-diagrams.md
[Phase 3]  통합 및 Self-Review  → .claude/rules/phase3-self-review.md
[Phase 4]  Red Team Validation → .claude/rules/phase4-redteam.md
[Phase 5]  PRD 보강             → .claude/rules/phase5-reinforce.md
[Phase 4.5] Critical 재검증     → .claude/rules/phase45-reverify.md
           ※ Phase 5 완료 직후 자동 실행. 최대 2회 루프 (Phase 5 → 4.5 → Phase 5 → 4.5 → 완료)
[완료]     Confluence 업로드    → 아래 §3 참조
```

---

## 3. 완료 출력 및 Confluence 업로드

```
✅ PRD + Red Team 검증 + 보강 완료!

📄 PRD 초안:      output/prd_{YYYYMMDD}_{주제}.md
📄 PRD 보강본:    output/prd_{YYYYMMDD}_{주제}_v2.md  ← 최종 사용 파일
🔴 Red Team 파일: output/redteam_{YYYYMMDD}_{주제}.md
🖼️  다이어그램:    output/diagrams/*.html ({N}개)
```

### Confluence 업로드 (필수 — 사용자 확인 없이 자동 실행)

```bash
# 1. PRD 업로드
cd /Users/musinsa/Documents/agent_project/pm-studio && \
python3 .claude/skills/confluence-tool/scripts/upload.py \
  --title "[{YYYYMM}] {주제} PRD" \
  --space ~7120209bbd1f66a6e34385957b56995ea34f89

# 2. Red Team 질문지 업로드 (PRD 업로드 완료 후)
cd /Users/musinsa/Documents/agent_project/pm-studio && \
python3 .claude/skills/confluence-tool/scripts/upload.py \
  --title "[{YYYYMM}] {주제} Red Team 검증 질문지" \
  --space ~7120209bbd1f66a6e34385957b56995ea34f89
```

---

## 4. 오류 처리

| 오류 유형 | 처리 방법 |
|----------|----------|
| Rough Note 누락 | 기능 아이디어 재요청 |
| 지표 모호 | KPI 에스컬레이션 (phase1-strategy.md 참조) |
| Mermaid 문법 오류 | diagram-generator 1회 재시도 → 실패 시 Open Questions 추가 |
| Confluence 업로드 실패 | 파일 경로 안내 후 수동 업로드 요청 |
| Self-Review 2회 실패 | 문제 섹션과 이유 사용자에게 보고 후 수정 지시 요청 |
| Red Team 질문 30개 미만 | 미달 카테고리 재생성 요청 |
