
import pandas as pd
import plotly.express as px
import streamlit as st

from st_aggrid import AgGrid, ColumnsAutoSizeMode, ExcelExportMode

from util.db import request_sql
from util.config import build_config
from webapp.const import ALL_COLS, JOINS, SHOW_COLUMNS_MONTH
from webapp.util import setup, fetch_default_months, fetch_report_types
from util.db import get_sql_list


# -----------------------------ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ-------------------------
def get_filters(db_path: str):
    "Функция для получения и отображения фильтров"
    filters = st.multiselect("Выберите фильтры", ALL_COLS)
    dict_filters = {}
    for i in range(len(filters)):
        filter_str = get_filter_query(filters, dict_filters)
        query = f"""SELECT DISTINCT {ALL_COLS[filters[i]]}
                    {JOINS} {filter_str}"""
        dict_filters[f"filter_{i}"] = st.multiselect(
            f"Выберите значение для поля {filters[i]}",
            [i[0] for i in request_sql(db_path, query)]
        )
    return dict_filters, filters


def get_filter_query(filters: list, dict_values: dict) -> str:
    filter_query_str = ""
    for i in range(len(dict_values)):
        if i == 0:
            filter_query_str += "WHERE"
        else:
            filter_query_str += "AND"
        filter_query_str += f"""
            {ALL_COLS[filters[i]]} in (
                {get_sql_list(dict_values[f"filter_{i}"], is_string=True)})
            """
    return filter_query_str


def display_chart(data: pd.DataFrame, type_: str, title: str):
    fig = px.line(
                data,
                x='Месяц', y=type_, color="Тип", markers=True,
                height=300
            )
    fig.update_layout(title=title, title_x=0.3)
    fig.update_xaxes(tickvals=[i for i in range(1, 13)], tickmode='linear')
    return fig


def display_table(data):
    data = data.set_index(["Тип", 'Месяц']).stack().reset_index()
    data.columns = ["Тип", 'Месяц', "Показатель", "Значение"]
    data = pd.pivot_table(
        data=data,
        values="Значение",
        index=["Показатель", 'Тип'],
        columns="Месяц",
        aggfunc='sum',
        fill_value=0,
        margins=True
    ).reset_index()
    data = data.iloc[:-1, :]
    data.columns = [str(i) for i in data.columns[:-1]] + ["Итого"]
    st.write("<h5>Таблица. Динамика продаж</h5>", unsafe_allow_html=True)
    AgGrid(
        data,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        excel_export_mode=ExcelExportMode.MANUAL,
    )


# -----------------------------КОД СТРАНИЦЫ------------------------------------
cfg = build_config('config.yaml')
db_path, last_update_month, last_update_year = setup(cfg)
default_monthes = fetch_default_months(db_path)
types = fetch_report_types(db_path)

header_cols = st.columns([2, 6])
header_cols[0].header('Динамика продаж')
st.write(
    "<i style='color:gray'>Выбор фильтров можно оставить пустым</i>",
    unsafe_allow_html=True
)
header_cols[1].write('')
ch_types = st.multiselect(
    label="Выберите тип отчета", options=types, default=SHOW_COLUMNS_MONTH)

# Отображение фильтров
columns = st.columns([2, 3, 3], gap="small")
with columns[0]:
    dict_filters, filters = get_filters(db_path)
if any([True if len(i) == 0 else False for i in dict_filters.values()]):
    columns[0].warning("Выберите значения для фильтров!")
else:
    filter_query_str = get_filter_query(filters, dict_filters)
    query = f"""SELECT
                sales.year, sales.type, sales.month,
                CAST(SUM(count) AS INTEGER) as 'Количество',
                CAST(SUM(revenue) AS INTEGER) as 'Выручка, руб б/НДС'
            {JOINS} {filter_query_str}
            GROUP BY sales.year, sales.type, sales.month"""
    # Отображение таблиц
    data = request_sql(db_path, query, headers=True)
    data.set_index(["type", "year"], inplace=True)
    data.index = [' '.join(map(str, i)) for i in data.index.tolist()]
    data.reset_index(inplace=True)
    data.columns = ["Тип", "Месяц", 'Кол-во', 'Выручка, руб б/НДС']
    data = data[data["Тип"].isin(ch_types)]
    # Графики
    columns[1].plotly_chart(
        display_chart(
            data,
            "Кол-во", 'Динамика продаж, кол-во'),
        use_container_width=True)
    columns[2].plotly_chart(
        display_chart(
            data,
            "Выручка, руб б/НДС", 'Динамика продаж, руб б/НДС'),
        use_container_width=True)
    display_table(data)
