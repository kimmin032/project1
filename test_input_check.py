"""입력 검증(기능 ③) 테스트. 실행: pytest -v

규칙 표의 각 줄이 테스트 하나(또는 한 묶음)에 대응한다.
AI는 실제로 부르지 않고, 가짜 ask_llm으로 바꿔서 '몇 번 불렸는지'만 확인한다.
"""

import json

import pytest

import generator
from generator import _clean_hypothesis, generate
from input_check import check_input
from llm_client import LLMError
from prompts import DEFAULT_PERSONA, NO_PERSONA, PERSONAS

EMPTY_WARNING = "상품 설명을 입력해 주세요."
GOOD_DESC = "수제 가죽 카드지갑, 슬림형, 카드 6장 수납, 2만원대"


# ---------- 규칙 1: 5자 미만(공백 빼고) → 재입력 안내 ----------
@pytest.mark.parametrize("desc", ["옷팝니다", "옷 팝 니 다", "  옷팝니다  "])
def test_rule1_too_short_is_rejected_with_help(desc):
    out = check_input(desc, PERSONAS[0])
    assert out["ok"] is False
    assert "특징·가격을 더 적어 주세요" in out["warning"]
    assert "예:" in out["warning"]  # 입력 예시 포함


def test_rule1_boundary_five_chars_passes():
    assert check_input("수제카드집", PERSONAS[0])["ok"] is True  # 정확히 5자


# ---------- 규칙 2: 비었음 → 경고 한 줄 ----------
@pytest.mark.parametrize("desc", ["", "   ", "\n\t", None])
def test_rule2_empty_gives_one_line_warning(desc):
    out = check_input(desc, PERSONAS[0])
    assert out["ok"] is False
    assert out["warning"] == EMPTY_WARNING


# ---------- 규칙 3: 페르소나 '선택 안 함' → 기본 페르소나 + 안내 ----------
@pytest.mark.parametrize("persona", [NO_PERSONA, None, "", "목록에 없는 값"])
def test_rule3_no_persona_applies_default_with_notice(persona):
    out = check_input(GOOD_DESC, persona)
    assert out["ok"] is True
    assert out["persona"] == DEFAULT_PERSONA == "가성비 중심 대학생"
    assert "기본 페르소나를 적용했어요" in out["notice"]


def test_rule3_chosen_persona_is_kept_without_notice():
    out = check_input(GOOD_DESC, "품질 중심 직장인")
    assert out["persona"] == "품질 중심 직장인"
    assert out["notice"] is None


def test_rule3_dropdown_has_no_persona_option():
    assert NO_PERSONA == "선택 안 함"
    assert NO_PERSONA not in PERSONAS  # 기본 페르소나가 실제 목록과 섞이지 않게


# ---------- 규칙 4: 특수문자·숫자만 → 규칙 1과 같은 안내 ----------
@pytest.mark.parametrize("desc", ["!!!!!", "12345", "1234 5678", "!@#$%", "..."])
def test_rule4_symbols_or_digits_only_same_message_as_rule1(desc):
    out = check_input(desc, PERSONAS[0])
    assert out["ok"] is False
    assert out["warning"] == check_input("옷팝니다", PERSONAS[0])["warning"]


# ---------- 길이는 한글·영문 글자만 센다 (숫자·특수문자로 5자를 채울 수 없다) ----------
@pytest.mark.parametrize("desc", ["옷팝니다!!!12345", "옷팝니다 12345", "옷팝니다!!!!!", "카드지갑12", "a1b2c3!!"])
def test_length_counts_only_letters_so_padding_is_rejected(desc):
    out = check_input(desc, PERSONAS[0])
    assert out["ok"] is False
    assert out["warning"] == check_input("옷팝니다", PERSONAS[0])["warning"]  # 규칙 1과 같은 안내


@pytest.mark.parametrize("desc", [
    "수제 가죽 카드지갑, 2만원대",   # 글자 11자 + 숫자
    "슬림형 6장 2만원",              # 글자 6자 + 숫자
    "카드지갑들12",                  # 글자 정확히 5자 + 숫자
    "iPhone 15 케이스",              # 영문·한글 섞임
])
def test_length_counts_only_letters_but_numbers_in_good_text_pass(desc):
    out = check_input(desc, PERSONAS[0])
    assert out["ok"] is True
    assert out["warning"] is None


def test_generate_does_not_call_ai_for_padded_short_input(fake_llm):
    out = generate("옷팝니다!!!12345", NO_PERSONA)
    assert fake_llm == []  # AI 0회 호출
    assert out["ok"] is False


def test_valid_description_passes():
    out = check_input(GOOD_DESC, PERSONAS[0])
    assert out["ok"] is True
    assert out["warning"] is None
    assert out["description"] == GOOD_DESC


def test_rejected_input_has_no_persona_notice():
    # 생성하지 않을 거면 페르소나 안내도 필요 없다
    assert check_input("옷팝니다", NO_PERSONA)["notice"] is None


# ---------- 어떤 경우에도 멈추지 않는다 ----------
@pytest.mark.parametrize("desc", [None, 123, 3.5, [], {}, "\n"])
@pytest.mark.parametrize("persona", [None, 123, [], NO_PERSONA])
def test_check_input_never_raises_on_weird_values(desc, persona):
    out = check_input(desc, persona)
    assert out["ok"] is False
    assert out["warning"]


# ---------- generate(): AI 호출 여부와 예외 흡수 ----------
FAKE_RESPONSE = json.dumps({
    "framework": "AIDA",
    "a": {"angle": "가격·혜택: x", "copy": "A 문구", "hypothesis": "가격 혜택을 보여주면 클릭률이 높아질 것이다.",
          "channels": {"kakao": "k", "instagram": {"headline": "h", "body": "b"}, "email_subject": "e"}},
    "b": {"angle": "페인 포인트: y", "copy": "B 문구", "hypothesis": "불편에 공감하면 클릭률이 높아질 것이다.",
          "channels": {"kakao": "k", "instagram": {"headline": "h", "body": "b"}, "email_subject": "e"}},
}, ensure_ascii=False)


@pytest.fixture
def fake_llm(monkeypatch):
    """가짜 ask_llm: 불린 횟수와 프롬프트를 기록한다."""
    calls = []

    def fake(prompt, system=""):
        calls.append(prompt)
        return FAKE_RESPONSE

    monkeypatch.setattr(generator, "ask_llm", fake)
    return calls


@pytest.mark.parametrize("desc", ["", "   ", None, "옷팝니다", "!!!!!", "12345"])
def test_generate_does_not_call_ai_for_bad_input(fake_llm, desc):
    out = generate(desc, NO_PERSONA)
    assert fake_llm == []  # AI 0회 호출
    assert out["ok"] is False
    assert out["result"] is None
    assert out["warning"]


def test_generate_calls_ai_for_good_input(fake_llm):
    out = generate(GOOD_DESC, "품질 중심 직장인")
    assert len(fake_llm) == 1
    assert out["ok"] is True
    assert out["result"]["a"]["copy"] == "A 문구"
    assert out["notice"] is None
    assert "품질 중심 직장인" in fake_llm[0]


def test_generate_uses_default_persona_when_not_chosen(fake_llm):
    out = generate(GOOD_DESC, NO_PERSONA)
    assert out["ok"] is True
    assert "기본 페르소나를 적용했어요" in out["notice"]
    assert DEFAULT_PERSONA in fake_llm[0]
    assert NO_PERSONA not in fake_llm[0]  # '선택 안 함'이라는 글자가 AI에게 가면 안 된다


def test_generate_turns_llm_error_into_warning(monkeypatch):
    def boom(prompt, system=""):
        raise LLMError("AI 서버에 연결하지 못했습니다.")

    monkeypatch.setattr(generator, "ask_llm", boom)
    out = generate(GOOD_DESC, PERSONAS[0])
    assert out["ok"] is False
    assert out["warning"] == "AI 서버에 연결하지 못했습니다."


def test_generate_hides_unexpected_error_details(monkeypatch):
    def boom(prompt, system=""):
        raise RuntimeError("secret-detail-xyz")

    monkeypatch.setattr(generator, "ask_llm", boom)
    out = generate(GOOD_DESC, PERSONAS[0])  # 예외가 밖으로 나오면 여기서 테스트 실패
    assert out["ok"] is False
    assert "알 수 없는 오류" in out["warning"]
    assert "secret-detail-xyz" not in out["warning"]


def test_generate_survives_non_json_answer(monkeypatch):
    monkeypatch.setattr(generator, "ask_llm", lambda prompt, system="": "죄송합니다, 못 하겠어요")
    out = generate(GOOD_DESC, PERSONAS[0])
    assert out["ok"] is False
    assert out["warning"]


# ---------- 덤: CTR 가설 머리말 겹침 제거 ----------
@pytest.mark.parametrize("raw, expected", [
    ("A안은 가격 혜택을 먼저 보여주면 클릭률이 높아질 것이다.", "가격 혜택을 먼저 보여주면 클릭률이 높아질 것이다."),
    ("B안이 검증하는 CTR 가설은 불편에 공감하면 클릭률이 높아질 것이다.", "불편에 공감하면 클릭률이 높아질 것이다."),
    ("A안: 가격 혜택을 보여주면 클릭률이 높아질 것이다.", "가격 혜택을 보여주면 클릭률이 높아질 것이다."),
    ("CTR 가설: 공감 문구가 클릭률을 높일 것이다.", "공감 문구가 클릭률을 높일 것이다."),
    ("가격 혜택을 먼저 보여주면 클릭률이 높아질 것이다.", "가격 혜택을 먼저 보여주면 클릭률이 높아질 것이다."),
])
def test_clean_hypothesis_removes_duplicate_prefix(raw, expected):
    assert _clean_hypothesis(raw) == expected
