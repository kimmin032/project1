"""문구 생성의 전체 흐름을 담당하는 파일.

지시문 만들기(prompts) → AI 호출(llm_client) → 답변을 정리해서 돌려주기.
"""

import json
import re

from input_check import check_input
from llm_client import LLMError, ask_llm
from prompts import CHANNEL_LABELS, CHANNEL_LIMITS, EMAIL_AD_PREFIX, build_prompt


def _parse_json(text: str) -> dict:
    """AI 답변에서 JSON 부분만 꺼내 파이썬 딕셔너리로 바꾼다."""
    # AI가 가끔 ```json ... ``` 로 감싸거나 앞뒤에 말을 붙이므로 { } 사이만 잘라낸다
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise LLMError("AI 답변에서 결과를 찾지 못했습니다. 다시 시도해 주세요.")
    try:
        return json.loads(text[start:end + 1])
    except ValueError:
        raise LLMError("AI 답변 형식이 깨졌습니다. 다시 시도해 주세요.") from None


def _with_ad_prefix(subject: str) -> str:
    """이메일 제목 맨 앞에 "(광고) "를 붙인다. AI가 이미 붙였으면 중복되지 않게 먼저 뗀다."""
    subject = subject.strip()
    if subject.startswith("(광고)"):
        subject = subject[len("(광고)"):].strip()
    return EMAIL_AD_PREFIX + subject


def check_lengths(variant: dict) -> list:
    """한 안(a 또는 b)의 채널별 글자 수를 검사한다. 글자는 절대 자르지 않는다.

    채널마다 {"key", "text", "length", "limit", "excess"} 를 돌려준다. excess가 0보다 크면 초과.
    """
    ch = variant["channels"]
    texts = {
        "kakao_body": ch["kakao"],
        "insta_headline": ch["instagram"]["headline"],
        "insta_body": ch["instagram"]["body"],
        "email_subject": ch["email_subject"],  # "(광고) " 포함된 상태로 센다
    }
    report = []
    for key, text in texts.items():
        limit = CHANNEL_LIMITS[key]
        report.append({
            "key": key,
            "text": text,
            "length": len(text),
            "limit": limit,
            "excess": max(0, len(text) - limit),
        })
    return report


def _read_text(getter) -> str:
    """AI 답변에서 글자 값을 꺼낸다. 없거나 빈 값이면 에러."""
    try:
        value = getter()
    except (KeyError, TypeError):
        value = None
    if not isinstance(value, str) or not value.strip():
        raise LLMError("AI 답변에 일부 항목이 빠져 있습니다. 다시 시도해 주세요.")
    return value.strip()


def make_copy(description: str, persona: str, framework: str = "자동") -> dict:
    """A안·B안 문구, 채널별 버전, CTR 가설을 만들어 돌려준다.

    결과 모양 (a, b 각각):
    {"angle", "copy", "hypothesis",
     "channels": {"kakao", "instagram": {"headline", "body"}, "email_subject"},
     "checks": [채널별 글자 수 검사 결과]}
    """
    system, user = build_prompt(description, persona, framework)
    result = _parse_json(ask_llm(user, system=system))

    # 화면에서 쓸 값이 다 있는지 확인 (없으면 빈 값으로 채우지 않고 에러로 알린다)
    for key in ("a", "b"):
        v = result.get(key) if isinstance(result, dict) else None
        if not isinstance(v, dict):
            raise LLMError("AI 답변에 A안/B안이 빠져 있습니다. 다시 시도해 주세요.")
        v["angle"] = _read_text(lambda: v["angle"])
        v["copy"] = _read_text(lambda: v["copy"])
        v["hypothesis"] = _clean_hypothesis(_read_text(lambda: v["hypothesis"]))
        ch = v.get("channels") if isinstance(v.get("channels"), dict) else {}
        insta = ch.get("instagram") if isinstance(ch.get("instagram"), dict) else {}
        v["channels"] = {
            "kakao": _read_text(lambda: ch["kakao"]),
            "instagram": {
                "headline": _read_text(lambda: insta["headline"]),
                "body": _read_text(lambda: insta["body"]),
            },
            "email_subject": _with_ad_prefix(_read_text(lambda: ch["email_subject"])),
        }
        v["checks"] = check_lengths(v)

    result.setdefault("framework", framework)
    return result


UNKNOWN_ERROR_MESSAGE = "알 수 없는 오류가 났어요. 다시 시도해 주세요."

# 화면이 이미 "A안: "을 붙이므로, AI가 가설 문장 앞에 쓴 "A안은", "A안이 검증하는 CTR 가설은" 같은 머리말
_HYPOTHESIS_PREFIXES = [
    re.compile(r"^[AaBb]안\s*(?:이|은|는|가)?\s*검증하는\s*CTR\s*가설\s*(?:은|는|이|:|：)?\s*"),
    re.compile(r"^[AaBb]안\s*(?:은|는|이|가|의)\s+"),
    re.compile(r"^[AaBb]안\s*[:：\-]\s*"),
    re.compile(r"^CTR\s*가설\s*(?:은|는|이|:|：)\s*"),
]


def _clean_hypothesis(text):
    """가설 문장 앞의 겹치는 머리말을 지운다. 다 지워서 빈 문장이 되면 원래 문장을 돌려준다."""
    cleaned = text.strip()
    changed = True
    while changed:
        changed = False
        for pattern in _HYPOTHESIS_PREFIXES:
            new = pattern.sub("", cleaned, count=1)
            if new != cleaned:
                cleaned, changed = new, True
    return cleaned or text.strip()


def generate(description, persona, framework="자동"):
    """입력 검사 → 문구 생성. 어떤 경우에도 예외를 밖으로 내보내지 않는다.

    결과 모양: {"ok": bool, "result": 문구 결과 또는 None, "warning": 경고 한 줄 또는 None, "notice": 안내 한 줄 또는 None}
    """
    try:
        checked = check_input(description, persona)
        if not checked["ok"]:  # 검사에 걸리면 AI를 부르지 않는다
            return {"ok": False, "result": None, "warning": checked["warning"], "notice": None}
        result = make_copy(checked["description"], checked["persona"], framework)
        return {"ok": True, "result": result, "warning": None, "notice": checked["notice"]}
    except LLMError as e:  # 메시지에 API 키는 들어 있지 않다
        return {"ok": False, "result": None, "warning": str(e), "notice": None}
    except Exception:  # 예상 못 한 오류: 내용은 화면에 내보내지 않는다
        return {"ok": False, "result": None, "warning": UNKNOWN_ERROR_MESSAGE, "notice": None}


if __name__ == "__main__":
    # 터미널에서 `python generator.py` 로 실행하는 간단 테스트
    try:
        out = make_copy("수제 가죽 카드지갑, 슬림형, 카드 6장 수납, 2만원대", "가성비 중심 대학생")
        print("구조:", out["framework"])
        for key, name in (("a", "A안"), ("b", "B안")):
            v = out[key]
            print("\n[{}] 소구점: {}".format(name, v["angle"]))
            print(v["copy"])
            print("CTR 가설:", v["hypothesis"])
            for c in v["checks"]:
                mark = "  <- {}자 초과".format(c["excess"]) if c["excess"] else ""
                print("  - {} ({}/{}자){}\n    {}".format(
                    CHANNEL_LABELS[c["key"]], c["length"], c["limit"], mark, c["text"]))
    except LLMError as e:
        print("[오류] {}".format(e))
