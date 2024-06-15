import streamlit as st

from streamlit.components.v1 import html

from util.read_file import read_file

FIXED_CONTAINER_CSS = read_file('./webapp/styles/css/fixed_container.css')
FIXED_CONTAINER_JS = read_file('./webapp/styles/js/fixed_container.js')


def st_fixed_container(
    *,
    height: int | None = None,
    border: bool | None = None,
    transparent: bool = False,
):
    counter = 0
    fixed_container = st.container()
    non_fixed_container = st.container()
    with fixed_container:
        html(
            f"<script>{FIXED_CONTAINER_JS}</script>",
            scrolling=False, height=0
        )
        st.markdown(
            f"<style>{FIXED_CONTAINER_CSS}</style>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<div class='fixed-container-0'></div>",
            unsafe_allow_html=True,
        )
    with non_fixed_container:
        st.markdown(
            "<div class='not-fixed-container'></div>",
            unsafe_allow_html=True,
        )
    counter += 1
    if transparent:
        parent_container = fixed_container
    else:
        parent_container = fixed_container.container()
    return parent_container.container(height=height, border=border)
