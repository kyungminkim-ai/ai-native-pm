"""Rule-based 처리 모듈 — 소재 선별 및 메타데이터 생성 규칙."""
import re
import string
from datetime import datetime, timedelta
from typing import Optional

_SINGLE_DIGIT_HOUR = re.compile(r'^(\d{4}-\d{2}-\d{2})\s+(\d):')
from config import (
    MARKETING_TEAM_KEYWORDS, CANCEL_KEYWORDS, SEND_HOUR, SEND_WINDOW_DAYS,
    SEND_WINDOW_START_HOUR, TITLE_MIN_LEN, TITLE_MAX_LEN, MEANINGLESS_TITLES,
    AD_CODE_PREFIX, UNSUBSCRIBE_TEXT,
)


# ── 소재 선별 규칙 ─────────────────────────────────────────────────────

def is_cancelled(remarks: Optional[str]) -> bool:
    if not remarks:
        return False
    return any(kw.lower() in remarks.lower() for kw in CANCEL_KEYWORDS)


def is_marketing_team(team_name: Optional[str]) -> bool:
    if not team_name:
        return False
    return any(kw in team_name for kw in MARKETING_TEAM_KEYWORDS)


def _parse_release_dt(release_dt) -> Optional[datetime]:
    """release_start_date_time 값을 datetime으로 파싱.
    단자리 시각(예: '2026-04-27 2:00:00')도 허용.
    """
    if release_dt is None or isinstance(release_dt, float):
        return None
    if isinstance(release_dt, str):
        release_dt = release_dt.strip()
        if not release_dt:
            return None
        # '2026-04-27 2:00:00' → '2026-04-27 02:00:00' (Python 3.9 fromisoformat 호환)
        release_dt = _SINGLE_DIGIT_HOUR.sub(r'\1 0\2:', release_dt)
        try:
            return datetime.fromisoformat(release_dt)
        except ValueError:
            return None
    if isinstance(release_dt, datetime):
        return release_dt
    return None


def is_in_send_window(release_dt, send_dt: str) -> bool:
    """발송 윈도우 체크: D-1 10:00 <= release_dt < D-0 10:00 (SEND_WINDOW_DAYS 기준)."""
    dt = _parse_release_dt(release_dt)
    if dt is None:
        return False
    send_date    = datetime.strptime(send_dt, "%Y-%m-%d")
    window_start = (send_date - timedelta(days=SEND_WINDOW_DAYS)).replace(
        hour=SEND_WINDOW_START_HOUR, minute=0, second=0, microsecond=0
    )
    window_end   = send_date.replace(hour=SEND_HOUR, minute=0, second=0, microsecond=0)
    return window_start <= dt < window_end


def is_landing_open(release_dt, send_dt: str) -> bool:
    """하위 호환 — is_in_send_window 로 위임."""
    return is_in_send_window(release_dt, send_dt)


def validate_landing_url(url: Optional[str]):
    """랜딩 URL 유효성 검사. 문제 있으면 reason code(str) 반환, 정상이면 None."""
    from run_logger import (
        REASON_URL_MISSING, REASON_URL_PLACEHOLDER,
        REASON_URL_NO_ID, REASON_URL_NOT_MUSINSA, REASON_URL_FORMAT,
    )

    if not url or not isinstance(url, str) or not url.strip():
        return REASON_URL_MISSING

    url = url.strip()

    # http로 시작하지 않으면 형식 오류
    if not url.lower().startswith("http"):
        return REASON_URL_FORMAT

    # 한국어 포함 또는 TBD 임시값
    if re.search(r'[가-힣]', url) or re.search(r'\bTBD\b', url, re.IGNORECASE):
        return REASON_URL_PLACEHOLDER

    # musinsa.com 외부 도메인
    if "musinsa.com" not in url.lower():
        return REASON_URL_NOT_MUSINSA

    # /content/ 또는 /campaign/ 경로에 유효한 ID 없음
    content_match  = re.search(r'/content/([^/?&#]*)',  url)
    campaign_match = re.search(r'/campaign/([^/?&#]*)', url)
    if content_match or campaign_match:
        segment = (content_match or campaign_match).group(1).strip()
        if not segment or len(segment) < 2 or not re.search(r'\d', segment):
            return REASON_URL_NO_ID

    return None


def is_already_selected(ad_status) -> bool:
    """선정 여부 컬럼에 '광고진행' 계열이 있으면 True (이미 진행/완료된 소재)."""
    if ad_status is None:
        return False
    status = str(ad_status).strip()
    if not status or status.lower() in ("nan", "none", ""):
        return False
    if status == "광고미진행":
        return False
    return "광고진행" in status


def make_sheet_key(landing_url: str, brand_id: str, send_dt: str) -> str:
    return f"{landing_url or ''}|{brand_id or ''}|{send_dt}"


# ── 메타데이터 생성 규칙 ───────────────────────────────────────────────

def sanitize_title(raw: Optional[str]) -> str:
    """제목에서 제어문자와 literal escape 시퀀스를 제거하고 연속 공백을 정규화한다.

    앱푸시 제목에 Webhook용 \\n 등이 섞이는 경우를 방지한다.
    순수 한글만 포함된 대괄호 레이블(예: [콜라보], [한정])도 제거한다.
    숫자·특수문자 포함 대괄호(예: [최대 80%])는 유지한다.
    """
    if not raw:
        return ""
    cleaned = re.sub(r"[\n\r\t]", " ", raw)           # 실제 제어문자
    cleaned = re.sub(r"\\[nrt]", " ", cleaned)         # literal \n \r \t (2자 시퀀스)
    cleaned = re.sub(r"\s*\[[가-힣]+\]\s*", " ", cleaned)  # 순수 한글 대괄호 레이블
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


def classify_target(
    team_name: Optional[str],
    brand_id: Optional[str] = None,
    brand_df=None,
) -> str:
    """팀명 → brand_list 성별 → 전체 순으로 타겟 성별을 결정한다.

    Step 1: 팀명에 "여성"/"남성" 키워드가 있으면 해당 성별 반환
    Step 2: brand_list.gender에 "여성"/"남성"이 등록돼 있으면 반환
    Step 3: "전체"
    """
    if team_name:
        if "여성" in team_name:
            return "여성"
        if "남성" in team_name:
            return "남성"

    if brand_id and brand_df is not None and not brand_df.empty:
        matches = brand_df[brand_df["brand_id"] == brand_id]
        if not matches.empty:
            gender = str(matches.iloc[0].get("gender", "") or "").strip()
            if gender in ("여성", "남성"):
                return gender

    return "전체"


def get_content_type(landing_url: Optional[str]) -> Optional[str]:
    if not landing_url:
        return None
    if "/campaign/" in landing_url:
        return "캠페인"
    if "/content/" in landing_url:
        return "콘텐츠"
    if "/brand/" in landing_url:
        return "브랜드"
    return None


def get_priority(team_name: Optional[str], landing_url: Optional[str]) -> int:
    if not team_name:
        return 3
    if "전사캠페인" in team_name:
        return 1
    if "카테고리마케팅" in team_name:
        return 2
    return 3


def get_category_id(team_name: Optional[str]) -> str:
    """팀명 → 카테고리 ID 임시 매핑 테이블."""
    TEAM_TO_CATEGORY = {
        "아웃도어":      "017",
        "스포츠":        "017",
        "애슬레저":      "017",
        "풋웨어":        "103",
        "무신사풋웨어":  "103",
        "뷰티":          "104",
        "뷰티1":         "104",
        "뷰티2":         "104",
        "여성패션":      "100",
        "남성패션":      "001",
        "유니섹스패션":  "001",
        "키즈":          "106",
        "라이프":        "102",
        "글로벌패션":    "001",
    }
    if not team_name:
        return ""
    for key, cat_id in TEAM_TO_CATEGORY.items():
        if key in team_name:
            return cat_id
    return ""


def is_title_valid(title: Optional[str]) -> bool:
    if not title or not isinstance(title, str):
        return False
    title = title.strip()
    if not title or title.lower() in MEANINGLESS_TITLES:
        return False
    if len(title) < TITLE_MIN_LEN or len(title) > TITLE_MAX_LEN:
        return False
    # 영문 코드만 존재하는 경우 (예: INSALES_2Q_0412)
    if re.fullmatch(r"[A-Z0-9_\-]+", title):
        return False
    return True


def _int_to_base36(n: int) -> str:
    chars = string.digits + string.ascii_uppercase
    result = ""
    while n:
        result = chars[n % 36] + result
        n //= 36
    return result or "0"


def generate_ad_code(last_code: Optional[str]) -> str:
    """마지막 광고코드에서 +1 채번. 없으면 APSCMCD001 시작."""
    if not last_code or not last_code.startswith(AD_CODE_PREFIX):
        return f"{AD_CODE_PREFIX}001"
    suffix = last_code[len(AD_CODE_PREFIX):]
    try:
        num = int(suffix, 36) + 1
    except ValueError:
        num = 1
    return f"{AD_CODE_PREFIX}{_int_to_base36(num).zfill(3)}"


def build_push_url(landing_url: str, ad_code: str) -> str:
    if not landing_url or not ad_code:
        return ""
    utm = (
        f"utm_source=app_push"
        f"&utm_medium=cr"
        f"&utm_content=mf"
        f"&utm_campaign={ad_code}"
        f"&source={ad_code}"
    )
    sep = "&" if "?" in landing_url else "?"
    return f"{landing_url}{sep}{utm}"


def append_unsubscribe(message: str) -> str:
    if not message:
        return ""
    return f"{message}\n{UNSUBSCRIBE_TEXT}"


def lookup_brand_name(brand_id: Optional[str], brand_df) -> str:
    """brand_list DataFrame에서 한국어 브랜드명 조회."""
    if not brand_id or brand_df is None or brand_df.empty:
        return brand_id or ""
    matches = brand_df[brand_df["brand_id"] == brand_id]
    if matches.empty:
        return brand_id
    return str(matches.iloc[0].get("brand_nm", brand_id))


def lookup_brand_names(brand_id: Optional[str], brand_df) -> tuple:
    """brand_list DataFrame에서 (한국어명, 영문명) 튜플 조회."""
    if not brand_id or brand_df is None or brand_df.empty:
        return ("", "")
    matches = brand_df[brand_df["brand_id"] == brand_id]
    if matches.empty:
        return ("", "")
    row = matches.iloc[0]
    return (str(row.get("brand_nm", "") or ""), str(row.get("brand_nm_eng", "") or ""))


def build_category_list_str(category_df) -> str:
    """category_selector DataFrame에서 1뎁스 카테고리 목록 문자열 생성 (LLM 프롬프트용)."""
    if category_df is None or category_df.empty:
        return ""
    depth1 = category_df[category_df["구분"] == "1뎁스"]
    lines = [f"{row['코드']}: {row['카테고리명']}" for _, row in depth1.iterrows()]
    return "\n".join(lines)


# ── 산출물 컬럼 자동 생성 ─────────────────────────────────────────────

def build_braze_campaign_name(
    send_dt: str, send_time: str, ad_code: str,
    title: str, target: str, content_type: Optional[str],
) -> str:
    """캠페인메타엔진 braze_campaign_name 자동 생성.

    형식: YYMMDD_HH시_ADCODE_정기_GMV_{title}_{target}_{content_type}
    예시: 260428_11시_APSCMCD99A_정기_GMV_글랙 × 지꾸 콜라보 한정 발매_전체_콘텐츠
    """
    try:
        yy = str(send_dt)[2:4]
        mm = str(send_dt)[5:7]
        dd = str(send_dt)[8:10]
    except (IndexError, TypeError):
        yy = mm = dd = "00"
    hh = str(send_time or "11:00")[:2]
    ct = str(content_type or "")
    return f"{yy}{mm}{dd}_{hh}시_{ad_code}_정기_GMV_{title}_{target}_{ct}"


def build_feed_url(landing_url: str, ad_code: str) -> str:
    """feed_url 자동 생성.

    ad_code 앞 3자(APS)를 FED로 교체한 source 파라미터를 landing_url에 삽입.
    # fragment가 있으면 그 앞에 삽입, 없으면 끝에 추가.
    """
    if not landing_url or not ad_code:
        return ""
    fed_code = "FED" + ad_code[3:]   # "APSCMCD99A" → "FEDCMCD99A"
    if "#" in landing_url:
        hash_pos = landing_url.find("#")
        base     = landing_url[:hash_pos]
        fragment = landing_url[hash_pos:]
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}source={fed_code}{fragment}"
    elif "?" in landing_url:
        return f"{landing_url}&source={fed_code}"
    else:
        return f"{landing_url}?source={fed_code}"


def build_webhook_contents(contents: str) -> str:
    """webhook_contents 자동 생성.

    contents의 실제 개행(\\n)을 literal '\\\\n' 문자열로 치환.
    """
    return (contents or "").replace("\n", "\\n")


_V1_PRIORITY_PATTERN  = re.compile(r'%|한정|단독')
_V3_SCARCITY_PATTERN  = re.compile(r'마감|선착순|한정수량|오늘까지|오늘|D-day|품절|마지막')


def select_contents(
    v1_message: Optional[str],
    v2_message: Optional[str],
    v3_message: Optional[str] = None,
) -> tuple:
    """V1·V2·V3 중 발송 본문(contents)을 자동 선택한다.

    우선순위:
      1. V1 — 할인율(%) 또는 "한정"/"단독" 키워드 포함 시 (혜택 수치 강조)
      2. V3 — 긴급성/희소성 키워드 포함 시 (단, V1이 선택되지 않은 경우)
      3. V2 — 그 외 기본값 (브랜드감성)

    반환: (선택된 메시지, 소스 "v1"|"v2"|"v3")
    """
    if v1_message and _V1_PRIORITY_PATTERN.search(v1_message):
        return (v1_message, "v1")
    if v3_message and _V3_SCARCITY_PATTERN.search(v3_message):
        return (v3_message, "v3")
    return (v2_message, "v2")
