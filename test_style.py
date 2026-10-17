"""화면 꾸밈(style.py)의 그림 불러오기: 그림이 없어도 오류 없이 이모지로 대신 나오는지 확인한다.

실제 images/ 폴더는 건드리지 않고, IMAGE_DIR를 임시 폴더로 바꿔서 확인한다.
"""

import pytest

import style


@pytest.fixture
def images(tmp_path, monkeypatch):
    monkeypatch.setattr(style, "IMAGE_DIR", tmp_path)
    return tmp_path


def test_missing_images_fall_back_to_emoji(images):
    assert "<img" not in style.icon("hachi")
    assert style.EMOJI["hachi"] in style.icon("hachi")
    assert style.EMOJI["sisa"] in style.sticker("sisa")
    assert "<img" not in style.banner_html()
    assert "A/B 마케팅 문구 생성기" in style.banner_html()  # 제목은 그림 없이도 나온다


def test_unknown_name_gets_default_emoji(images):
    assert style.DEFAULT_EMOJI in style.icon("없는이름")


def test_existing_image_becomes_inline_img_with_size(images):
    (images / "hachi.png").write_bytes(b"\x89PNG fake")
    html = style.icon("hachi", 32)
    assert 'src="data:image/png;base64,' in html
    assert "width:32px" in html
    assert 'class="cute-sticker"' in style.sticker("hachi", 70)
    assert "width:70px" in style.sticker("hachi", 70)


def test_banner_image_is_shown_whole(images):
    (images / "banner.jpg").write_bytes(b"\xff\xd8 fake")
    html = style.banner_html()
    assert 'src="data:image/jpeg;base64,' in html
    assert "cute-banner-img" in html
    # 그림을 고정 높이로 자르지 않는다 (제목 윗부분 잘림 방지)
    assert "height: auto" in style.CSS


def test_unreadable_image_does_not_raise(images):
    (images / "hachi.png").mkdir()  # 파일이 아니라 폴더 → 못 읽는 그림
    assert style.EMOJI["hachi"] in style.icon("hachi")


def test_band_has_color_icon_and_sticker(images):
    html = style.band("A안", "pink", "hachi", "sisa")
    assert "cute-band pink" in html and "A안" in html
    assert style.EMOJI["hachi"] in html and style.EMOJI["sisa"] in html
