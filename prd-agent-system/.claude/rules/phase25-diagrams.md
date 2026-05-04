# Phase 2.5: 다이어그램 시각화 (생략 불가)

`ux-logic-analyst` 완료 직후 `diagram-generator` **에이전트**를 호출하여 모든 다이어그램을 HTML로 렌더링한다.

에이전트 스펙: `prd-agent-system/.claude/agents/diagram-generator/AGENT.md`

---

## 호출 형식

```
Task: 아래 다이어그램 요청을 처리해줘.
에이전트: prd-agent-system/.claude/agents/diagram-generator/AGENT.md

[Mermaid 플로우]
- ux-logic-analyst가 생성한 Mermaid 코드 블록 전체 (첨부)

[추가 SVG 다이어그램 — 필요 시]
- 시스템 아키텍처: {컴포넌트/레이어 설명}
- 타임라인/로드맵: {단계별 설명}
- 비교 매트릭스: {옵션/기준 설명}
- IA/사이트맵: {화면 트리 설명}
```

---

## 다이어그램 유형 판별

| 유형 | 렌더러 | 파일 |
|------|-------|------|
| 사용자 플로우, 상태, 시퀀스, 여정 | `render.py` | `{주제}_{타입}_flow.mmd` → `.html` |
| 시스템 아키텍처, 매트릭스, 타임라인, IA | `render_html.py` | `{주제}_{타입}.svg` → `.html` |

---

## EX 시나리오 → Mermaid 노드 매핑 (필수)

edge-case-analyst(Phase 2c)가 생성한 EX-NNN 예외 시나리오는 **예외/에러 플로우 차트의 노드와 명시적으로 연결**되어야 한다.
diagram-generator 호출 시 아래 매핑 테이블을 함께 전달한다:

```
[EX → 노드 매핑]
| EX ID | 관점 | 에러 플로우 차트 내 노드 ID | 노드 설명 |
|-------|------|--------------------------|---------|
| EX-001 | INPUT | ErrorNode_Input | {에러 메시지 노드 설명} |
| EX-002 | AUTH | ErrorNode_Auth | {인증 오류 노드 설명} |
| EX-003 | SYS | ErrorNode_Timeout | {타임아웃 노드 설명} |
| EX-004 | BIZ | ErrorNode_Biz | {비즈니스 예외 노드 설명} |
| EX-005 | RACE | ErrorNode_Race | {동시성 오류 노드 설명} |
```

**매핑 검증 기준:**
- 5가지 관점(INPUT/AUTH/SYS/BIZ/RACE)이 각각 에러 플로우 차트에 노드로 표현되어야 함
- 매핑 누락 시: 해당 EX 시나리오를 에러 플로우 차트에 추가하거나 Open Questions로 이전

---

## 렌더링 검증 기준

| 검증 항목 | 기준 |
|---------|-----|
| Mermaid .html 수 | .mmd 파일 수와 동일 |
| SVG .html 수 | .svg 파일 수와 동일 |
| EX → 노드 매핑 | EX-NNN 5가지 관점이 에러 플로우 노드에 각 1개 이상 연결 |
| 렌더링 실패 | 해당 다이어그램을 Open Questions에 추가, 나머지는 계속 진행 |
