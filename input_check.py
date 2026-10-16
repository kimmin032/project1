"""사용자 입력을 AI에 보내기 전에 검사하는 파일.

AI를 부르지 않는 순수 함수라서, 이상한 값이 들어와도 에러 없이 결과만 돌려준다.
"""

from prompts import DEFAULT_PERSONA, PERSONAS

MIN_LENGTH = 5  # 최소 글자 수 (한글·영문 글자만 센다. 공백·숫자·특수문자는 세지 않음)

EMPTY_MESSAGE = "상품 설명을 입력해 주세요."
HELP_MESSAGE = "특징·가격을 더 적어 주세요. 예: 수제 가죽 카드지갑, 슬림형, 카드 6장 수납, 2만원대"
DEFAULT_PERSONA_NOTICE = "기본 페르소나를 적용했어요 ({})".format(DEFAULT_PERSONA)


def _reject(warning):
    return {"ok": False, "description": "", "persona": None, "warning": warning, "notice": None}


def check_input(description, persona):
    """입력을 검사해서 {"ok", "description", "persona", "warning", "notice"} 를 돌려준다.

    ok가 False면 warning을 보여주고 AI를 부르지 않는다.
    ok가 True면 description·persona를 그대로 AI에 쓰면 되고, 기본 페르소나를 썼다면 notice가 채워진다.
    """
    text = description.strip() if isinstance(description, str) else ""
    compact = "".join(text.split())  # 공백·줄바꿈을 모두 뺀 글자

    if not compact:  # 규칙 2: 비었음 (문자열이 아닌 값도 비었다고 본다)
        return _reject(EMPTY_MESSAGE)
    # 규칙 1: 너무 짧음 / 규칙 4: 특수문자·숫자뿐 → 같은 안내
    # 길이는 한글·영문 글자만 센다. (그래야 "옷팝니다!!!12345"처럼 숫자·기호로 5자를 채울 수 없다)
    # 글자가 하나도 없으면 0자라서 규칙 4도 이 한 줄로 걸러진다.
    letters = sum(1 for ch in compact if ch.isalpha())
    if letters < MIN_LENGTH:
        return _reject(HELP_MESSAGE)

    # 규칙 3: 페르소나를 안 골랐거나 목록에 없는 값이면 기본 페르소나
    if isinstance(persona, str) and persona.strip() in PERSONAS:
        return {"ok": True, "description": text, "persona": persona.strip(), "warning": None, "notice": None}
    return {"ok": True, "description": text, "persona": DEFAULT_PERSONA,
            "warning": None, "notice": DEFAULT_PERSONA_NOTICE}
