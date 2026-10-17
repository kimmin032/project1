"""화면 꾸밈(2000년대 귀여운 핑크 개인 홈페이지 느낌)만 모아 둔 파일. 기능은 여기에 없다.

- HTML에는 고정 문구와 그림만 넣는다. AI가 쓴 글은 app.py에서 st.write/st.markdown으로만 출력한다.
- 그림은 images/ 폴더에서 읽는다. images/는 GitHub에 올리지 않으므로, 파일이 없거나 못 읽으면
  오류 없이 이모지로 대신 보여 준다.
"""

import base64
import io
from functools import lru_cache
from pathlib import Path

IMAGE_DIR = Path(__file__).parent / "images"
_EXTENSIONS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}

# 그림 이름 → 그림이 없을 때 대신 쓰는 이모지. 바꾸고 싶으면 여기만 고치면 된다.
EMOJI = {
    "chiicawa": "🐭",
    "hachi": "🐱",
    "woosagi": "🐰",
    "kani": "🌸",
    "laco": "🦦",
    "poong": "🐵",
    "sisa": "🦁",
    "bam": "🌰",
}
DEFAULT_EMOJI = "🎀"


def _shrink(data: bytes, mime: str, max_px: int) -> bytes:
    """그림이 max_px보다 크면 줄여서 화면으로 보내는 양을 아낀다. 못 줄이면 원본 그대로."""
    try:
        from PIL import Image  # streamlit이 함께 설치하는 패키지

        img = Image.open(io.BytesIO(data))
        if max(img.size) <= max_px:
            return data
        img.thumbnail((max_px, max_px))
        out = io.BytesIO()
        if mime == "image/png":
            img.save(out, "PNG", optimize=True)
        else:
            img.convert("RGB").save(out, "JPEG", quality=88)
        return out.getvalue()
    except Exception:
        return data


@lru_cache(maxsize=None)
def _encode(path: str, mime: str, max_px: int = 0) -> str:
    """그림 파일을 읽어 <img src>에 바로 넣을 수 있는 data URI로 바꾼다. (성공한 것만 기억해 둔다)"""
    with open(path, "rb") as f:
        data = f.read()
    if max_px:
        data = _shrink(data, mime, max_px)
    return "data:{};base64,{}".format(mime, base64.b64encode(data).decode("ascii"))


def _image_uri(name: str, max_px: int = 0):
    """images/<name>.png|jpg 의 data URI. 파일이 없거나 못 읽으면 None.

    lion.jpg.jpg 처럼 확장자가 겹쳐 저장된 파일도 찾는다.
    """
    for ext, mime in _EXTENSIONS.items():
        for filename in (name + ext, name + ext + ext):
            path = IMAGE_DIR / filename
            try:
                if path.is_file():
                    return _encode(str(path), mime, max_px)
            except Exception:  # 못 읽는 그림 때문에 화면 전체가 죽으면 안 된다
                continue
    return None


def icon(name: str, size: int = 48) -> str:
    """제목 옆에 붙이는 작은 아이콘."""
    uri = _image_uri(name, size * 3)
    if uri:
        return '<img class="cute-icon" src="{}" style="width:{}px;height:{}px" alt="">'.format(uri, size, size)
    return '<span class="cute-icon-emoji" style="font-size:{}px">{}</span>'.format(
        int(size * 0.85), EMOJI.get(name, DEFAULT_EMOJI))


def sticker(name: str, size: int = 100) -> str:
    """상자 모서리에 스티커처럼 걸쳐 붙이는 그림. 상자(position: relative)를 기준으로 자리를 잡는다."""
    uri = _image_uri(name, size * 3)
    if uri:
        return '<img class="cute-sticker" src="{}" style="width:{}px;height:{}px" alt="">'.format(uri, size, size)
    return '<span class="cute-sticker cute-sticker-emoji" style="font-size:{}px">{}</span>'.format(
        int(size * 0.8), EMOJI.get(name, DEFAULT_EMOJI))


def band(text: str, color: str, icon_name: str = None, sticker_name: str = None) -> str:
    """상자 위쪽 제목 띠. color는 "pink" 또는 "green". text는 고정 문구만 넣는다."""
    return '<div class="cute-band {}{}">{}<span>{}</span>{}</div>'.format(
        color,
        " has-sticker" if sticker_name else "",
        icon(icon_name) if icon_name else "",
        text,
        sticker(sticker_name) if sticker_name else "",
    )


def ribbon_divider() -> str:
    """점선 + 가운데 리본 구분선."""
    return '<div class="cute-ribbon"><span>🎀</span></div>'


def banner_html() -> str:
    """맨 위 배너. 그림은 자르지 않고 통째로 보여 주고(높이 자동), 제목은 그림 아래 띠에 둔다."""
    uri = _image_uri("banner")
    if uri:
        picture = '<img class="cute-banner-img" src="{}" alt="">'.format(uri)
    else:
        picture = '<div class="cute-banner-fallback">{}</div>'.format(
            " ".join(EMOJI[n] for n in ("hachi", "chiicawa", "woosagi", "kani", "laco")))
    return (
        '<div class="cute-banner">{}<div class="cute-banner-title">'
        "<h1>A/B 마케팅 문구 생성기</h1>"
        "<p>상품 설명과 타깃을 고르면 A안·B안 문구를 만들어 드려요 ♡</p>"
        "</div></div>"
    ).format(picture)


# 화면 양옆 여백의 장식 그림: (그림 이름, 모양). 위에서 아래로 쌓는다.
DECO_LEFT = (("star", "deco-plain"), ("lion", "deco-photo tilt-left"), ("trio", "deco-photo tilt-right"))
DECO_RIGHT = (("gab", "deco-plain deco-tall"),)
DECO_MAX_PX = {"gab": 720}  # 크게 보여 주는 그림은 원본 크기까지 보낸다. 나머지는 400px로 줄인다.


def deco_html() -> str:
    """양옆 여백에 고정해 두는 장식. 그림이 하나도 없으면 빈 글자를 돌려준다. (없는 그림은 그냥 건너뜀)

    화면이 좁으면 CSS가 통째로 숨긴다.
    """
    def side(css_class, items):
        imgs = []
        for name, shape in items:
            uri = _image_uri(name, DECO_MAX_PX.get(name, 400))
            if uri:
                imgs.append('<img class="{}" src="{}" alt="">'.format(shape, uri))
        return '<div class="deco-side {}">{}</div>'.format(css_class, "".join(imgs)) if imgs else ""

    return side("deco-left", DECO_LEFT) + side("deco-right", DECO_RIGHT)


def empty_html() -> str:
    return (
        '<div class="cute-empty">{}<br>왼쪽에 상품 정보를 넣고 버튼을 눌러 주세요</div>'
    ).format(icon("chiicawa", 48))


_STAR = (
    "%3Csvg xmlns='http://www.w3.org/2000/svg' width='90' height='90'%3E"
    "%3Ctext x='62' y='26' font-size='16' fill='%23c9e59a'%3E%E2%98%85%3C/text%3E"
    "%3Ctext x='12' y='72' font-size='11' fill='%23ffb8d4'%3E%E2%98%85%3C/text%3E"
    "%3C/svg%3E"
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Jua&display=swap');

:root {
  --pink: #ff6fa5; --pink-light: #ffd3e4; --pink-bg: #fff0f6;
  --green: #8cc152; --green-light: #d8f0b8; --green-dark: #4f8a1f;
  --cream: #fff8e1; --brown: #6b4a52;
}

/* 배경: 연분홍 체크무늬(깅엄) + 작은 별 */
.stApp {
  background-color: var(--pink-bg);
  background-image:
    url("data:image/svg+xml;utf8,__STAR__"),
    linear-gradient(90deg, rgba(255,170,205,.35) 50%, transparent 50%),
    linear-gradient(rgba(255,170,205,.35) 50%, transparent 50%);
  background-size: 90px 90px, 30px 30px, 30px 30px;
}
[data-testid="stHeader"] { background: transparent; }

/* 글씨: 본문은 Gowun Dodum, 제목은 Jua. (아이콘 글꼴은 건드리지 않는다) */
.stApp, .stApp p, .stApp label, .stApp li, .stApp textarea, .stApp input, .stApp button,
.stApp summary p, .stApp [data-baseweb="select"] div {
  font-family: 'Gowun Dodum', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
}
.stApp p, .stApp label, .stApp li, .stApp textarea { font-size: 1.25rem; color: var(--brown); }
.stApp [data-testid="stCaptionContainer"] p { font-size: 1.05rem; }
.stApp h1, .stApp h2, .stApp h3, .cute-band, .stApp summary p {
  font-family: 'Jua', 'Gowun Dodum', 'Malgun Gothic', sans-serif;
}

/* 페이지 전체를 감싸는 둥근 이중 테두리 액자 */
.block-container {
  max-width: 1200px; margin-top: 1rem; padding: 1.2rem 1.6rem 2rem;
  background: rgba(255, 248, 252, .88); border: 5px double #b7dd8a; border-radius: 18px;
}

/* 배너: 그림은 자르지 않고 통째로, 제목은 그림 아래 */
.cute-banner { border: 3px solid var(--pink-light); border-radius: 14px; background: #fff; overflow: hidden; }
.cute-banner-img { display: block; width: 100%; height: auto; }
.cute-banner-fallback { padding: 1rem; font-size: 3rem; text-align: center; background: linear-gradient(90deg, #ffd3e4, #fff8e1); }
.cute-banner-title { text-align: center; padding: .5rem 1rem .8rem; background: var(--cream); border-top: 3px dotted var(--pink-light); }
.cute-banner-title h1 {
  margin: 0; padding: 0; font-size: 2.3rem; color: var(--pink);
  text-shadow: 2px 2px 0 #fff, -2px -2px 0 #fff, 2px -2px 0 #fff, -2px 2px 0 #fff, 0 3px 0 var(--pink-light);
}
.cute-banner-title p { margin: .1rem 0 0; color: var(--brown); font-size: 1.15rem; }

/* 리본 구분선 */
.cute-ribbon { display: flex; align-items: center; gap: .6rem; margin: .8rem 0; }
.cute-ribbon::before, .cute-ribbon::after { content: ""; flex: 1; border-top: 3px dotted #ffa6c9; }
.cute-ribbon span { font-size: 1.5rem; }

/* 상자: 크림 바탕, 연두 이중 테두리, 둥근 모서리 (입력 패널 · A안 · B안) */
.st-key-menu, .st-key-box_a, .st-key-box_b {
  position: relative; background: var(--cream); border: 5px double var(--green); border-radius: 14px;
  padding: 0 0 14px; margin-top: 52px; /* 위쪽 52px은 스티커가 올라오는 자리 */
}
/* 가로 여백은 안쪽 요소가 갖는다. (제목 띠는 첫 요소라 여백 없이 상자 폭에 꼭 맞는다) */
.st-key-menu > [data-testid="stElementContainer"]:not(:first-child),
.st-key-box_a > [data-testid="stElementContainer"]:not(:first-child),
.st-key-box_b > [data-testid="stElementContainer"]:not(:first-child) { padding: 0 14px; }
.st-key-menu [data-testid="stElementContainer"], .st-key-menu [data-testid="stMarkdown"], .st-key-menu [data-testid="stMarkdownContainer"],
.st-key-box_a [data-testid="stElementContainer"], .st-key-box_a [data-testid="stMarkdown"], .st-key-box_a [data-testid="stMarkdownContainer"],
.st-key-box_b [data-testid="stElementContainer"], .st-key-box_b [data-testid="stMarkdown"], .st-key-box_b [data-testid="stMarkdownContainer"] { overflow: visible; }

/* 제목 띠: A안은 연분홍, 입력 패널·B안은 연두 (색만 다름) */
.cute-band {
  display: flex; align-items: center; gap: .6rem; box-sizing: border-box; min-height: 60px; margin: 0 0 .5rem; padding: .35rem .9rem;
  font-size: 1.4rem; border-radius: 9px 9px 0 0; border-bottom: 3px dotted rgba(255,255,255,.9);
}
.cute-band.has-sticker { padding-right: 112px; } /* 오른쪽 스티커(100px) 자리 */
.cute-band.pink { background: var(--pink-light); color: #d6407f; }
.cute-band.green { background: var(--green-light); color: var(--green-dark); }
.cute-icon { object-fit: contain; flex: none; }
.cute-icon-emoji { line-height: 1; flex: none; }

/* 스티커: 상자 오른쪽 위 모서리에 살짝 걸쳐 붙인다 */
.cute-sticker { position: absolute; top: -50px; right: 6px; transform: rotate(8deg); z-index: 5; pointer-events: none; object-fit: contain; }
.cute-sticker-emoji { line-height: 1; }

/* 입력 위젯 */
.st-key-menu [data-baseweb="textarea"], .st-key-menu [data-baseweb="select"] > div {
  background: #fff; border: 2px solid #b7dd8a !important; border-radius: 10px;
}
.st-key-menu button, .stButton button {
  width: 100%; font-family: 'Jua', 'Gowun Dodum', sans-serif; font-size: 1.2rem; color: #2f5d0f;
  background: linear-gradient(#d9f2b0, #8cc152); border: 2px solid var(--green-dark); border-radius: 999px;
}
.st-key-menu button:hover, .stButton button:hover {
  background: linear-gradient(#e6f8c8, #9ccf63); color: #2f5d0f; border-color: var(--green-dark);
}

/* 접는 영역(세부 설정 · 채널 버전 · CTR 가설)도 같은 상자 스타일 */
[data-testid="stExpander"] details {
  background: var(--cream); border: 5px double var(--green); border-radius: 14px; overflow: hidden;
}
[data-testid="stExpander"] summary { background: var(--green-light); }
[data-testid="stExpander"] summary:hover { background: #e6f8c8; }
[data-testid="stExpander"] summary p { color: var(--green-dark); font-size: 1.2rem; }
[data-testid="stExpander"] .cute-band { margin: 0 0 .5rem; border-radius: 9px; }
[data-testid="stExpander"] .cute-band.has-sticker { padding-right: .9rem; }

/* 양옆 여백의 장식 그림: 화면에 고정(스크롤해도 제자리), 가운데 내용 밖에만 놓는다. 좁으면 숨김 */
:root {
  --deco-w: clamp(140px, calc(50vw - 616px - 20px), 260px);
  --deco-w-right: clamp(150px, calc(50vw - 610px - 10px), 420px); /* gab은 여백을 거의 다 채울 만큼 크게 */
}
.deco-side { display: none; }
@media (min-width: 1560px) and (min-height: 650px) {
  .deco-side {
    display: flex; flex-direction: column; align-items: center; gap: 16px;
    position: fixed; top: 4.5rem; z-index: 0; pointer-events: none;
  }
  .deco-left { right: calc(50% + 616px); width: min(var(--deco-w), 170px); }
  .deco-right { left: calc(50% + 610px); width: var(--deco-w-right); }
  .deco-side img { display: block; width: 100%; height: auto; box-sizing: border-box; }
  .deco-plain { filter: drop-shadow(2px 3px 0 rgba(255, 150, 190, .35)); }
  .deco-tall { max-height: 88vh; object-fit: contain; object-position: top; }
  /* 사진 카드: 흰 테두리를 살짝 */
  .deco-photo { border: 7px solid #fff; border-radius: 6px; box-shadow: 0 3px 8px rgba(120, 60, 80, .28); }
  .tilt-left { transform: rotate(-2deg); }
  .tilt-right { transform: rotate(2deg); }
}

/* 결과가 없을 때 안내 */
.cute-empty {
  background: var(--cream); border: 3px dashed #ffa6c9; border-radius: 14px; padding: 2rem 1rem;
  text-align: center; font-family: 'Jua', 'Gowun Dodum', sans-serif; font-size: 1.3rem; color: var(--pink);
}
</style>
""".replace("__STAR__", _STAR)
