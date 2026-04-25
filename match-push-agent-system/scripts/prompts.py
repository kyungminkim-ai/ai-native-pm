"""LLM 프롬프트 템플릿 — Confluence Sub-PRD B 섹션 5 기준."""
import re


def _strip_unsubscribe(text: str) -> str:
    """수신거부 문구를 제거해 순수 메시지 본문만 반환."""
    return re.sub(r"\n수신거부.*$", "", text or "").strip()


def build_title_prompt(brand: str, promotion_content: str, target: str, remarks: str = "") -> str:
    target_ctx = {"여성": "여성 고객 대상", "남성": "남성 고객 대상"}.get(target, "전체 고객 대상")

    _remarks_section = f"\n## 마케터 메모 (우선 반영)\n{remarks.strip()}" if remarks and remarks.strip() else ""

    return f"""당신은 무신사 앱푸시 제목 작성 전문가입니다. {target_ctx}.

다음 소재 정보를 바탕으로 앱푸시 제목을 작성하세요.

## 소재 정보
- 브랜드: {brand or "정보 없음"}
- 프로모션 내용: {promotion_content or "정보 없음"}{_remarks_section}

## 작성 규칙
1. 길이: 15~40자 (공백 포함)
2. 브랜드명을 제목 앞부분에 배치
3. 소재 유형에 맞는 패턴을 아래 표에서 선택하여 적용
4. 명사형 종결 ("발매", "드롭", "출시", "할인", "에디션" 등으로 끝남)
5. 감탄사·명령조·"지금 확인" 등 행동 유도 어구 금지
6. 브랜드명은 한국어 표기 우선 (영문 브랜드는 그대로 사용 가능)

## 소재 유형별 패턴 (상황에 맞게 선택)
- 콜라보/협업:       "브랜드A × 브랜드B [설명]"          예) 컨버스 × 매드해피 척 70
- 콜라보 무신사 에디션: "브랜드 × 브랜드, 무신사 에디션"  예) 레이브 × 헬로키티, 무신사 에디션
- 아티스트/IP 드롭:  "브랜드명 무신사 드롭"               예) 킥플립 무신사 드롭
- 단독 선발매:       "브랜드 무신사 단독 선발매"           예) 시에라디자인 무신사 단독 선발매
- 시즌 신상:         "브랜드 26SS/25FW 컬렉션명"          예) 겐조 26SS 카툰 컬렉션
- 단순 할인:         "브랜드 최대 N% 할인"                예) 리드볼트 최대 20% 할인
- 대형 할인 캠페인:  "[최대 N%] 이벤트명"                 예) [최대 80%] 티셔츠 페스티벌 오픈
- 사은품/기획세트:   "브랜드 구매 시 [사은품] 증정"       예) 일리윤 기획세트 구매 시 몬치치 증정

## 출력 형식 (JSON만, 다른 텍스트 없이)
{{"title": "생성된 제목"}}"""


def build_v1_benefit_prompt(
    title: str, brand: str, promotion_content: str,
    content_type: str, target: str, remarks: str = "",
) -> str:
    target_ctx = {"여성": "여성 고객을 대상으로 합니다.", "남성": "남성 고객을 대상으로 합니다."}.get(
        target, "전체 고객을 대상으로 합니다."
    )
    _remarks_section = f"\n- 마케터 메모: {remarks.strip()}" if remarks and remarks.strip() else ""

    return f"""당신은 무신사 앱푸시 메시지 전문가입니다. {target_ctx}

다음 소재 정보를 바탕으로 혜택 강조형(V1 BENEFIT) 앱푸시 본문을 작성하세요.

## 소재 정보
- 제목: {title or "정보 없음"}
- 브랜드: {brand or "정보 없음"}
- 프로모션 내용: {promotion_content or "정보 없음"}
- 콘텐츠 유형: {content_type or "정보 없음"}{_remarks_section}

## 작성 규칙
1. 반드시 `(광고) `로 시작
2. 길이: 40~60자 (수신거부 문구 제외)
3. 혜택 수치 강조 (할인율 %, 쿠폰, 적립금, 결제혜택)
4. 복수 혜택은 `+`로 연결: `최대 30% 쿠폰 + 최대 5만원 적립금`
5. **명사형으로 반드시 끝낼 것** — "...증정", "...혜택", "...진행", "...할인", "...쿠폰"

## 금지 (위반 시 재작성)
- 동사형·형용사형 종결 절대 금지: "서둘러요", "해보세요", "놓치지 마세요", "받아보세요", "만나보세요", "확인하세요", "가세요", "오세요"
- 감탄사 및 과장어: "엄청난", "놀라운", "대박", "미친"
- 명령조: "사세요!", "하세요!", "마세요!"
- 모호한 표현: "다양한", "많은", "여러"
- 수신거부 문구 포함 금지 (Python이 별도 추가)

## 좋은 예시
- `(광고) 최대 30% 쿠폰 + 최대 5만원 적립금 + 최대 1만원 결제혜택`
- `(광고) 최대 80% 할인 + 단 하루 25% 쿠폰`
- `(광고) 최대 31% 할인 + 쿠폰 + 사은품 혜택`

## 나쁜 예시 (이렇게 쓰지 마세요)
- `(광고) 한정판 품절 전 서둘러요` ← 동사형 종결 금지
- `(광고) 지금 바로 혜택 받아보세요` ← 동사형 종결 금지

## 출력 형식 (JSON만, 다른 텍스트 없이)
{{"message": "생성된 본문 (수신거부 문구 제외)", "confidence": 신뢰도점수}}

confidence는 1.0~5.0 사이의 float. 5.0에 가까울수록 품질이 높음."""


def build_v2_brand_prompt(
    title: str, brand: str, promotion_content: str,
    content_type: str, target: str, remarks: str = "",
) -> str:
    target_ctx = {"여성": "여성 고객을 대상으로 합니다.", "남성": "남성 고객을 대상으로 합니다."}.get(
        target, "전체 고객을 대상으로 합니다."
    )
    _remarks_section = f"\n- 마케터 메모: {remarks.strip()}" if remarks and remarks.strip() else ""

    return f"""당신은 무신사 앱푸시 메시지 전문가입니다. {target_ctx}

다음 소재 정보를 바탕으로 브랜드/감성 강조형(V2 BRAND) 앱푸시 본문을 작성하세요.

## 소재 정보
- 제목: {title or "정보 없음"}
- 브랜드: {brand or "정보 없음"}
- 프로모션 내용: {promotion_content or "정보 없음"}
- 콘텐츠 유형: {content_type or "정보 없음"}{_remarks_section}

## 작성 규칙
1. 반드시 `(광고) `로 시작
2. 길이: 25~45자 (수신거부 문구 제외)
3. 브랜드/제품의 고유성·차별성을 감성적으로 표현
4. 수치(할인율 등) 최소화 — 혜택 나열 금지
5. 감성적·서사적 어조 권장
6. **명사형으로 반드시 끝낼 것** — "...존재감", "...발매", "...에디션", "...드롭", "...컬렉션"

## 금지 (위반 시 재작성)
- 동사형·형용사형 종결 절대 금지: "서둘러요", "해보세요", "만나보세요", "느껴보세요", "경험해보세요"
- 성급한 명령: "지금 바로 사세요!", "놓치지 마세요!"
- 일반 형용사 반복: "좋은", "멋진", "예쁜"
- 혜택 수치 나열 (V1과 중복 방지)
- 수신거부 문구 포함 금지 (Python이 별도 추가)

## 좋은 예시
- `(광고) 올 블랙보다 시크한 그레이 스티치의 존재감`
- `(광고) 다시 시작되는 그들의 이야기를 담은 굿즈, 무신사 드롭 발매`

## 나쁜 예시 (이렇게 쓰지 마세요)
- `(광고) 현진과 에스에스알엘의 협업, 지금 만나보세요` ← 동사형 종결 금지
- `(광고) 스타일을 느껴보세요` ← 동사형 종결 금지

## 출력 형식 (JSON만, 다른 텍스트 없이)
{{"message": "생성된 본문 (수신거부 문구 제외)", "confidence": 신뢰도점수}}

confidence는 1.0~5.0 사이의 float. 5.0에 가까울수록 품질이 높음."""


def build_v3_best_prompt(
    title: str, brand: str, promotion_content: str,
    content_type: str, target: str,
    v1_message: str = "", v2_message: str = "",
    remarks: str = "",
) -> str:
    target_ctx = {"여성": "여성 고객을 대상으로 합니다.", "남성": "남성 고객을 대상으로 합니다."}.get(
        target, "전체 고객을 대상으로 합니다."
    )
    _remarks_section = f"\n- 마케터 메모: {remarks.strip()}" if remarks and remarks.strip() else ""
    v1_clean = _strip_unsubscribe(v1_message) if v1_message else "(없음)"
    v2_clean = _strip_unsubscribe(v2_message) if v2_message else "(없음)"

    return f"""당신은 무신사 앱푸시 메시지 전문가입니다. {target_ctx}

V1(혜택강조)과 V2(브랜드감성) 두 버전을 비교·분석하여, 각각의 장점을 결합한 최선의 V3 앱푸시 본문을 작성하세요.

## 소재 정보
- 제목: {title or "정보 없음"}
- 브랜드: {brand or "정보 없음"}
- 프로모션 내용: {promotion_content or "정보 없음"}
- 콘텐츠 유형: {content_type or "정보 없음"}{_remarks_section}

## 기존 버전 (참고·개선 대상)
- V1 (혜택강조): {v1_clean}
- V2 (브랜드감성): {v2_clean}

## V3 작성 지침
1. 반드시 `(광고) `로 시작
2. 길이: 25~45자 (수신거부 문구 제외)
3. **V1의 약점 보완**: 제목과 본문이 중복되는 경우 → 본문에서 제목 내용 반복 금지
4. **V2의 약점 보완**: 혜택 정보가 전혀 없어 클릭 동기가 약한 경우 → 핵심 혜택 1개만 간결히 추가
5. **가이드라인 완전 충족**: 명사형 종결, 금칙어 없음, 수치 과장 없음
6. V1과 V2 중 더 나은 표현이 있다면 그것을 발전시켜도 됨

## 명사형 종결 필수 (위반 시 재작성)
- 동사형·형용사형 종결 절대 금지: "서둘러요", "해보세요", "만나보세요", "확인하세요", "받아보세요"
- 반드시 명사로 끝나야 함: "...혜택", "...발매", "...에디션", "...할인", "...증정", "...드롭"

## 금지
- 과장어: "엄청난", "놀라운", "대박", "초특가"
- 명령조: "사세요!", "하세요!"
- 모호한 표현: "다양한", "많은", "여러"
- 수신거부 문구 포함 금지 (Python이 별도 추가)

## 좋은 V3 예시
- V1: `(광고) 에스에스알엘 × 현진 무신사 에디션, 최대 31% 할인 + 쿠폰 + 사은품 혜택` (제목과 중복)
- V2: `(광고) 에스에스알엘과 현진이 함께 완성한 무신사 에디션` (혜택 없음)
- V3: `(광고) 현진 × 에스에스알엘, 최대 31% 할인 + 사은품 혜택` (중복 제거 + 핵심 혜택 유지)

## 출력 형식 (JSON만, 다른 텍스트 없이)
{{"message": "생성된 본문 (수신거부 문구 제외)", "confidence": 신뢰도점수}}

confidence는 1.0~5.0 사이의 float. 5.0에 가까울수록 품질이 높음."""


def build_review_prompt(
    title: str, contents_v1: str, contents_v2: str,
    brand: str, promotion_content: str, target: str,
    contents_v3: str = "",
) -> str:
    target_ctx = {"여성": "여성 고객 대상", "남성": "남성 고객 대상"}.get(target, "전체 고객 대상")
    v1_clean = _strip_unsubscribe(contents_v1)
    v2_clean = _strip_unsubscribe(contents_v2)
    v3_clean = _strip_unsubscribe(contents_v3) if contents_v3 else ""
    v3_line = f"\n- 본문 V3 (최선책 합성): {v3_clean or '(없음)'}" if v3_clean else ""

    return f"""당신은 무신사 앱푸시 메시지 품질 검토 전문가입니다. {target_ctx}.

생성된 앱푸시 메시지를 소재 원본과 비교하며 독립적인 관점에서 평가하세요.
생성 규칙이 아닌 실제 수신자 경험·브랜드 적합성·마케팅 효과 관점에서만 평가합니다.

## 소재 원본
- 브랜드: {brand or "정보 없음"}
- 프로모션 내용: {promotion_content or "정보 없음"}

## 생성된 메시지
- 제목: {title or "(없음)"}
- 본문 V1 (혜택강조): {v1_clean or "(없음)"}
- 본문 V2 (브랜드감성): {v2_clean or "(없음)"}{v3_line}

## 평가 기준
1. **정확성**: 소재 원본의 혜택·브랜드 정보가 왜곡 없이 반영됐는가?
2. **수신자 반응**: 메시지를 받았을 때 클릭 의향이 생기는가?
3. **브랜드 일관성**: 무신사 특유의 감각적·트렌디·젊은 톤앤매너에 맞는가?
4. **차별성**: 흔한 할인 광고와 차별화되는 요소가 있는가?
5. **문제 여부**: 과장 표현, 오해 소지, 부정확한 수치가 있는가?

## 출력 형식 (JSON만, 다른 텍스트 없이)
{{
  "score": 종합점수,
  "verdict": "pass",
  "notes": "핵심 피드백 한 문장 (문제 없으면 빈 문자열)",
  "issues": ["이슈1", "이슈2"]
}}

score: 1.0~5.0 float. verdict: pass(3.5이상) / warning(2.5~3.4) / fail(2.4이하).
issues는 실제 문제가 있을 때만 기재, 없으면 빈 배열 []."""


def build_category_infer_prompt(
    event_name: str,
    promotion_content: str,
    main_title: str,
    landing_url: str,
    category_list_str: str,
) -> str:
    return f"""당신은 무신사 앱푸시 소재를 분류하는 전문가입니다.

아래 소재 정보를 보고, 해당 소재와 관련된 카테고리 코드를 선택하세요.

## 소재 정보
- 이벤트명: {event_name or "정보 없음"}
- 프로모션 내용: {promotion_content or "정보 없음"}
- 제목: {main_title or "정보 없음"}
- 랜딩 URL: {landing_url or "정보 없음"}

## 선택 가능한 카테고리 (코드: 카테고리명)
{category_list_str}

## 선택 규칙
1. 소재 내용에 가장 부합하는 카테고리 코드를 최대 3개 선택
2. 명확하게 관련 있는 카테고리만 선택 (불확실하면 선택 금지)
3. K-Pop 굿즈·앨범 → 111, E-Sports·스포츠구단 → 112, 캐릭터(디즈니/마블 등) → 113, 만화/애니메이션 → 114
4. 일반 패션 소재(단순 할인행사)는 의류/신발 등 해당 카테고리만 선택
5. 관련 카테고리가 없으면 빈 배열 반환

## 출력 형식 (JSON만, 다른 텍스트 없이)
{{"codes": ["코드1", "코드2"]}}

codes는 최대 3개. 해당 없으면 빈 배열 []."""
