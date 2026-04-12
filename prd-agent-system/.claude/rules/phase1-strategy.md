# Phase 1: 전략 및 지표 수립

## Step 1-A: Context Loading (Confluence)

Confluence 참조 키워드가 있을 경우 `confluence-skill`로 관련 문서를 검색한다.

```
Task: Confluence에서 "{Rough Note 핵심 키워드}"를 검색하고 관련 섹션을 요약해줘.
스킬: prd-agent-system/.claude/skills/confluence-skill/SKILL.md 참조
```

검색 결과는 Phase 1-B 지표 수립의 배경 자료로 활용.

---

## Step 1-B: Amplitude Baseline 조회 (조건부)

### 실행 조건

아래 중 하나에 해당하면 Amplitude MCP를 통해 Baseline 데이터를 수집한다.

| 트리거 | 판단 기준 |
|--------|---------|
| Rough Note에 수치 공백 | "현재 ~% 수준", "기존 대비" 등 Baseline 수치가 없을 때 |
| 사용자 관련 지표 필요 | CTR, CVR, 잔존율, 세션 수, 이벤트 수 등 |
| `--data amplitude` 플래그 | 사용자가 명시적으로 Amplitude 조회 요청 |
| Phase 0에서 수치 공백 확인 | 가정 검증 Q1~Q5 답변에 정량 데이터 없을 때 |

### 조회 절차

```
1. mcp__Amplitude__get_context
   → 사용자 조직 및 접근 가능한 projectId 확인

2. mcp__Amplitude__get_project_context(projectId)
   → 프로젝트 설정 및 주요 이벤트 목록 확인

3. mcp__Amplitude__get_events(projectId)
   → Rough Note 키워드로 관련 이벤트 탐색
   → 예: "push", "click", "purchase", "session" 등

4. mcp__Amplitude__query_chart(projectId, chartId)
   또는
   mcp__Amplitude__search(projectId, query)
   → Baseline 수치 추출 (최근 30일 또는 사용자 지정 기간)

5. 수집된 수치를 PRD (2) 목표 / Business Impact → Metrics 테이블 Baseline 컬럼에 삽입
```

### 조회 실패 처리

| 상황 | 처리 |
|------|------|
| 이벤트 없음 | 에이전트 직접 추정 없이 "{OQ-B01 — Baseline 확인 필요}"로 표기 |
| 조회 오류 | 오류 사유 기록 후 수동 입력 요청 |
| 시즌성 의심 | 단월 스냅샷임을 명시, 시계열 추이 추가 조회 권장 주석 삽입 |

---

## Step 1-C: Metric Proposal

`references/metric_guide.md`를 기준으로 아래 3계층 지표를 제안한다.

- **North Star Metric** (1개): 비즈니스 성장과 사용자 가치를 동시에 반영
- **Primary Metrics** (2~3개): North Star 달성을 위한 중간 목표
- **Guardrail Metrics** (1~2개): 개선 과정에서 악화되면 안 되는 지표

Baseline은 Step 1-B 조회 결과 또는 사용자 제공 수치를 사용.
제안 시 반드시 "지표 → 비즈니스 목표" 간 논리적 연결을 설명.

---

## 에스컬레이션 조건

지표가 모호하거나 비즈니스 목표가 불분명하면 작업 중단 후 재확인:

> "지표를 확정하기 어렵습니다. 이 기능을 통해 기대하는 핵심 결과(KPI)는 무엇인가요?
> 예: MAU 증가 / 구매 전환율 개선 / 이탈률 감소 / 특정 기능 사용률 목표"
