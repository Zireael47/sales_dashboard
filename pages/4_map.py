import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from colour import Color
from PIL import Image, ImageDraw, ImageFont

from webapp.util import setup, subheader

from util.db import request_sql
from util.config import build_config

# -----------------------------ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ-------------------------
GREEN = 200
BLUE = 150
REGIONS = pd.read_parquet("./data/geo/russia_regions.parquet")
LEGEND_FORMAT = "{:.3f}\nмлн руб\nб/НДС"


def get_map_data(db_path, year):
    "Получает данные для карты за указанный год из базы данных"
    query = f"""
        SELECT
            regions.region,
            regions.terr_type,
            SUM(sales.revenue)
        FROM sales
        LEFT JOIN clients ON sales.client_code = clients.code
        LEFT JOIN regions ON clients.region = regions.region
        WHERE sales.year = {year}
          AND sales.type = 'Факт'
        GROUP BY regions.region, regions.terr_type
    """
    map_data = request_sql(db_path, query, headers=True)
    map_data.columns = ["name", "terr_type", "value"]
    map_data["log"] = map_data["value"].apply(
        lambda x: math.log(x) if x != 0 else 0)
    map_data.fillna(0, inplace=True)
    max_val = max(map_data.log)
    min_val = min(map_data[map_data["log"] != 0].log)
    map_data["color"] = map_data["log"].apply(
        lambda x: 255 - (x - min_val) / (max_val - min_val) * 255)
    return map_data


def build_map(df, width=1000, height=600):
    "Строит карту России с данными о продажах по регионам"
    df = pd.merge(REGIONS, df, how='left', on='name')
    df.fillna(1, inplace=True)
    df["color"] = df["color"].apply(lambda x: 255 if x == 1 else x)
    df["value"] = df["value"].apply(lambda x: 0 if x == 1 else x)
    russia_map = go.Figure()
    for _, r in df.iterrows():
        red = math.floor(r["color"])
        color = 'rgb(255, 255, 255)' if red == 255\
            else f'rgb({red}, {GREEN}, {BLUE})'
        russia_map.add_trace(
            go.Scatter(
                x=r.x, y=r.y,
                name=r["name"],
                text=f"{r['name']}<br>{r['value']/1000000:.3f} млн руб б/НДС",
                hoverinfo="text", line_color='grey', fill='toself',
                line_width=1, fillcolor=color, showlegend=False
            )
        )
    russia_map.update_xaxes(visible=False)
    russia_map.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    russia_map.update_layout(
        showlegend=False, dragmode='pan',
        width=width, height=height,
        margin={'l': 10, 'b': 10, 't': 10, 'r': 10}
    )
    return russia_map


def hor_chart(df: pd.DataFrame) -> go.Figure:
    "Строит горизонтальный барчарт для стран с данными о продажах"
    df.sort_values(by="value", ascending=True, inplace=True)
    fig = go.Figure()
    for i in range(len(df)):
        name = df.iloc[i, list(df.columns).index('name')]
        value = round(df.iloc[i, list(df.columns).index('value')] / 1000000, 3)
        red = df.iloc[i, list(df.columns).index('color')]
        fig.add_trace(
            go.Bar(
                y=[name], x=[value],
                name=name,
                orientation='h',
                marker=dict(color=f'rgba({red}, 200, 150, 1)'),
            )
        )
    fig.update_layout(
        barmode='stack',
        showlegend=False,
        margin={'l': 0, 'b': 0, 't': 0, 'r': 0},
        width=200, height=300
    )
    return fig


def pie_chart(territory: pd.DataFrame):
    "Строит круговую диаграмму для распределения продаж по типу территории"
    colors = [
        f'rgb(255, {GREEN}, {BLUE})',
        f'rgb(125, {GREEN}, {BLUE})',
        f'rgb(0, {GREEN}, {BLUE})',
    ]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=territory.terr_type,
                values=list(territory.iloc[:, 1]),
                hole=.5,
                marker=dict(colors=colors)
            )
        ]
    )
    fig.update_layout(
        margin={'l': 0, 'b': 0, 't': 0, 'r': 0},
        width=200, height=200,
        legend=dict(orientation='h', xanchor="center", x=0.5, y=0)
    )
    return fig


def build_legend(
    min_val, max_val,
    length=60, height=550,
    top=20, left=5, bottom=70
) -> Image:
    "Строит легенду для карты с градацией цветов"
    min_color = Color(rgb=(0, GREEN / 255, BLUE / 255))
    max_color = Color(rgb=(1, GREEN / 255, BLUE / 255))
    font = ImageFont.truetype("arial.ttf", 13)
    font_col = (60, 60, 60)

    im = Image.new('RGB', (length, height))
    ld = im.load()
    colors = list(min_color.range_to(max_color, im.size[1]))
    for y in range(im.size[1]):
        if (y < top * 4) or y > (height - bottom - top):
            color = (255, 255, 255)
        else:
            color = (round(colors[y].rgb[0] * 255), 200, 150)
        for x in range(im.size[0]):
            ld[x, y] = color
    imgDraw = ImageDraw.Draw(im)
    imgDraw.text(
        (left, top),
        LEGEND_FORMAT.format(max_val / 1000000), font_col, font)
    imgDraw.text(
        (left, height - bottom),
        LEGEND_FORMAT.format(min_val / 1000000), font_col, font)
    return im


def fetch_years(db_path):
    """Получение списка лет из базы данных."""
    query = "SELECT DISTINCT year FROM sales"
    years = [i[0] for i in request_sql(db_path, query)]
    years.sort(reverse=True)
    return years


def get_territory_text(territory: pd.DataFrame):
    territory["value"] = territory["value"].apply(
        lambda x: round(x/1000000, 3))
    territory.sort_values(by='value', ascending=False, inplace=True)
    territory.reset_index(inplace=True)
    text = ''
    for i in range(len(territory)):
        text += f"<b>{territory.iloc[i, 0]}</b>: {territory.iloc[i, 1]};</h6> "
    return text


def regions_info(year, region):
    data = request_sql(
        db_path,
        f"""
            SELECT
                sales.manager,
                clients.head_name,
                SUM(sales.revenue) as revenue
            FROM sales
            LEFT JOIN clients ON sales.client_code = clients.code
            WHERE sales.year = {year}
                AND sales.type = 'Факт'
                AND clients.region = '{region}'
            GROUP BY sales.manager, clients.head_name
            ORDER BY sales.manager DESC, revenue DESC
        """,
        headers=True
    )
    data["revenue"] = data["revenue"].apply(lambda x: round(x/1000000, 3))
    text = f'<b>Данные за {year} год в млн руб б/НДС</b><br>'
    text += f'<br><b>Итого: {data["revenue"].sum():.3f}</b><br>'
    for i in range(len(data)):
        manager = data.iloc[i, 0]
        client = data.iloc[i, 1]
        s = data.iloc[i, 2]
        sum_m = data[data["manager"] == manager]["revenue"].sum()
        text_m = f"<b>{manager}: {sum_m:.3f}</b><br>"
        text_cl = f"{client}: <b>{s}</b><br>"

        if (i == 0) or (manager != data.iloc[i - 1, 0]):
            text += "<br>" + text_m
        text += text_cl
    return text


# -----------------------------КОД СТРАНИЦЫ------------------------------------
cfg = build_config('config.yaml')
db_path, last_update_month, last_update_year = setup(cfg)

header_cols = st.columns([1, 1, 1])
header_cols[0].header('Продажи по регионам')

# Кнопки выбора года
header_cols[1].text('')
year = header_cols[1].radio(
    "Выберите год", fetch_years(db_path), horizontal=True)

map_data = get_map_data(db_path, year)
territory = pd.pivot_table(map_data, 'value', 'terr_type', aggfunc='sum')
territory_text = get_territory_text(territory)

russia_map = build_map(map_data)
legend = build_legend(
    min_val=min(map_data[map_data.value != 0].value),
    max_val=max(map_data.value))

# Итоги по РФ, СНГ, Зарубеж
with header_cols[2]:
    st.text('')
    subheader(f'Итого {round(territory.value.sum(), 3)} млн руб б/НДС', 4)
    st.markdown(territory_text, unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns([9, 1, 3, 3])
col1.plotly_chart(russia_map, use_container_width=True)  # Карта РФ
col2.image(legend)  # Легенда
col3.plotly_chart(pie_chart(territory), use_container_width=True)
col3.plotly_chart(
    hor_chart(map_data[map_data["terr_type"] != 'Россия']),
    use_container_width=True)
# Справка по регионам
with col4:
    region = st.selectbox(
        label='Выберите регион',
        options=list(map_data["name"].unique()))
    text = regions_info(year, region)
    with st.container(height=450):
        st.write(text, unsafe_allow_html=True)
