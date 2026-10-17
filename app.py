"""Streamlit 화면. 왼쪽 1/3: 입력 메뉴, 오른쪽 2/3: 결과(A/B 상자, 접힌 영역 채널 버전·CTR 가설).

꾸미는 부분(CSS·배너·띠)은 style.py에 있고, 이 파일은 화면 흐름만 다룬다.
"""

import streamlit as st

from generator import generate
from prompts import CHANNEL_LABELS, FRAMEWORK_SHORT, FRAMEWORKS, NO_PERSONA, PERSONAS
from style import CSS, band, banner_html, deco_html, empty_html, ribbon_divider

st.set_page_config(page_title="A/B 마케팅 문구 생성기", page_icon="✍️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(banner_html(), unsafe_allow_html=True)
st.markdown(ribbon_divider(), unsafe_allow_html=True)

left, right = st.columns([1, 2])

# 입력은 상품 설명·페르소나 두 개 + 세부 설정(프레임워크)
with left:
    with st.container(key="menu"):
        st.markdown(band("상품 정보 입력", "green", "chiicawa", "poong"), unsafe_allow_html=True)
        description = st.text_area(
            "상품 설명",
            placeholder="예: 수제 가죽 카드지갑, 슬림형, 카드 6장 수납, 2만원대",
        )
        persona = st.selectbox("타깃 페르소나", [NO_PERSONA] + PERSONAS)

        # 세부 설정은 기본으로 접어 둔다. (채널은 3개 모두 보여주므로 선택지 없음)
        with st.expander("세부 설정", expanded=False):
            framework = st.radio(
                "프레임워크",
                FRAMEWORKS,
                index=0,
                captions=[FRAMEWORK_SHORT[f] for f in FRAMEWORKS],
            )

        # 검사·AI 호출·오류 처리는 generate()가 모두 맡는다. (어떤 경우에도 예외 없이 결과만 돌려준다)
        # 결과는 화면이 다시 그려져도 남도록 session_state에 보관하고, 버튼을 누를 때마다 통째로 교체한다.
        clicked = st.button("카피 만들기", type="primary")

if clicked:
    with right:
        with st.spinner("문구를 만드는 중..."):
            st.session_state["output"] = generate(description, persona, framework)

with right:
    output = st.session_state.get("output")
    result = None
    if output:
        if output["warning"]:
            st.warning(output["warning"])
        if output["notice"]:
            st.info(output["notice"])
        result = output["result"]
    else:
        st.markdown(empty_html(), unsafe_allow_html=True)

    if result:
        st.caption("사용한 구조: {}".format(result["framework"]))
        # (키, 이름, 띠 색, 제목 옆 아이콘, 모서리 스티커)
        cards = (("a", "A안", "pink", "hachi", "sisa"), ("b", "B안", "green", "woosagi", "bam"))
        for key, name, color, icon_name, sticker_name in cards:
            with st.container(key="box_" + key):
                st.markdown(band(name, color, icon_name, sticker_name), unsafe_allow_html=True)
                st.markdown("**소구점**: {}".format(result[key]["angle"]))
                st.write(result[key]["copy"])

        # 채널별 버전: 글자 수를 보여주고, 넘으면 자르지 않고 경고만 한다
        st.markdown(ribbon_divider(), unsafe_allow_html=True)
        with st.expander("카톡·인스타·이메일 버전 보기"):
            st.markdown(band("채널 버전", "green", "kani"), unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            for col, (key, name, color, icon_name, _) in zip((col_a, col_b), cards):
                with col:
                    st.markdown(band(name, color, icon_name), unsafe_allow_html=True)
                    for c in result[key]["checks"]:
                        st.markdown("**{}**".format(CHANNEL_LABELS[c["key"]]))
                        st.write(c["text"])
                        st.caption("{}/{}자".format(c["length"], c["limit"]))
                        if c["excess"]:
                            st.warning("{} {}자 초과 ({}/{})".format(
                                CHANNEL_LABELS[c["key"]], c["excess"], c["length"], c["limit"]))

        with st.expander("왜 이렇게 나눴나요? (CTR 가설)"):
            st.markdown(band("CTR 가설", "pink", "laco"), unsafe_allow_html=True)
            st.markdown("**A안**: {}".format(result["a"]["hypothesis"]))
            st.markdown("**B안**: {}".format(result["b"]["hypothesis"]))

st.markdown(ribbon_divider(), unsafe_allow_html=True)

# 양옆 여백 장식(화면에 고정). 그림이 하나도 없으면 아무것도 그리지 않는다.
decoration = deco_html()
if decoration:
    st.markdown(decoration, unsafe_allow_html=True)
