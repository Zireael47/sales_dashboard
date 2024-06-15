import streamlit as st

from webapp.const import NAVBAR
from webapp.container import st_fixed_container

from util.read_file import read_file
from util.db import request_sql


def set_style(last_date):
    st.set_page_config(layout='wide', initial_sidebar_state="collapsed")
    hide_st = read_file('./webapp/styles/css/hide_streamlit.css')
    st.markdown(
        f"<style>{hide_st}</style>", unsafe_allow_html=True
    )
    with st_fixed_container():
        nav_cols = st.columns(len(NAVBAR)+2)
        with nav_cols[0]:
            st.image('./data/pics/logo_2.png',)
        with nav_cols[1]:
            st.write(
                f'<b>Последнее обновление:</b>  \n{last_date.split(" ")[0]}'
                f' {last_date.split(" ")[1]}',
                unsafe_allow_html=True
            )
        for i in range(2, len(NAVBAR)+2):
            with nav_cols[i]:
                for j in range(len(NAVBAR[i-2])):
                    st.page_link(**NAVBAR[i-2][j], use_container_width=True)
    st.markdown('')
    st.markdown('')


def setup(cfg):
    db_path = cfg["DBPath"]
    last_update = request_sql(db_path, "SELECT date FROM last_update")[0][0]
    last_update_month, last_update_year = last_update\
        .split(' ')[0].split('.')[1:]
    set_style(last_update)
    return db_path, last_update_month, last_update_year


def fetch_default_months(db_path):
    """Получение списка месяцев по умолчанию из базы данных."""
    query = """
        SELECT DISTINCT(month) FROM sales
        WHERE year = (SELECT MAX(year) FROM sales)
        AND type = 'Факт'
    """
    return [i[0] for i in request_sql(db_path, query)]


def fetch_report_types(db_path):
    "Получение списка типов отчетов из базы данных."
    query = "SELECT DISTINCT type, year FROM sales"
    types = [f"{i[0]} {i[1]}" for i in request_sql(db_path, query)]
    types.sort(reverse=True)
    return types


def subheader(text: str, header_ord: int):
    st.write(
        f"<h{header_ord}>{text}</h{header_ord}>",
        unsafe_allow_html=True
    )


def warning():
    st.warning('Выберите настройки отчета')
