"""Streamlit 화면. 위에서 아래로: 입력 → 버튼 → 경고 → A/B 카드 → 접힌 영역(채널 버전, CTR 가설)."""

import streamlit as st

from generator import make_copy
from llm_client import LLMError
from prompts import CHANNEL_LABELS, PERSONAS

st.set_page_config(page_title="A/B 마케팅 문구 생성기", page_icon="✍️")
st.title("✍️ A/B 마케팅 문구 생성기")
st.caption("상품 설명과 타깃을 고르면 A안·B안 문구를 만들어 드려요.")

# 입력은 두 개만
description = st.text_area(
    "상품 설명",
    placeholder="예: 수제 가죽 카드지갑, 슬림형, 카드 6장 수납, 2만원대",
)
persona = st.selectbox("타깃 페르소나", PERSONAS)

# 한 번 만든 결과는 화면이 다시 그려져도 남도록 session_state에 보관
if st.button("카피 만들기", type="primary"):
    if not description.strip():
        st.session_state.pop("result", None)
        st.warning("상품 설명을 입력해 주세요.")
    else:
        try:
            with st.spinner("문구를 만드는 중..."):
                st.session_state["result"] = make_copy(description, persona)
        except LLMError as e:  # 메시지에는 API 키가 들어 있지 않다
            st.session_state.pop("result", None)
            st.warning(str(e))

result = st.session_state.get("result")
if result:
    st.caption("사용한 구조: {}".format(result["framework"]))
    col_a, col_b = st.columns(2)
    for col, key, name in ((col_a, "a", "A안"), (col_b, "b", "B안")):
        with col:
            with st.container(border=True):
                st.subheader(name)
                st.markdown("**소구점**: {}".format(result[key]["angle"]))
                st.write(result[key]["copy"])

    # 채널별 버전: 글자 수를 보여주고, 넘으면 자르지 않고 경고만 한다
    with st.expander("카톡·인스타·이메일 버전 보기"):
        col_a, col_b = st.columns(2)
        for col, key, name in ((col_a, "a", "A안"), (col_b, "b", "B안")):
            with col:
                st.markdown("### {}".format(name))
                for c in result[key]["checks"]:
                    st.markdown("**{}**".format(CHANNEL_LABELS[c["key"]]))
                    st.write(c["text"])
                    st.caption("{}/{}자".format(c["length"], c["limit"]))
                    if c["excess"]:
                        st.warning("{} {}자 초과 ({}/{})".format(
                            CHANNEL_LABELS[c["key"]], c["excess"], c["length"], c["limit"]))

    with st.expander("왜 이렇게 나눴나요? (CTR 가설)"):
        st.markdown("**A안**: {}".format(result["a"]["hypothesis"]))
        st.markdown("**B안**: {}".format(result["b"]["hypothesis"]))
