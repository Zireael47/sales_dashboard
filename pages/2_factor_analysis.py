import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from webapp.const import JOINS, LIST_FORMAT
from webapp.util import subheader, warning
from webapp.util import setup, fetch_default_months, fetch_report_types

from util.db import request_sql, get_sql_list
from util.config import build_config


# -----------------------------ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ-------------------------

def fetch_categories(db_path):
    """Получение списка категорий из базы данных."""
    query = """
        SELECT DISTINCT(category) FROM categories
        WHERE category <> 'Прочее'
    """
    return ['Все'] + [i[0] for i in request_sql(db_path, query)]


def get_data(db_path, types, monthes, category):
    """Получение данных на основе выбранных типов, месяцев и категорий."""
    monthes_str = f"""WHERE sales.month in ({get_sql_list(monthes)})"""\
        if monthes[0] != 'Все' else ''
    category_str = f"categories.category='{category[0]}'"\
        if category[0] != 'Все' else ''
    if category_str and monthes_str:
        category_str = "AND " + category_str
    elif category_str:
        category_str = "WHERE " + category_str
    query = f"""
        SELECT
            sales.year, sales.type, categories.category,
            products.subcategory, products.unit,
            CAST(SUM(count) AS INTEGER) as 'Количество',
            CAST(SUM(revenue) AS INTEGER) as 'Выручка, руб б/НДС'
        {JOINS} {monthes_str} {category_str}
        GROUP BY sales.year, sales.type, categories.category,
        products.subcategory, products.unit
    """
    data = request_sql(db_path, query, headers=True)
    data.set_index(["type", "year"], inplace=True)
    data.index = [' '.join(map(str, i)) for i in data.index.tolist()]
    data.reset_index(inplace=True)
    data.columns = [
        "Тип", 'Категория', "Субкатегория",
        "Ед.изм.", 'Кол-во', "Выручка"
    ]
    data = data[data["Тип"].isin(types)]
    data = pd.pivot_table(
        data, values=['Кол-во', "Выручка"],
        index=['Категория', "Субкатегория", "Ед.изм."],
        columns="Тип", aggfunc='sum', fill_value=0
    )
    data.columns = list(
        data.columns.to_series()
            .apply(lambda x: '{0} {1}'.format(*x)).reset_index()[0]
    )
    data.reset_index(inplace=True)
    data["Тип"] = 0
    return data


def get_types(data, types):
    """Классификация данных на разные типы на основе условий."""
    cnt_old, cnt_new = f'Кол-во {types[0]}', f'Кол-во {types[1]}'
    rev_old, rev_new = f'Выручка {types[0]}', f'Выручка {types[1]}'
    for i in range(len(data)):
        type_ = "Исключение" if (
            data.loc[i, 'Ед.изм.'] == 'комплект' or
            data.loc[i, 'Категория'] == 'Прочее'
        ) else "Вывод" if data.loc[i, rev_new] == 0 else "Лонч" if (
            data.loc[i, rev_new] > 0 and data.loc[i, rev_old] == 0
        ) else "Current"
        data.loc[i, 'Тип'] = type_

    pivot = pd.pivot_table(
        data=data, index='Тип',
        values=[cnt_old, cnt_new, rev_old, rev_new], aggfunc='sum'
    )
    final = pd.DataFrame(
        [[pivot.sum()[rev_old], pivot.sum()[rev_new]]],
        columns=[f'Выручка {types[0]}', f'Выручка {types[1]}']
    )

    for type_ in ["Вывод", "Исключение", "Лонч"]:
        final[type_] = (pivot[rev_new] - pivot[rev_old])[type_]\
            if type_ in pivot.index else 0

    price_old = (pivot[rev_old]/pivot[cnt_old])["Current"]
    price_new = (pivot[rev_new]/pivot[cnt_new])["Current"]
    final["Цена"] = pivot[cnt_old]["Current"] * (price_new - price_old)
    final["Шт"] = price_new * (
        pivot[cnt_new]["Current"] - pivot[cnt_old]["Current"]
    )
    final = final[
        [rev_old, "Шт", "Цена", "Вывод", "Лонч", "Исключение", rev_new]
    ]
    df = final.sum().reset_index()
    df.columns = ['name', 'value']
    return df


def get_factors(df):
    "Расчет накопленных значений, цветов и процентов текста для датафрейма."
    df["cum_value"] = 0
    df["base"] = 0
    df["show"] = 0
    df["color"] = 0
    df["text"] = 0
    df["textp"] = 0
    df["text"] = df["value"].apply(lambda x: round(x / 1000000, 2))

    for i in range(len(df)):
        df.loc[i, "show"] = abs(df.loc[i, "value"])
        if i == 0 or i == len(df) - 1:
            # Отобразить первое и последнее значение цвет серый
            df.loc[i, "cum_value"] = df.loc[i, "value"]
            df.loc[0, "base"] = 0
            df.loc[i, "color"] = 'silver'
        else:
            # Иначе считаем накопленное значение как сумма текущего с пред
            df.loc[i, "cum_value"] = df.loc[i-1, "cum_value"] +\
                df.loc[i, "value"]
            if df.loc[i, "value"] < 0:
                # Если значение меньше 0, то цвет красный
                df.loc[i, "base"] = df.loc[i, "cum_value"]
                df.loc[i, "color"] = 'red'
            else:
                # Иначе цвет зеленый
                df.loc[i, "base"] = df.loc[i, "cum_value"] -\
                     df.loc[i, "value"]
                df.loc[i, "color"] = 'green'
        text_p = round((df.loc[i, 'value'] / df.loc[0, 'value'])*100, 1)
        text_p = text_p if i != len(df)-1 else round(text_p-100, 1)
        df.loc[i, "textp"] = f"{text_p}%" if i != 0 else ""
    return df


def plot_data(df, ch_types):
    """Построение данных с использованием Plotly и Streamlit."""
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df.name, y=df.base,
            name='base', marker_color=['white'] * len(df),
        )
    )
    fig.add_trace(
        go.Bar(
            x=df.name, y=df.show,
            name='show', text=df.text, marker_color=list(df.color),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.name, y=[90000] * len(df),
            name='%', text=df.textp, mode='text', textposition='top center',
        )
    )
    fig.update_layout({
        'barmode': 'stack',
        'xaxis': {'dtick': 'M1', 'tickformat': "%m.%Y", 'tickangle': 0},
        'yaxis': {'title_text': "Value"},
    })
    fig.update_yaxes(title='y', visible=False, showticklabels=False)
    fig.update_layout(
        yaxis_range=[0, max(df["cum_value"]) * 1.1],
        margin=dict(l=0, r=0, t=10, b=0),
        title=dict(
            text=f"Факторный анализ продаж {ch_types[1]} vs {ch_types[0]}"
            ", млн руб б/НДС",
            font=dict(size=20),
            yref='paper',
            y=1
        ),
        autosize=True, height=400, showlegend=False
    )
    return fig


def get_add_text(data, type_, sort_by):
    col_name = f'Выручка {sort_by}'
    df = data[data["Тип"] == type_]\
        .sort_values(by=col_name, ascending=False)[["Субкатегория", col_name]]
    df[col_name] = df[col_name] / 1000000
    text = LIST_FORMAT.format('Итого', df[col_name].sum())
    for i in range(len(df)):
        text += LIST_FORMAT.format(df.iloc[i, 0], df.iloc[i, 1])
    return text


# -----------------------------КОД СТРАНИЦЫ------------------------------------
cfg = build_config('config.yaml')
db_path, last_update_month, last_update_year = setup(cfg)

default_monthes = fetch_default_months(db_path)
types = fetch_report_types(db_path)
categories = fetch_categories(db_path)

st.header('Факторный анализ')
header_cols = st.columns([1, 1, 1])
monthes = header_cols[0].multiselect(
    label="Выберите месяц", options=['Все'] + [i for i in range(1, 13)],
    default=default_monthes
)
ch_types = header_cols[1].multiselect(
    label="Выберите тип отчета",
    options=types, default=['Факт 2023', 'Факт 2024'], max_selections=2
)
category = header_cols[2].multiselect(
    label="Выберите категорию",
    options=categories, default='Все', max_selections=1
)

try:
    data = get_data(db_path, ch_types, monthes, category)
    df = get_types(data, ch_types)
    df = get_factors(df)

    launch_text = get_add_text(data, "Лонч", ch_types[1])
    withdrawal_text = get_add_text(data, "Вывод", ch_types[0])

    cols = st.columns([3, 2])
    cols[0].plotly_chart(plot_data(df, ch_types))
    with cols[1]:
        subheader("Данные в млн руб б/НДС", 5)
        subcols = st.columns([1, 1])
        with subcols[0]:
            subheader("Вывод из ассортимента:", 5)
            st.write(withdrawal_text, unsafe_allow_html=True)
        with subcols[1]:
            subheader("Лончи (новые продукты):", 5)
            st.write(launch_text, unsafe_allow_html=True)
except BaseException:
    warning()
