# 소재 분류 정책 — 성별 타겟 & 카테고리 코드

> 대상: 시스템 운영 담당자 / 개발자
> 마지막 수정: 2026-04-25
> 구현 위치: `scripts/rules.py` — `classify_target()`, `get_category_id()`

---

## 1. 성별 타겟 분류 (`target` 컬럼)

발송 대상 성별(`여성` / `남성` / `전체`)을 아래 우선순위 순서로 결정합니다.

### 판단 순서

| 우선순위 | 조건 | 결과 |
|----------|------|------|
| 1순위 | `register_team_name`에 **"여성"** 포함 | `여성` |
| 1순위 | `register_team_name`에 **"남성"** 포함 | `남성` |
| 2순위 | `brand_list.csv`의 `gender` 컬럼이 **"여성"** 또는 **"남성"** | 해당 값 |
| 3순위 | 위 조건 모두 미해당 | `전체` |

### 팀명 키워드 예시

| 팀명 패턴 | 결과 |
|-----------|------|
| `여성패션팀`, `여성뷰티팀` | `여성` |
| `남성패션팀`, `남성스트릿팀` | `남성` |
| `전사캠페인`, `카테고리마케팅`, `아웃도어팀` | `전체` (brand_list 참조) |

### 업데이트 방법

- 팀명 키워드 추가/수정: `scripts/rules.py` > `classify_target()` 함수
- 브랜드별 성별 고정: `input/brand_list.csv` > `gender` 컬럼 직접 편집

---

## 2. 카테고리 코드 분류 (`category_id` 컬럼)

카테고리 ID는 **팀명 키워드 매핑(rule-based)** + **LLM 유추(AI)** 두 단계로 결정됩니다.

### 2-1. Rule-based: 팀명 → 카테고리 코드 (1차)

`register_team_name`에 아래 키워드가 포함되면 해당 코드로 매핑합니다.

| 팀명 키워드 | 카테고리 코드 | 카테고리명 |
|-------------|--------------|-----------|
| 아웃도어 | 017 | 아웃도어 |
| 스포츠 | 017 | 아웃도어 |
| 애슬레저 | 017 | 아웃도어 |
| 풋웨어 | 103 | 신발 |
| 무신사풋웨어 | 103 | 신발 |
| 뷰티, 뷰티1, 뷰티2 | 104 | 뷰티 |
| 여성패션 | 100 | 여성의류 |
| 남성패션 | 001 | 남성의류 |
| 유니섹스패션 | 001 | 남성의류 |
| 키즈 | 106 | 키즈 |
| 라이프 | 102 | 라이프스타일 |
| 글로벌패션 | 001 | 남성의류 |

> 키워드가 매핑되지 않으면 `category_id = ""` (공란)

### 2-2. LLM 유추: 소재 내용 기반 카테고리 코드 (2차, API 키 필요)

`category_selector.csv`의 전체 카테고리 목록을 참조하여 Claude API가 소재 내용(이벤트명, 프로모션 내용, 제목, 랜딩 URL)을 보고 관련 카테고리 코드 최대 3개를 추가로 유추합니다.

**LLM 유추 특별 규칙:**
| 소재 유형 | 코드 |
|-----------|------|
| K-Pop 굿즈·앨범 | 111 |
| E-Sports·스포츠구단 | 112 |
| 캐릭터 굿즈 (디즈니/마블 등) | 113 |
| 만화·애니메이션 | 114 |
| 일반 패션 단순 할인 | 해당 의류/신발 카테고리만 |

### 최종 병합 로직

```
최종 category_id = rule-based 코드 + LLM 유추 코드 (쉼표 구분, 중복 제거)
```

### 업데이트 방법

- **팀명-카테고리 매핑 변경**: `scripts/rules.py` > `get_category_id()` > `TEAM_TO_CATEGORY` 딕셔너리 직접 편집
- **LLM 유추 규칙 변경**: `scripts/prompts.py` > `build_category_infer_prompt()` 내 선택 규칙 섹션 수정
- **카테고리 목록 변경**: `input/category_selector.csv` 업데이트

---

## 3. AI 로직이 적용되는 전체 분류 영역 요약

| 분류 항목 | 방식 | 수정 위치 |
|-----------|------|----------|
| 성별 타겟 (1순위) | Rule-based 팀명 키워드 | `rules.py::classify_target()` |
| 성별 타겟 (2순위) | brand_list.csv 조회 | `input/brand_list.csv` |
| 카테고리 코드 (1차) | Rule-based 팀명 매핑 | `rules.py::get_category_id()` |
| 카테고리 코드 (2차) | LLM (Claude API) | `prompts.py::build_category_infer_prompt()` |
| 발송 본문 선택 | Rule-based 키워드 (%, 한정, 마감 등) | `rules.py::select_contents()` |
| 메시지 생성 (제목/V1/V2/V3) | LLM (Claude API) | `prompts.py`, `llm_client.py` |
| Red Team 검토 | LLM (Claude API) | `prompts.py::build_review_prompt()` |

---

## 4. 분류 결과가 다를 경우 대응

| 증상 | 원인 | 조치 |
|------|------|------|
| `target = 전체`인데 여성 전용 브랜드 | brand_list.csv에 gender 미등록 | brand_list.csv의 해당 brand_id gender 컬럼에 "여성" 입력 |
| `category_id = ""` 공란 | 팀명이 매핑 테이블에 없음 | rules.py TEAM_TO_CATEGORY에 팀명 추가 |
| LLM 카테고리 유추 결과가 엉뚱함 | 소재 내용이 불명확하거나 prompts.py 규칙 미흡 | build_category_infer_prompt() 선택 규칙 보완 |
| V3가 선택됐는데 희소성 없는 소재 | _V3_SCARCITY_PATTERN 키워드가 맞지 않음 | rules.py::_V3_SCARCITY_PATTERN 패턴 조정 |
