"""V3 재생성 스크립트 — 기존 llm_responses에서 V3를 새 로직(V1+V2 합성 최선책)으로 갱신."""
import json
import re
import sys
import time
import anthropic
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from prompts import build_v3_best_prompt


RESPONSES_PATH = Path(__file__).parent.parent / "data" / "llm_responses_20260428_20260504.json"
OUTPUT_PATH    = Path(__file__).parent.parent / "data" / "llm_responses_20260428_20260504_v3new.json"
MODEL          = "claude-sonnet-4-6"


def _strip_unsubscribe(text: str) -> str:
    return re.sub(r"\n수신거부.*$", "", text or "").strip()


def _call_claude(client: anthropic.Anthropic, prompt: str):
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                m = re.search(r"\{.*\}", raw, re.DOTALL)
                if m:
                    return json.loads(m.group())
        except anthropic.RateLimitError:
            wait = 2 ** attempt
            print(f"  Rate limit — {wait}s 대기", flush=True)
            time.sleep(wait)
        except Exception as e:
            print(f"  API 오류 ({attempt+1}/3): {e}", flush=True)
            time.sleep(2 ** attempt)
    return None


def main():
    data = json.loads(RESPONSES_PATH.read_text(encoding="utf-8"))

    try:
        client = anthropic.Anthropic()
        use_api = True
        print("API 모드로 V3 재생성합니다.")
    except Exception:
        use_api = False
        print("API 키 없음 — 수동 V3 값으로 패치합니다.")

    # 수동 V3 값 (API 없을 때 사용 — writing_policy.md 기준으로 사람이 작성)
    manual_v3 = {
        "605315": "(광고) 현진 × 에스에스알엘, 최대 31% 할인 + 사은품 혜택",
        "605757": "(광고) 글랙 × 지꾸 첫 콜라보, 최대 25% 할인 + 키링 증정",
        "588695": "(광고) 한화생명e스포츠 × 무신사, 공식 라이선스 굿즈 단독 발매",
        "606962": "(광고) 1993스튜디오 × FC서울, 무신사 단독 한정 발매",
        "615455": "(광고) 컨버스 × 다저스 × 언디피티드 척70 한정 발매",
        "615902": "(광고) 오찌 코브스 쪼리 신규 발매, 여름 한정 컬렉션",
        "605412": "(광고) 카니 × 어프어프 무신사 단독 선발매 특별 혜택",
        "616022": "(광고) 미니틴 공식 라이선스 머치, 무신사 한정 단독 발매",
        "614141": "(광고) 몽클레르 26SS 풋웨어 셀렉션, 무신사 단독 입점",
        "605521": "(광고) 시리즈 × GTO 첫 콜라보, 무신사 단독 선발매",
        "606032": "(광고) 산리오 × 커버낫 키즈 한정 스페셜, 무신사 발매",
        "599256": "(광고) 수아레 × 핏더사이즈 무신사 단독 콜라보 발매",
        "615357": "(광고) 무신사 스포츠 브랜드, 최대 70% 할인 + 20% 쿠폰",
        "612469": "(광고) 웬즈데이오아시스 × 정무드, 무신사 단독 에디션",
        "613044": "(광고) 에스트라 더마 UV, 위글위글 특별 사은품 증정",
        "613082": "(광고) 리복 × 발란사 무신사 단독 발매, 한정 풋웨어 컬렉션",
        "613132": "(광고) 일리윤 × 몬치치, 기획세트 구매 시 사은품 증정",
        "614655": "(광고) 데우스 엑스 마키나 26SS 신상, 무신사 단독 라인업",
        "615900": "(광고) 뉴발란스 썸머런팩, 1080V5 & REBELV5 신규 발매",
        "615153": "(광고) 무신사 풋웨어, 최대 70% 할인 + 20% 쿠폰 혜택",
    }

    updated = dict(data)
    total = len(data)

    for i, (job_id, entry) in enumerate(data.items(), 1):
        title   = entry.get("title", "")
        v1_msg  = _strip_unsubscribe(entry.get("contents", ""))
        v2_msg  = _strip_unsubscribe(entry.get("contents_v2", ""))
        old_v3  = entry.get("contents_v3", "")

        print(f"[{i:2d}/{total}] ID={job_id} | title={title[:20]}...", flush=True)
        print(f"  V1: {v1_msg[:50]}", flush=True)
        print(f"  V2: {v2_msg[:50]}", flush=True)
        print(f"  V3 (old): {old_v3[:50]}", flush=True)

        if use_api:
            prompt = build_v3_best_prompt(
                title=title,
                brand="",
                promotion_content="",
                content_type="",
                target="전체",
                v1_message=v1_msg,
                v2_message=v2_msg,
            )
            parsed = _call_claude(client, prompt)
            if parsed and "message" in parsed:
                new_v3 = parsed["message"]
                new_conf = float(parsed.get("confidence", 4.5))
            else:
                new_v3 = manual_v3.get(job_id, old_v3)
                new_conf = 4.0
        else:
            new_v3 = manual_v3.get(job_id, old_v3)
            new_conf = 4.5

        updated[job_id] = {**entry, "contents_v3": new_v3, "confidence_v3": new_conf}
        print(f"  V3 (new): {new_v3}", flush=True)
        print(flush=True)

        if use_api and i < total:
            time.sleep(0.5)

    OUTPUT_PATH.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
