"""채널 문구 앞에 붙은 소구점 이름("가격·혜택:", "페인 포인트:")을 막고, 붙어 있으면 지우는지 확인하는 테스트."""

import json

import pytest

import generator
from generator import _strip_angle_label, generate
from prompts import build_prompt

GOOD_DESC = "수제 가죽 카드지갑, 슬림형, 카드 6장 수납, 2만원대"


# ---------- 지시문에 규칙이 들어가는가 ----------
def test_prompt_forbids_angle_names_in_channel_texts():
    _, user = build_prompt(GOOD_DESC, "가성비 중심 대학생")
    rule = user.split("[채널별 버전 규칙]")[1].split("[CTR 가설 규칙]")[0]
    assert "가격·혜택:" in rule and "페인 포인트:" in rule
    assert "쓰지 않는다" in rule


# ---------- 앞머리 지우기 ----------
@pytest.mark.parametrize("raw, expected", [
    ("가격·혜택: 슬림한 카드지갑", "슬림한 카드지갑"),
    ("페인 포인트: 주머니 속 불편함 해결", "주머니 속 불편함 해결"),
    ("가격·혜택：슬림한 카드지갑", "슬림한 카드지갑"),          # 전각 콜론
    ("  가격·혜택 :   슬림한 카드지갑", "슬림한 카드지갑"),      # 공백
    ("[페인 포인트] - 두꺼운 지갑", "두꺼운 지갑"),
    ("가격·혜택 강조: 슬림한 카드지갑", "슬림한 카드지갑"),
    ("페인 포인트 공감: 두꺼운 지갑", "두꺼운 지갑"),
    ("가격/혜택: 슬림한 카드지갑", "슬림한 카드지갑"),
    ("가격·혜택: 페인 포인트: 둘 다 붙음", "둘 다 붙음"),       # 겹쳐 붙어도 모두 지움
])
def test_strip_removes_leading_angle_name(raw, expected):
    assert _strip_angle_label(raw) == expected


@pytest.mark.parametrize("text", [
    "슬림한 카드지갑, 2만원대",
    "가격이 부담되셨나요? 혜택을 드려요",
    "페인 포인트를 짚어 드려요",            # 구분 기호가 없으면 일반 문장이라 그대로 둔다
    "카드 6장 수납 (가격·혜택: 2만원대)",    # 앞머리가 아닌 곳은 건드리지 않는다
])
def test_strip_leaves_normal_text_alone(text):
    assert _strip_angle_label(text) == text


def test_strip_never_returns_empty():
    assert _strip_angle_label("가격·혜택:") == "가격·혜택:"


# ---------- 전체 흐름: 4개 채널 문구 모두에서 지워지는가 ----------
def _response(prefix_a, prefix_b, ad=""):
    def variant(angle, copy, prefix):
        return {
            "angle": angle, "copy": copy, "hypothesis": "공감하면 클릭률이 높아질 것이다.",
            "channels": {
                "kakao": prefix + "카톡 본문",
                "instagram": {"headline": prefix + "헤드라인", "body": prefix + "인스타 본문"},
                "email_subject": ad + prefix + "메일 제목",
            },
        }
    return json.dumps({
        "framework": "AIDA",
        "a": variant("가격·혜택: 합리적인 가격", "A 문구", prefix_a),
        "b": variant("페인 포인트: 두꺼운 지갑", "B 문구", prefix_b),
    }, ensure_ascii=False)


def _run(monkeypatch, response):
    monkeypatch.setattr(generator, "ask_llm", lambda prompt, system="": response)
    out = generate(GOOD_DESC, "가성비 중심 대학생")
    assert out["ok"] is True
    return out["result"]


def test_all_four_channel_texts_are_cleaned(monkeypatch):
    r = _run(monkeypatch, _response("가격·혜택: ", "페인 포인트: "))
    for key in ("a", "b"):
        ch = r[key]["channels"]
        assert ch["kakao"] == "카톡 본문"
        assert ch["instagram"] == {"headline": "헤드라인", "body": "인스타 본문"}
        assert ch["email_subject"] == "(광고) 메일 제목"
        assert [c["text"] for c in r[key]["checks"]] == ["카톡 본문", "헤드라인", "인스타 본문", "(광고) 메일 제목"]


def test_angle_names_stay_in_angle_field(monkeypatch):
    r = _run(monkeypatch, _response("가격·혜택: ", "페인 포인트: "))
    assert r["a"]["angle"] == "가격·혜택: 합리적인 가격"   # 소구점 칸에는 이름이 남아야 한다
    assert r["b"]["angle"] == "페인 포인트: 두꺼운 지갑"
    assert r["a"]["copy"] == "A 문구"


def test_label_after_ad_prefix_in_email_subject_is_cleaned(monkeypatch):
    r = _run(monkeypatch, _response("가격·혜택: ", "페인 포인트: ", ad="(광고) "))
    assert r["a"]["channels"]["email_subject"] == "(광고) 메일 제목"  # (광고)가 두 번 붙지도 않는다
    assert r["b"]["channels"]["email_subject"] == "(광고) 메일 제목"


def test_lengths_are_counted_after_cleaning(monkeypatch):
    r = _run(monkeypatch, _response("가격·혜택: ", "페인 포인트: "))
    headline = next(c for c in r["a"]["checks"] if c["key"] == "insta_headline")
    assert headline["length"] == len("헤드라인")
