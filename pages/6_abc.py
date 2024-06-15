from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

from st_aggrid import AgGrid, ColumnsAutoSizeMode, ExcelExportMode

from webapp.const import MONTH_DICT, JOINS
from webapp.util import setup, subheader
from util.config import build_config
from util.db import request_sql


# -----------------------------ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ-------------------------
def abc(x):
    """Присвоение категорий в abc-анализе"""
    if x < 80:
        return "A"
    elif x < 95:
        return "B"
    else:
        return "C"


def get_abc_data(
    db_path: str,
    category: str, subcategory: str, type_: str,
    dates: list, start: str, end: str
):
    """Получение данных для анализа ABC"""
    choose = "products.name" if subcategory != "НЭБ" else "products.code_ap"
    data = request_sql(
        db_path,
        f"""SELECT
            sales.year, sales.month,
            {choose} as name,
            SUM(sales.count) as 'Продажи, шт'
        {JOINS}
        WHERE categories.category = '{category}'
            AND products.subcategory = '{subcategory}'
            AND categories.type = '{type_}'
            AND sales.count > 0
            AND sales.type = 'Факт'
        GROUP BY sales.year, sales.month, {choose}""",
        headers=True
    )
    data = pd.pivot_table(
        data, 'Продажи, шт', 'name', ["year", "month"], "sum", 0
    )
    data.columns = list(
        data.columns.to_series().apply(
            lambda x: '{1}.{0}'.format(*x)
        ).reset_index()[0]
    )
    data.columns = [
        f"{MONTH_DICT[int(i.split('.')[0])]}.{i.split('.')[1]}"
        for i in data.columns
    ]
    # Фильтрация по дате, заполнение пустых продаж 0
    vals = dates[dates.index(start):dates.index(end)+1]
    for val in vals:
        if val not in data.columns:
            data[val] = 0
    data = data[vals].stack().reset_index()
    data.columns = ["Наименование", "Дата", "Продажи, шт"]
    return data


def abc_table(data: pd.DataFrame):
    """Создание сводной таблицы ABC"""
    pivot = pd.pivot_table(
        data=data,
        values="Продажи, шт",
        index="Наименование",
        aggfunc='sum', fill_value=0
    ).reset_index()
    pivot.sort_values(by='Продажи, шт', ascending=False, inplace=True)
    pivot = pivot[pivot['Продажи, шт'] > 0]
    pivot["%"] = round(pivot['Продажи, шт']/pivot['Продажи, шт'].sum()*100, 2)
    pivot["Категория"] = pivot["%"].cumsum().apply(lambda x: abc(x))
    return pivot


def abc_graph(data: pd.DataFrame, abc_table: pd.DataFrame):
    """Построение графика ABC"""
    data = pd.merge(
        data, abc_table[["Наименование", "Категория"]],
        'left', "Наименование"
    )
    data["date"] = data["Дата"].apply(
        lambda x: date(
            year=int(x.split('.')[1]),
            month=list(MONTH_DICT.values())
            .index((x.split('.')[0]))+1,
            day=1))
    data = pd.pivot_table(
        data, 'Продажи, шт', ["Дата", "date", "Категория",],
        aggfunc='sum', fill_value=0
    ).reset_index()
    data.sort_values(
        by=["date", "Категория", 'Продажи, шт'],
        ascending=[True, True, False],
        inplace=True
    )
    fig = px.bar(
        data,
        x="Дата", y="Продажи, шт", color="Категория",
    )
    fig.update_layout(title='Динамика продаж по категориям, шт', title_x=0.3)
    return fig


def get_dates_and_categories(db_path):
    """Получение доступных дат и категорий из базы данных"""
    dates = [
        f"{MONTH_DICT[el[1]]}.{el[0]}" for el in
        request_sql(
            db_path, "SELECT DISTINCT year, month FROM sales WHERE type='Факт'"
        )
    ]
    categories = [
        el[0] for el in
        request_sql(
            db_path,
            f"""SELECT DISTINCT categories.category
            {JOINS} ORDER BY categories.category"""
        )
    ]
    return dates, categories


def display_selections(
    dates, last_update_year, last_update_month,
    categories
):
    """Отображение выборов на странице"""
    col1, col2, col3, col4 = st.columns([3, 2, 1, 2], gap="medium")
    start, end = col1.select_slider(
        label="Выберите период для расчета:",
        options=dates,
        value=[
            f"Янв.{last_update_year}",
            f"{MONTH_DICT[int(last_update_month)]}.{last_update_year}"
        ]
    )
    category = col2.radio("Выберите категорию", categories, horizontal=True)
    types = [
        el[0] for el in
        request_sql(
            db_path,
            f"""SELECT DISTINCT categories.type
            {JOINS} WHERE categories.category ='{category}'"""
        )
    ]
    type_ = col3.radio("Выберите тип", types, horizontal=True)
    subcategories = [
        el[0] for el in
        request_sql(
            db_path,
            f"""SELECT DISTINCT products.subcategory {JOINS}
            WHERE categories.category = '{category}'
            AND categories.type = '{type_}'"""
        )
    ]
    subcategory = col4.radio(
        label="Выберите субкатегорию",
        options=subcategories, horizontal=True
    )
    return start, end, category, type_, subcategory


def display_abc_analysis(data):
    """Отображение таблицы и графика ABC анализа"""
    col5, col6 = st.columns([1, 1])
    with col5:
        subheader("Таблица. Категории и % продаж", 5)
    if len(data[data["Продажи, шт"] != 0]) > 0:
        pivot = abc_table(data)
        with col5:
            AgGrid(
                data=pivot,
                columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW, # noqa
                excel_export_mode=ExcelExportMode.MANUAL,
                height=350
            )
        col6.plotly_chart(abc_graph(data, pivot), use_container_width=True)
    else:
        col5.write('Нет продаж за выбранный период')


# -----------------------------КОД СТРАНИЦЫ------------------------------------
cfg = build_config('config.yaml')
db_path, last_update_month, last_update_year = setup(cfg)
st.header('ABC-анализ продаж по категориям')
dates, categories = get_dates_and_categories(db_path)
start, end, category, type_, subcategory = display_selections(
    dates,
    last_update_year, last_update_month,
    categories
)
data = get_abc_data(db_path, category, subcategory, type_, dates, start, end)
display_abc_analysis(data)
