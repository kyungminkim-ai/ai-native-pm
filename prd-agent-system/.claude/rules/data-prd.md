# 데이터 PRD 분기 워크플로우

## 판별 기준

Rough Note에서 아래 키워드 2개 이상 감지 시 → `data-prd-writer` 에이전트 직접 호출.

| 판별 키워드 |
|-----------|
| 데이터 파이프라인, 데이터 연동, 데이터 수집 |
| API 연동, 배치 파이프라인, 로그 수집, 이벤트 수집 |
| 스키마, 테이블 명세, 데이터 카탈로그 |
| 개인정보 처리, 보존 정책, 데이터 생명주기 |
| SLA, 신선도, 가용성, 정합성 기준 |

---

## 데이터 PRD 워크플로우

```
Rough Note + Confluence 키워드
        │
        ▼
[Step 1: Context Loading]
   - Confluence 참조 시 confluence-skill로 관련 문서 수집
   - 스키마·API 스펙·기존 파이프라인 문서 우선 탐색
        │
        ▼
[Step 2: data-prd-writer 호출]
   - 에이전트: prd-agent-system/.claude/agents/data-prd-writer/AGENT.md
   - 6섹션(I~VI) 완성
   - 데이터 흐름 Mermaid 포함 → output/diagrams/{주제}_data_flow.mmd 저장
        │
        ▼
[Step 3: diagram-generator 에이전트]
   - 데이터 흐름 Mermaid → render.py 렌더링
   - 파이프라인 아키텍처 SVG → render_html.py 렌더링
   - 출력: output/diagrams/*.html
        │
        ▼
[Step 4: 파일 저장]
   - output/prd-data_{YYYYMMDD}_{주제}.md
        │
        ▼
[Step 5: Red Team 검증 (선택)]
   - 사용자가 명시적으로 요청한 경우에만 red-team-validator 호출
   - 데이터 PRD는 기본적으로 Red Team 생략 (스키마/거버넌스 문서 성격)
```

---

## 완료 출력 형식

```
✅ 데이터 PRD 작성 완료

📄 파일: output/prd-data_{날짜}_{주제}.md
   - PRD 유형: {유형}
   - 스키마 필드: {N}개
   - 미결 사항 (OQ): {N}건

🖼️ 다이어그램: output/diagrams/{주제}_data_flow.html
```
