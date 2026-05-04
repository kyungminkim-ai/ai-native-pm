# two-pager-agent-system

경영진 의사결정용 2-Pager 문서를 작성하고 검토하는 멀티에이전트 시스템.

---

## 무엇을 만드는가

**2-Pager**는 경영진이 10분 안에 읽고 의사결정을 내릴 수 있도록 설계된 산문형 기획 문서다.  
PowerPoint 슬라이드나 불릿 목록이 아니라, 완성된 문장으로 쓰인 내러티브 형식을 따른다.

산출물 파일 위치: `output/two_pager_{YYYYMMDD}_{주제}.md`

**포함 섹션:**
1. BLUF — 한 문단으로 끝나는 핵심 제안과 결정 요청
2. 배경 & 문제 정의 — 왜 지금인가, 어떤 문제인가
3. 제안 솔루션 — 무엇을, 왜 이 방법으로
4. 대안 검토 — 진지하게 검토된 Option A/B/C
5. 리스크 & 완화 방안
6. 성공 지표 — 현재값 → 목표값 (변화량, 기간) 형식
7. 요청 사항 — 독자가 해야 할 구체적 행동

선택 섹션:
- Lessons Learned (이전 시도 결과가 있는 경우)
- Appendix 참조 목록 (대용량 데이터·분석 자료)

---

## 에이전트 구조

```
[SKILL.md — 오케스트레이터]
    │
    ├─ Phase 0.5: discovery-validator
    │   Discovery 충분성 5개 영역 검증
    │   → PROCEED / PROCEED_WITH_ASSUMED / RECOMMEND_DISCOVERY
    │
    ├─ Phase 4: two-pager-writer
    │   초안 작성 + 독자 질문 목록 생성
    │
    ├─ Phase 5a: audience-simulator
    │   독자 입장 Silent Read 시뮬레이션
    │   범용 질문 10개 + 주제 특화 질문 5~10개 → 커버리지 점수 산출
    │
    └─ Phase 5b: two-pager-reviewer
        초안 검토 + 직접 재작성 + 코멘트 삽입
        audience-simulator 커버리지 결과 통합 반영
```

**에이전트 파일 위치:**
```
.claude/
├── discovery-validator/AGENT.md
├── two-pager-writer/AGENT.md
├── audience-simulator/AGENT.md
└── two-pager-reviewer/AGENT.md
```

---

## 이 시스템이 고려한 것들

### 1. Discovery가 먼저다 (Marty Cagan 원칙)

기획 문서는 Product Discovery *이후*에 작성되어야 한다.  
Discovery *대신* 작성된 문서는 검증되지 않은 가정으로 가득 차 있으면서도, 일단 문서가 존재하면 아무도 가정을 의심하지 않는 "문서 중력(Document Gravity)" 현상을 만든다.

**discovery-validator**는 작성 전에 5개 영역(Value, Usability, Feasibility, Viability, Timing)의 Discovery 충분성을 판단한다. Discovery가 부족하면 `/discovery` 먼저 진행을 권유하고, 부분적으로 부족하면 `[ASSUMED]` 태그를 달아 투명하게 표시한 채 진행한다.

### 2. 문서는 자립해야 한다 (Amazon 6-pager 원칙)

이 주제를 전혀 모르는 독자도 문서 하나만으로 이해할 수 있어야 한다.  
Amazon에서는 회의 전 20~25분을 묵독에 할당하며, 그 자리에서 처음 보는 사람도 전체 맥락을 파악할 수 있어야 회의가 의미 있다고 본다.

**Stand-alone 테스트**가 writer와 reviewer 모두에 내장되어 있으며, 전문 용어 풀어쓰기, "왜 지금인가" 타이밍 근거, 맥락 없는 지시어 제거가 체크 항목에 포함된다.

### 3. 독자 질문을 미리 시뮬레이션한다 (Amazon Silent Read 원칙)

실제 보고 회의에서 경영진은 문서를 읽으면서 끊임없이 질문한다.  
**audience-simulator**는 그 질문을 미리 생성하고, 문서가 각 질문에 답하는지 커버리지 점수로 측정한다.  
커버리지가 낮은 질문은 reviewer에게 전달되어 `> [!COMMENT]` 코멘트로 삽입된다.

### 4. 지적이 아닌 재작성 (Reviewer 철학)

리뷰어가 "이 부분이 약하다"고만 지적하면 작성자는 어떻게 고쳐야 할지 모른다.  
**two-pager-reviewer**는 약한 부분을 직접 재작성하고, 재작성 후에도 판단이 필요한 부분만 코멘트를 남긴다.

### 5. 숫자는 맥락과 함께 (Amazon 데이터 원칙)

"MAU 200만"이 아니라 "MAU 200만, 전년 대비 +15%, 경쟁사 대비 구매전환율 절반 수준"이어야 한다.  
성공 지표(Goals)는 **현재값 → 목표값 (변화량, 기간)** 형식을 강제한다.

### 6. 시제 분리로 독자 혼동 방지

- **현재 상태(State of Business)**: 현재형만 사용 — 가장 최신 스냅샷
- **과거 교훈(Lessons Learned)**: 과거형만 사용 — 해석 없이 데이터만
- **제안 방향**: 미래형/조건형 — 아직 결정되지 않은 것임을 명시

reviewer가 시제 일관성을 자동으로 검토하여 혼용 시 직접 수정한다.

### 7. Why before What (Google Chrome 런치 원칙)

기능이나 솔루션 설명 전에 "왜 이것이 필요한가"를 먼저 서술한다.  
섹션 2(배경 & 문제 정의)의 첫 문단은 반드시 타이밍 근거 — 시장 변화, 내부 이벤트, 경쟁 상황 — 로 시작해야 한다.

### 8. 대안을 진지하게 다룬다

형식적으로 Option B, C를 나열하는 것이 아니라, 각 대안이 1단락 이상 장단점을 포함해 서술되어야 한다.  
"Document Gravity" 함정을 피하기 위해, 이 문서는 경영진에게 선택지를 제시하는 것이지 요구사항을 지시하는 것이 아님을 reviewer가 감시한다.

---

## 사용법

```
/two-pager [주제 또는 아이디어]
/two-pager [TM-XXXX]
/two-pager [주제] --refs [Confluence URL]
/two-pager [주제] --file [자료 파일 경로]
```

전체 워크플로우는 자동으로 실행되며, 작성자가 개입할 지점은:
1. Phase 1 — 질문지 답변 제출
2. Phase 3 — 컨텍스트 요약 확인 후 "작성해줘"
3. 완료 후 — 코멘트([!COMMENT]) 검토 및 최종 수정

---

## 참고 자료

이 시스템은 아래 세 가지 원천에서 설계 원칙을 추출했다:

| 원칙 | 출처 |
|------|------|
| Discovery-first, Document Gravity | Marty Cagan — "Discovery vs. Documentation" |
| Narrative 형식, 자립 문서, 시제 분리, Appendix, Goals 포맷, Silent Read | Amazon 6-pager 방법론 |
| Why before What, Simple surface + Sophisticated core | Google Chrome 런치 스피치 (Sundar Pichai, 2008) |
