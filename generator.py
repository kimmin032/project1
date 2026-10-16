"""문구 생성의 전체 흐름을 담당하는 파일.

지시문 만들기(prompts) → AI 호출(llm_client) → 답변을 정리해서 돌려주기.
"""

import json

from llm_client import LLMError, ask_llm
from prompts import build_prompt


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


def make_copy(description: str, persona: str, framework: str = "자동") -> dict:
    """A안·B안 문구를 만들어 돌려준다.

    결과 모양:
    {"framework": "AIDA", "a": {"angle": "...", "copy": "..."}, "b": {"angle": "...", "copy": "..."}}
    """
    system, user = build_prompt(description, persona, framework)
    result = _parse_json(ask_llm(user, system=system))

    # 화면에서 쓸 값이 다 있는지 확인 (없으면 빈 값으로 채우지 않고 에러로 알린다)
    try:
        for key in ("a", "b"):
            result[key]["angle"]
            result[key]["copy"]
    except (KeyError, TypeError):
        raise LLMError("AI 답변에 A안/B안이 빠져 있습니다. 다시 시도해 주세요.") from None

    result.setdefault("framework", framework)
    return result


if __name__ == "__main__":
    # 터미널에서 `python generator.py` 로 실행하는 간단 테스트
    try:
        out = make_copy("수제 가죽 카드지갑", "가성비 중심 대학생")
        print("구조:", out["framework"])
        for key, name in (("a", "A안"), ("b", "B안")):
            print("\n[{}] 소구점: {}".format(name, out[key]["angle"]))
            print(out[key]["copy"])
    except LLMError as e:
        print("[오류] {}".format(e))
