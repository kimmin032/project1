"""양옆 장식 그림(style.deco_html): 그림이 없으면 조용히 빠지고, 있으면 들어가는지 확인한다.

실제 images/ 폴더는 건드리지 않고 IMAGE_DIR를 임시 폴더로 바꿔서 확인한다.
"""

import pytest

import style


@pytest.fixture
def images(tmp_path, monkeypatch):
    monkeypatch.setattr(style, "IMAGE_DIR", tmp_path)
    return tmp_path


def test_no_images_means_no_decoration_and_no_error(images):
    assert style.deco_html() == ""


def test_only_existing_images_are_used(images):
    (images / "star.png").write_bytes(b"\x89PNG fake")
    html = style.deco_html()
    assert html.count("<img") == 1 and "deco-left" in html
    assert "deco-right" not in html  # 오른쪽 그림(gab)이 없으면 오른쪽 칸은 만들지 않는다


def test_all_four_images_go_left_to_right_in_order(images):
    for name in ("star.png", "lion.jpg", "trio.jpg", "gab.png"):
        (images / name).write_bytes(b"fake")
    html = style.deco_html()
    assert html.count("<img") == 4
    left, right = html.split("deco-right")
    assert left.count("<img") == 3 and right.count("<img") == 1
    assert "deco-photo" in left  # lion·trio는 사진 카드


def test_double_extension_files_are_found(images):
    (images / "lion.jpg.jpg").write_bytes(b"fake")
    assert "data:image/jpeg;base64," in style.deco_html()


def test_decoration_is_hidden_on_narrow_screens_and_never_blocks_clicks():
    assert ".deco-side { display: none; }" in style.CSS
    assert "@media (min-width: 1560px)" in style.CSS
    assert "pointer-events: none" in style.CSS
    assert "position: fixed" in style.CSS
