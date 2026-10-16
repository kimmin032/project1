"""AI에게 보낼 지시문(프롬프트)을 모아 둔 파일.

문구 스타일이나 규칙을 바꾸고 싶으면 이 파일만 고치면 된다.
"""

# 화면 드롭다운에 보여줄 페르소나 목록
PERSONAS = [
    "가성비 중심 대학생",
    "품질 중심 직장인",
    "트렌드 민감형 MZ",
]
DEFAULT_PERSONA = PERSONAS[0]

# 세부 설정의 프레임워크 선택지 ("자동"이면 AI가 골라 준다)
FRAMEWORKS = ["자동", "AIDA", "PAS"]

FRAMEWORK_GUIDE = {
    "AIDA": "AIDA = 주목(Attention) → 관심(Interest) → 욕구(Desire) → 행동(Action) 순서로 쓴다.",
    "PAS": "PAS = 문제(Problem) → 문제 키우기(Agitate) → 해결책(Solution) 순서로 쓴다.",
    "자동": "AIDA와 PAS 중 이 상품과 타깃에 더 잘 맞는 구조를 하나 골라 쓴다.",
}

SYSTEM_PROMPT = (
    "너는 소규모 쇼핑몰 셀러를 돕는 한국어 마케팅 카피라이터다. "
    "과장·허위 표현은 쓰지 않고, 상품 설명에 없는 사실(가격, 할인율, 수상 이력 등)은 지어내지 않는다. "
    "반드시 JSON만 출력하고, 코드블록(```)이나 설명 문장은 붙이지 않는다."
)

USER_TEMPLATE = """아래 상품을 타깃 페르소나에게 팔기 위한 A/B 테스트용 마케팅 문구를 만들어 줘.

[상품 설명]
{description}

[타깃 페르소나]
{persona}

[작성 구조]
{framework_guide}

[규칙]
- A안과 B안은 서로 다른 소구점(접근 각도)으로 쓴다. (예: A안은 가격 혜택, B안은 고민 공감)
- 각 안은 3~5문장, 한국어로 쓴다.
- 상품 설명에 없는 구체적 숫자나 사실은 만들지 않는다.

[출력 형식 - 이 JSON만 출력]
{{
  "framework": "사용한 구조 (AIDA 또는 PAS)",
  "a": {{"angle": "A안의 소구점 한 줄", "copy": "A안 문구"}},
  "b": {{"angle": "B안의 소구점 한 줄", "copy": "B안 문구"}}
}}"""


def build_prompt(description: str, persona: str, framework: str = "자동"):
    """(system, user) 지시문 두 개를 만들어 돌려준다."""
    guide = FRAMEWORK_GUIDE.get(framework, FRAMEWORK_GUIDE["자동"])
    user = USER_TEMPLATE.format(
        description=description.strip(),
        persona=persona.strip(),
        framework_guide=guide,
    )
    return SYSTEM_PROMPT, user
