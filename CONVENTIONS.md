# PM Studio — 공통 규약

> 모든 에이전트·스킬이 준수하는 공통 규칙.
> 각 시스템의 CLAUDE.md에서 이 파일을 참조하여 중복 정의를 제거한다.
> 마지막 업데이트: 2026-04-12

---

## 1. 파일 명명 규칙

| 산출물 유형 | 패턴 |
|------------|------|
| Flash Report | `pgm-agent-system/output/flash_{YYYYMMDD}.md` |
| 회의록 초안 | `pgm-agent-system/output/meeting_minutes_{YYYYMMDD}.md` |
| Slack 요약 | `pgm-agent-system/output/slack_summary_{YYYYMMDD}.txt` |
| Weekly Draft | `pgm-agent-system/output/weekly_draft_{YYYYMMDD}.json` |
| Jira Raw | `pgm-agent-system/output/jira_raw_{YYYYMMDD}.json` |
| Flash 분석 결과 | `pgm-agent-system/output/flash_analysed_{YYYYMMDD}.json` |
| 회의록 분석 결과 | `pgm-agent-system/output/minutes_analysed_{YYYYMMDD}.json` |
| 이전 주 Flash 분석 | `pgm-agent-system/output/analysed_report_prev.json` |
| 파이프라인 상태 | `pgm-agent-system/output/.pipeline_state.json` |
| 아티팩트 레지스트리 | `pgm-agent-system/output/_artifacts.json` |
| PRD | `prd-agent-system/output/prd_{YYYYMMDD}_{주제}.md` |
| PRD 보강본 (1회차) | `prd-agent-system/output/prd_{YYYYMMDD}_{주제}_v2.md` |
| PRD 보강본 (2회차) | `prd-agent-system/output/prd_{YYYYMMDD}_{주제}_v3.md` |
| Red Team | `prd-agent-system/output/redteam_{YYYYMMDD}_{주제}.md` |
| GTM | `gtm-agent-system/output/GTM_Brief_{YYYYMMDD}_{주제}.md` |
| 보고서 검토 | `report-agent-system/output/report_review_{YYYYMMDD}_{주제}.md` |
| 과제 검토 | `pgm-agent-system/output/ticket_review_{YYYYMMDD}.md` |
| 작업 로그 | `output/work_log_{YYYYMMDD}.md` |

---

## 2. 반드시 사전 컨펌이 필요한 작업

되돌리기 어려운 작업은 반드시 미리보기를 보여주고 사용자 승인을 받는다.

| 작업 | 컨펌 방법 |
|------|----------|
| Jira 티켓 생성 | 생성 예정 목록 표로 정리 후 "진행할까요?" |
| Confluence 페이지 업로드 | 제목·Space·내용 미리보기 확인 후 "업로드할까요?" |
| 이메일 발송 | 제목·수신자·본문 미리보기 확인 후 "발송할까요?" |
| Jira 코멘트 게시 | 마크다운 미리보기 → 승인 후 게시 |

---

## 3. API 오류 처리

| 오류 | 처리 방법 |
|------|----------|
| Confluence/Jira API 401 | "CONFLUENCE_API_TOKEN을 확인해주세요" 후 중단 |
| Gmail 인증 오류 | "GMAIL_APP_PASSWORD 환경변수를 확인하세요" 후 중단 |
| Google Docs API 실패 | 해당 단계 스킵, 로컬 MD 파일 경로 안내 후 계속 진행 |
| Slack Webhook 실패 | 터미널에 요약 출력 + 파일 경로 안내 |
| 검색 결과 없음 | 타 Space 검색 확장 제안 (`--space ALL`) |
| 팀 산출물 실패 | 해당 팀 2회 재시도, 이후 사용자에게 보고 |
| Jira 티켓 0건 | "이번 주 처리된 티켓이 없습니다. 날짜 범위를 확인할까요?" |

---

## 4. 출력 문체 규칙

- **명사형 종결**: 모든 보고서·메일 서술은 `~완료`, `~예정`, `~중`, `~함`으로 종결
  - ✅ "캠페인 메타 엔진 배포 완료" / ❌ "배포를 완료했습니다"
- **핵심 수치 볼드**: `**숫자**` 형식 필수 (예: `**5건 완료**`, `**18 SP**`)
- **기술 용어 병기**: API, 배치, 파이프라인 등은 괄호 병기 (예: `API 연동(외부 데이터 연결)`)
- **비즈니스 언어**: 아젠다·보고서 제목은 기술 용어 대신 비즈니스 언어로 재작성

---

## 5. 아티팩트 버스 (Artifact Bus)

매 PGM 실행 후 `pgm-agent-system/output/_artifacts.json`에 산출물 경로를 기록한다.
다른 에이전트·스킬(`/report`, `/mail` 등)은 이 파일을 읽어 이번 주 산출물을 참조한다.

```json
{
  "date": "YYYYMMDD",
  "week": 10,
  "flash_md": "pgm-agent-system/output/flash_{YYYYMMDD}.md",
  "meeting_minutes_md": "pgm-agent-system/output/meeting_minutes_{YYYYMMDD}.md",
  "weekly_draft_json": "pgm-agent-system/output/weekly_draft_{YYYYMMDD}.json",
  "jira_raw_json": "pgm-agent-system/output/jira_raw_{YYYYMMDD}.json",
  "analysed_report_json": "pgm-agent-system/output/analysed_report.json",
  "google_docs_flash_url": null,
  "google_docs_minutes_url": null,
  "gmail_draft_id": null,
  "weekly_result_json": null
}
```

---

## 6. 체크포인트 시스템 (PGM 파이프라인 전용)

`pgm-agent-system/output/.pipeline_state.json`에 각 단계 완료 여부를 기록.
재실행 시 완료된 단계는 스킵하고 실패한 단계부터 재개한다.

```json
{
  "date": "YYYYMMDD",
  "mode": "full|flash|weekly",
  "jira_key": "MATCH",
  "confluence_url": "https://...",
  "steps": {
    "jira_parse":         { "status": "done|pending|failed", "artifact": "output/jira_raw_YYYYMMDD.json" },
    "confluence_fetch":   { "status": "done|pending|failed", "artifact": "output/confluence_YYYYMMDD.md" },
    "analyst":            { "status": "done|pending|failed", "artifact": "output/analysed_report.json" },
    "publisher":          { "status": "done|pending|failed", "artifact": "output/flash_YYYYMMDD.md" },
    "minutes_generator":  { "status": "done|pending|failed", "artifact": "output/meeting_minutes_YYYYMMDD.md" },
    "weekly_poster":      { "status": "done|pending|failed", "artifact": "output/weekly_result_YYYYMMDD.json" }
  }
}
```

**재실행 규칙**: 오늘 날짜의 `.pipeline_state.json`이 존재하면 → `"done"` 단계 스킵 → `"failed"` 또는 `"pending"` 단계부터 재개.

---

## 7. Next Actions 힌트 (경량 Message Bus)

스킬 실행 완료 후 **관련 후속 액션을 선택지로 제시**한다.
사용자가 직접 "다음엔 뭐 해?"를 물을 필요 없이 자연스러운 워크플로우 연결을 유도한다.

### 표준 형식

```
💡 다음 단계 제안:
  [A] {액션명} — {한 줄 이유}
  [B] {액션명} — {한 줄 이유}
  [C] 여기서 종료

→ A/B/C 중 선택하거나, 다른 작업을 말씀해주세요.
```

### 스킬별 표준 next_actions

| 완료 스킬 | A (권장) | B (대안) |
|----------|---------|---------|
| `/prd` 완료 → `_v2.md` 생성 | Red Team 재검증 결과 확인 (자동 진행) | Confluence 업로드 |
| `/two-pager` 완료 | PRD 작성 시작 (`/prd`) | Red Team 검토 (`/red`) |
| `/red` 완료 (단독 실행) | PRD 보강 반영 | QA 테스트케이스 생성 (`qa-agent`) |
| `/discovery` 완료 | PRD 작성 (`/prd`) | 전략 논의 (`/strategy`) |
| `/pgm` Flash 완료 | C레벨 보고서 검토 (`/report`) | 회의록 작성 (`/meeting`) |
| `/analyst` 완료 | 분석 결과 PRD에 반영 | Confluence 저장 |
| `/meeting` 완료 | Jira Initiative 코멘트 반영 (`/pgm --weekly`) | 참석자 Slack 공유 (`/slack --send`) |

### 적용 규칙

- 자동 실행이 확정된 단계(예: Phase 4.5 재검증)는 힌트 없이 자동 진행
- 되돌리기 어려운 작업(Confluence 업로드, Jira 게시)은 힌트에 포함하되 선택을 받음
- 선택지는 최대 3개 (A/B/C)로 제한

---

## 8. Health Status 기준

| 상태 | 기호 | 판단 기준 |
|------|------|----------|
| 정상 진행 | 🟢 Green | 계획 일정 내 진행 중, 블로커 없음 |
| 주의 필요 | 🟡 Yellow | 일정 지연 위험 또는 해결 중인 이슈 존재 |
| 긴급 대응 | 🔴 Red | 블로커로 일정 영향 확실, 즉각 의사결정 필요 |

모든 Flash Report 최상단에 Health Status를 1줄로 표기한다:
```
| 전체 상태 | 🟢 정상 진행 | 계획 대비 차질 없음 |
```
