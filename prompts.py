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
NO_PERSONA = "선택 안 함"  # 드롭다운 맨 위 항목. 고르면 기본 페르소나가 자동 적용된다.

# 채널별 글자 수 제한 - 숫자는 확인 후 여기 한 곳에서만 바꾸면 된다. (공백·줄바꿈 포함해서 센다)
CHANNEL_LIMITS = {
    "kakao_body": 400,      # 친구톡 이미지형 기준 400자 (텍스트형 최대 1,300자) - 카카오 비즈니스 가이드 확인
    "insta_headline": 30,   # 인스타 헤드라인 (임시값)
    "insta_body": 125,      # 인스타 본문: '더 보기' 전에 보이는 앞부분 기준
    "email_subject": 40,    # 이메일 제목: "(광고) " 접두어까지 포함한 글자 수 (임시값)
}

# 이메일은 광고성 메일이라 제목 맨 앞에 붙인다. (AI가 아니라 코드가 붙인다)
EMAIL_AD_PREFIX = "(광고) "

# 화면·경고에 보여줄 채널 이름
CHANNEL_LABELS = {
    "kakao_body": "카톡 본문",
    "insta_headline": "인스타 헤드라인",
    "insta_body": "인스타 본문",
    "email_subject": "이메일 제목",
}

# 세부 설정의 프레임워크 선택지 ("자동"이면 AI가 골라 준다)
FRAMEWORKS = ["자동", "AIDA", "PAS"]

FRAMEWORK_GUIDE = {
    "AIDA": "AIDA = 주목(Attention) → 관심(Interest) → 욕구(Desire) → 행동(Action) 순서로 쓴다.",
    "PAS": "PAS = 문제(Problem) → 문제 키우기(Agitate) → 해결책(Solution) 순서로 쓴다.",
    "자동": "AIDA와 PAS 중 이 상품과 타깃에 더 잘 맞는 구조를 하나 골라 쓴다.",
}

# 화면에서 선택지 옆에 보여줄 짧은 설명 (AI에게 가는 FRAMEWORK_GUIDE와는 별개)
FRAMEWORK_SHORT = {
    "자동": "상품과 타깃에 맞는 구조를 AI가 골라요",
    "AIDA": "주목 → 관심 → 욕구 → 행동",
    "PAS": "문제 → 자극 → 해결",
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
- 소구점은 고정한다.
  · A안: 가격·혜택 강조 (가성비, 합리적인 선택, 받을 수 있는 이점 중심)
  · B안: 페인 포인트 공감 (타깃이 겪는 불편·고민을 짚고 공감하는 중심)
- 두 안은 구조(작성 구조)와 길이, 톤, 문장 수는 비슷하게 맞춘다. 소구점만 다르게 한다.
- 각 안은 반드시 2~3문장으로 쓴다. (1문장은 안 되고, 4문장 이상도 안 된다)
- angle은 "가격·혜택: ..." / "페인 포인트: ..." 처럼 소구점 이름으로 시작해 한 줄로 쓴다.
- 설명이 짧아 쓸 특징이 적으면, 새 특징을 지어내지 말고 타깃의 상황·고민과 설명에 있는 특징(예: 수제, 가죽)만 활용한다. '안전', '세련', '튼튼', '편리' 같은 설명에 없는 장점 표현도 쓰지 않는다.
- 문구의 말투는 타깃 페르소나에 맞춘다. (예: 대학생은 친근하고 가볍게, 직장인은 단정하고 신뢰감 있게, MZ는 트렌디하고 짧게)
- 상품 설명에 적힌 특징만 쓴다. 설명에 없는 특징(내구성, 무게, 소재, 품질, 성능 등)이나 숫자, 가격, 할인율은 만들지 않는다.
- '최고', '최상', '1위', '완벽', '무조건' 같은 과장·최상급 표현은 쓰지 않는다.

[채널별 버전 규칙] 각 안의 문구를 아래 3개 채널용으로도 바꿔 쓴다. 소구점과 사실은 그대로 유지한다.
- 카카오 친구톡: 본문만, {kakao_max}자 이내.
- 인스타그램 피드: 헤드라인({insta_headline_max}자 이내) + 본문({insta_body_max}자 이내).
  피드에서는 '더 보기' 전의 앞부분만 보이므로 본문 첫 문장에 핵심(소구점)을 넣는다.
- 이메일 제목: 제목만, {email_max}자 이내. 맨 앞의 "(광고)"는 시스템이 붙이니 쓰지 않는다.
- 채널 문구(카톡 본문, 인스타 헤드라인·본문, 이메일 제목)에는 "가격·혜택:", "페인 포인트:" 같은 소구점 이름을 쓰지 않는다. 소구점은 이름 없이 문장 안에 자연스럽게 녹인다.
- 글자 수는 공백을 포함해서 세고, 한도를 넘지 않게 쓴다.

[CTR 가설 규칙]
- 각 안이 어떤 클릭률(CTR) 가설을 검증하는지 "…하면 클릭률이 …할 것이다" 형태의 한 문장으로 쓴다. 예: "가격 혜택을 먼저 보여주면 클릭률이 높아질 것이다."
- 화면에서 "A안:" / "B안:"이 앞에 따로 붙으니, 문장에 "A안", "B안", "CTR 가설은" 같은 머리말을 쓰지 않는다.
- 구체적인 % 수치나 성과 숫자는 쓰지 않는다.

[출력 형식 - 이 JSON만 출력]
{{
  "framework": "사용한 구조 (AIDA 또는 PAS)",
  "a": {{
    "angle": "가격·혜택 강조 (구체적으로 한 줄)",
    "copy": "A안 문구",
    "hypothesis": "A안이 검증하는 CTR 가설 한 문장 (머리말 없이)",
    "channels": {{
      "kakao": "친구톡 본문",
      "instagram": {{"headline": "인스타 헤드라인", "body": "인스타 본문"}},
      "email_subject": "이메일 제목 ((광고) 제외)"
    }}
  }},
  "b": {{
    "angle": "페인 포인트 공감 (구체적으로 한 줄)",
    "copy": "B안 문구",
    "hypothesis": "B안이 검증하는 CTR 가설 한 문장 (머리말 없이)",
    "channels": {{
      "kakao": "친구톡 본문",
      "instagram": {{"headline": "인스타 헤드라인", "body": "인스타 본문"}},
      "email_subject": "이메일 제목 ((광고) 제외)"
    }}
  }}
}}"""


def build_prompt(description: str, persona: str, framework: str = "자동"):
    """(system, user) 지시문 두 개를 만들어 돌려준다."""
    guide = FRAMEWORK_GUIDE.get(framework, FRAMEWORK_GUIDE["자동"])
    user = USER_TEMPLATE.format(
        description=description.strip(),
        persona=persona.strip(),
        framework_guide=guide,
        kakao_max=CHANNEL_LIMITS["kakao_body"],
        insta_headline_max=CHANNEL_LIMITS["insta_headline"],
        insta_body_max=CHANNEL_LIMITS["insta_body"],
        # AI가 쓰는 제목은 "(광고) "를 뺀 나머지 부분의 한도
        email_max=CHANNEL_LIMITS["email_subject"] - len(EMAIL_AD_PREFIX),
    )
    return SYSTEM_PROMPT, user
