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

## 렌더링 검증 기준

| 검증 항목 | 기준 |
|---------|-----|
| Mermaid .html 수 | .mmd 파일 수와 동일 |
| SVG .html 수 | .svg 파일 수와 동일 |
| 렌더링 실패 | 해당 다이어그램을 Open Questions에 추가, 나머지는 계속 진행 |
