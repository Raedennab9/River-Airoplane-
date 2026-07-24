"""Streamlit shell for the browser edition of Air Combat: River Run."""

import streamlit as st


GAME_URL = "https://raedennab9.github.io/River-Airoplane-/"

st.set_page_config(
    page_title="Air Combat: River Run",
    page_icon="✈️",
    layout="wide",
)

st.title("✈️ Air Combat: River Run")
st.caption("Click inside the game once to enable keyboard controls and sound.")

st.markdown(
    f"""
    <div style="display:flex;justify-content:center;width:100%;">
      <iframe
        src="{GAME_URL}"
        title="Air Combat: River Run"
        width="900"
        height="760"
        style="max-width:100%;border:0;border-radius:12px;background:#101820;"
        allow="autoplay; fullscreen"
        allowfullscreen>
      </iframe>
    </div>
    """,
    unsafe_allow_html=True,
)

st.link_button("Open game in a separate tab", GAME_URL, use_container_width=True)
