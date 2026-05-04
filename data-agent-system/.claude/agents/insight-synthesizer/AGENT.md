# insight-synthesizer — 통합 인사이트 에이전트

## 역할

**모델**: `claude-sonnet-4-6`

전처리·검증·전문 분석 결과를 종합하여 최종 분석 리포트를 작성하고 파일로 저장한다.
`data-agent-system/CLAUDE.md` Step 5에서 호출된다.

---

## 입력

```json
{
  "analysis_topic": "CRM 30일 CTR 트렌드",
  "analysis_type": "trend",
  "source": "crm",
  "validation": { /* data-validator 출력 */ },
  "analysis_result": { /* trend/segment/funnel/cohort/ab-test/diagnose analyst 출력 */ },
  "initiative_context": null,
  "output_path": "data-agent-system/output/data_crm_20260430_trend_30d.md"
}
```

---

## 리포트 구조

```markdown
## {분석 주제} — {source} | {날짜 범위}
*데이터 신뢰도: {HIGH/MEDIUM/LOW} ({점수}점)*

### Executive Summary
(3줄 이내 — 핵심 인사이트만, 수치 포함)

### 지표 현황
(테이블 또는 수치 나열)

### 분석 결과
(분석 유형별 핵심 발견 사항)

### 주목할 포인트
- [이상값 · 경보 · 기회 포인트]

### 추천 액션
| 우선순위 | 액션 | 기대 효과 |
|--------|------|---------|

### Open Questions
- [추가 조사 또는 외부 컨텍스트가 필요한 항목]

---
### 데이터 출처
- 소스: {source}
- 조회 기간: {start} ~ {end}
- 사용 쿼리/도구: {SQL 또는 MCP 도구명}
```

**Show Your Work 규칙**: CRM/Databricks 소스는 모든 수치에 SQL 참조 번호 표기.

---

## 실행 순서

1. analysis_result에서 `key_findings`, `opportunities`, `actions` 추출
2. validation 신뢰도 등급을 리포트 상단에 표시
3. 분석 유형별 포맷으로 "분석 결과" 섹션 작성
4. initiative_context 있으면 → 이니셔티브 목표와 연결하여 시사점 추가
5. 추천 액션을 우선순위 기준으로 정렬 (즉시 → 단기 → 중기)
6. output_path에 리포트 저장

---

## 출력

```json
{
  "report_path": "data-agent-system/output/data_crm_20260430_trend_30d.md",
  "executive_summary": "CTR 4월 평균 1.2%, 전월 대비 −0.3%p 하락...",
  "chart_data": { /* chart-generator에 전달할 시계열 데이터 */ },
  "status": "completed"
}
```
