"""세부 설정의 프레임워크 선택이 실제로 AI 요청(지시문)에 들어가는지 확인하는 테스트."""

import json

import pytest

import generator
from generator import generate
from prompts import FRAMEWORK_GUIDE, FRAMEWORK_SHORT, FRAMEWORKS, build_prompt

GOOD_DESC = "수제 가죽 카드지갑, 슬림형, 카드 6장 수납, 2만원대"

_CH = {"kakao": "k", "instagram": {"headline": "h", "body": "b"}, "email_subject": "e"}
FAKE_RESPONSE = json.dumps({
    "framework": "AIDA",
    "a": {"angle": "가격·혜택: x", "copy": "A 문구", "hypothesis": "가격을 보여주면 클릭률이 높아질 것이다.", "channels": _CH},
    "b": {"angle": "페인 포인트: y", "copy": "B 문구", "hypothesis": "공감하면 클릭률이 높아질 것이다.", "channels": _CH},
}, ensure_ascii=False)


@pytest.fixture
def sent(monkeypatch):
    """AI에게 실제로 보낸 (user, system) 지시문을 기록하는 가짜 ask_llm."""
    calls = []

    def fake(prompt, system=""):
        calls.append((prompt, system))
        return FAKE_RESPONSE

    monkeypatch.setattr(generator, "ask_llm", fake)
    return calls


def test_aida_guide_is_sent_to_ai_and_pas_is_not(sent):
    generate(GOOD_DESC, "품질 중심 직장인", "AIDA")
    prompt = sent[0][0]
    assert FRAMEWORK_GUIDE["AIDA"] in prompt
    assert FRAMEWORK_GUIDE["PAS"] not in prompt


def test_pas_guide_is_sent_to_ai_and_aida_is_not(sent):
    generate(GOOD_DESC, "품질 중심 직장인", "PAS")
    prompt = sent[0][0]
    assert FRAMEWORK_GUIDE["PAS"] in prompt
    assert FRAMEWORK_GUIDE["AIDA"] not in prompt


def test_auto_is_default_and_lets_ai_choose(sent):
    generate(GOOD_DESC, "품질 중심 직장인")  # 인자를 생략해도 "자동"
    generate(GOOD_DESC, "품질 중심 직장인", "자동")
    for prompt, _ in sent:
        assert FRAMEWORK_GUIDE["자동"] in prompt
        assert "AIDA" in prompt and "PAS" in prompt


def test_unknown_framework_falls_back_to_auto_without_error(sent):
    out = generate(GOOD_DESC, "품질 중심 직장인", "엉뚱한값")
    assert out["ok"] is True
    assert FRAMEWORK_GUIDE["자동"] in sent[0][0]


def test_build_prompt_puts_each_choice_under_writing_structure():
    for fw in FRAMEWORKS:
        _, user = build_prompt(GOOD_DESC, "가성비 중심 대학생", fw)
        assert FRAMEWORK_GUIDE[fw] in user


def test_chosen_framework_overrides_ai_reported_one(sent):
    # 가짜 AI는 항상 "AIDA"라고 답한다. PAS를 골랐으면 PAS로 표시되어야 한다.
    assert generate(GOOD_DESC, "품질 중심 직장인", "PAS")["result"]["framework"] == "PAS"
    assert generate(GOOD_DESC, "품질 중심 직장인", "자동")["result"]["framework"] == "AIDA"


def test_every_choice_has_screen_description():
    assert FRAMEWORKS[0] == "자동"  # 기본값은 맨 위
    for fw in FRAMEWORKS:
        assert FRAMEWORK_SHORT[fw].strip()
