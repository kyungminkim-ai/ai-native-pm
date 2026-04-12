# Cross-team Artifact Registry 가이드

> 마지막 업데이트: 2026-04-12

## 개요

`output/_registry.json`은 pm-studio 내 모든 팀이 공유하는 **산출물 인덱스**다.
각 팀(스킬/에이전트)이 산출물을 생성할 때 이 레지스트리에 등록해 두면,
다른 팀이 "최신 PRD가 어디 있지?" "이번 주 Flash는 뭐야?" 를 물어볼 필요 없이
레지스트리를 조회해서 즉시 연결할 수 있다.

```
PRD 작성 완료 → registry에 등록
                    ↓
Red Team이 "최신 PRD" 조회 → 자동 연결
                    ↓
PGM이 "이번 주 PRD" 조회 → 자동 연결
```

---

## 등록 타입 목록

| 타입 | 설명 | 등록 팀 |
|------|------|--------|
| `prd` | 기능 PRD 초안 | 기획팀 (/prd) |
| `prd-data` | 데이터 파이프라인 PRD | 기획팀 (/prd) |
| `prd-v2` | Generator-Verifier 1회차 보강본 | 기획팀 (/prd) |
| `prd-v3` | Generator-Verifier 2회차 보강본 | 기획팀 (/prd) |
| `redteam` | Red Team 질문지 | 기획팀 (/red) |
| `two-pager` | 2-Pager 경영진 보고 문서 | 기획팀 (/two-pager) |
| `discovery` | Discovery 분석 보고서 | 디스커버리팀 (/discovery) |
| `flash` | Weekly Flash Report | PGM팀 (/pgm) |
| `meeting` | 회의록 | 미팅팀 (/meeting) |
| `analysis` | 데이터 분석 결과 | 분석팀 (/analyst) |
| `design-spec` | Figma 화면 설계서 | 디자인팀 (/figma) |

---

## 사용법

### 등록 (산출물 생성 직후)

```bash
python3 scripts/registry.py register \
  --type prd \
  --path prd-agent-system/output/prd_20260412_campaign_meta_engine.md \
  --topic "Campaign Meta Engine Phase 1"
```

### 조회 (다른 팀에서 참조할 때)

```bash
# 최신 PRD 경로만 출력
python3 scripts/registry.py get --type prd

# 전체 목록 확인
python3 scripts/registry.py list

# 특정 타입만 확인
python3 scripts/registry.py list --type flash
```

### 제거

```bash
python3 scripts/registry.py clear --type prd
```

---

## 각 팀의 등록 의무

| 팀 / 스킬 | 등록 타입 | 등록 시점 |
|----------|---------|---------|
| `/prd` | `prd` | Phase 3 완료 직후 |
| `/prd` | `prd-v2` | Phase 5 (1회차 보강) 완료 직후 |
| `/prd` | `prd-v3` | Phase 5 (2회차 보강) 완료 직후 |
| `/red` (단독 실행) | `redteam` | Red Team 파일 저장 직후 |
| `/two-pager` | `two-pager` | 최종본 저장 직후 |
| `/discovery` | `discovery` | 보고서 저장 직후 |
| `/pgm` | `flash` | Flash 파일 저장 직후 |
| `/meeting` | `meeting` | 회의록 저장 직후 |
| `/analyst` | `analysis` | 분석 보고서 저장 직후 |
| `/figma --spec` | `design-spec` | 설계서 저장 직후 |

---

## 레지스트리 구조 (output/_registry.json)

```json
{
  "prd": {
    "path": "prd-agent-system/output/prd_20260412_campaign_meta_engine.md",
    "topic": "Campaign Meta Engine Phase 1",
    "registered_at": "2026-04-12T13:30:00",
    "history": [
      {
        "path": "prd-agent-system/output/prd_20260410_audience_api_v2.md",
        "topic": "Audience API Console",
        "registered_at": "2026-04-10T10:00:00"
      }
    ]
  },
  "flash": {
    "path": "pgm-agent-system/output/flash_20260412.md",
    "topic": "",
    "registered_at": "2026-04-12T09:00:00",
    "history": []
  }
}
```

- 동일 타입이 재등록되면 이전 항목은 `history`에 보관 (최대 3개)
- `path`는 pm-studio 루트 기준 상대경로

---

## 비서실장의 레지스트리 활용

비서실장(`/staff`)은 아래 상황에서 레지스트리를 먼저 조회한다:

| 상황 | 조회 타입 |
|------|---------|
| "/red 실행해줘" (PRD 파일 미지정) | `prd-v2` → 없으면 `prd` |
| "이번 주 Flash 보고서 검토해줘" | `flash` |
| "PRD 기반으로 QA 테스트케이스 만들어줘" | `prd-v2` → 없으면 `prd` |
| "회의록 내용을 Jira 코멘트로 올려줘" | `meeting` |
| "Discovery 결과를 PRD에 반영해줘" | `discovery`, `prd` |

---

## 스크립트 위치

`scripts/registry.py` — pm-studio 루트 레벨
