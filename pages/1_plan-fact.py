import pandas as pd
import streamlit as st

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode
from st_aggrid import DataReturnMode, ColumnsAutoSizeMode, ExcelExportMode
from st_aggrid import JsCode

from webapp.const import JOINS, COLOR_STRINGS
from webapp.const import SHOW_COLUMNS, HIERARCHY_DICT, ALL_COLS
from webapp.util import warning


from util.db import request_sql, get_sql_list
from util.config import build_config
from util.read_file import read_file
from webapp.util import setup, fetch_default_months


# -----------------------------ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ-------------------------
def get_query(columns: list, months: list) -> str:
    """Функция для генерации SQL-запроса"""
    if months[0] == 'Все':
        months_str = ''
    else:
        months_str = f"WHERE sales.month in ({get_sql_list(months)})"
    col_str = ', '.join([f"{col} as '{col}'" for col in columns])
    query = f"""
        SELECT
            sales.year,
            sales.type,
            {col_str},
            CAST(SUM(count) AS INTEGER) as 'шт',
            CAST(SUM(revenue) AS INTEGER) as 'руб б/НДС',
            CAST(SUM(revenue_VAT) AS INTEGER) as 'руб с/НДС'
        {JOINS} {months_str}
        GROUP BY
            sales.year,
            sales.type,
            {', '.join(columns)}
    """
    return query


def get_hierarchy(df: pd.DataFrame, hierarchy: list) -> pd.DataFrame:
    "Функция для создания иерархии данных"
    val_ind = len(hierarchy)
    columns = ["name"] + list(df.columns)[val_ind:]
    df_h = pd.DataFrame(columns=columns)
    df_h.loc[0] = ["Итого"] + list(df.sum()[val_ind:])
    names = []
    for i in range(1, len(df)):
        group = list(df.iloc[i, :val_ind])
        for j in range(val_ind):
            name = 'Итого'
            out = df
            for k in range(j+1):
                name += f'|{group[k]}'
                out = out[out[out.columns[k]] == df.iloc[i, k]]
                if name not in names:
                    names.append(name)
                    row = list(out.sum()[val_ind:])
                    df_h.loc[len(df_h)] = [name] + row
    df_h.reset_index(drop=True, inplace=True)
    return df_h


def get_data(db_path: str, columns: list, months: list) -> pd.DataFrame:
    "Функция для получения данных из базы данных"
    query = get_query(columns, months)
    df = request_sql(db_path, query, headers=True)
    df = df.pivot_table(
        values=['руб б/НДС', 'руб с/НДС', 'шт'],
        index=columns,
        columns=['type', 'year'],
        aggfunc='sum',
        fill_value=0
    )
    df.columns = df.columns.swaplevel(2, 0).swaplevel(0, 1)
    df.columns = list(
        df.columns.to_series().apply(
            lambda x: '{0} {1} {2}'.format(*x)
        ).reset_index()[0]
    )
    df.reset_index(inplace=True)
    return df


def build_aggrid(df, show, auto_width=400, height=500) -> AgGrid:
    "Функция для построения таблицы AgGrid"
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode='single', use_checkbox=False)
    gridOptions = gb.build()
    coldefs = []
    JS_COLOR = JsCode(read_file('./webapp/styles/js/color_values.js')).js_code
    for col in list(df.columns)[1:]:
        hide = False if col in show else True
        valueFormatter = "x.toFixed(0) + '%'"\
            if any(el in col for el in COLOR_STRINGS) else "x.toLocaleString()"
        cellStyle = JS_COLOR\
            if any(el in col for el in COLOR_STRINGS) else None
        sort = "desc" if col == "Факт 2024 руб б/НДС" else None
        coldefs.append({
            "field": col,
            "valueFormatter": valueFormatter,
            "hide": hide,
            "cellStyle": cellStyle,
            "sort": sort,
        })
    gridOptions["columnDefs"] = coldefs
    gridOptions["defaultColDef"] = {
        "flex": True,
        "filter": True,
        "resizable": True,
        "sortable": True,
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "minWidth": 100
    }
    gridOptions["autoGroupColumnDef"] = {
        "headerName": 'name',
        "minWidth": auto_width,
        "cellRendererParams": {"suppressCount": True},
        'pinned': 'left'
    }
    gridOptions["treeData"] = True
    gridOptions["animateRows"] = True
    gridOptions["groupDefaultExpanded"] = 1
    gridOptions["getDataPath"] = JsCode(
        read_file('./webapp/styles/js/get_data_path.js')
    ).js_code
    return AgGrid(
        data=df, gridOptions=gridOptions, height=height,
        fit_columns_on_grid_load=True,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        data_return_mode=DataReturnMode.AS_INPUT, allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.NO_UPDATE, enable_enterprise_modules=True,
        key='grid1', theme="material",
        excel_export_mode=ExcelExportMode.MANUAL, tree_data=True,
    )


# -----------------------------КОД СТРАНИЦЫ------------------------------------
cfg = build_config('config.yaml')
db_path, last_update_month, last_update_year = setup(cfg)
default_monthes = fetch_default_months(db_path)
st.header('План-факт продаж')
header_cols = st.columns([1, 1, 1])
months = header_cols[0].multiselect(
    label="Выберите месяц",
    options=["Все"] + [i for i in range(1, 13)], default=default_monthes
)
group = header_cols[1].radio(
    label="Выберите группировку:",
    options=["По категориям", "По менеджерам", "Настроить"], horizontal=True
)

if group in HIERARCHY_DICT.keys():
    columns = HIERARCHY_DICT[group]
else:
    multigroup = header_cols[2].multiselect(
        label="Выберите элементы в нужном порядке",
        options=list(ALL_COLS.keys())
    )
    columns = [ALL_COLS[i] for i in multigroup]

if len(columns) * len(months) > 0:
    df = get_data(db_path=db_path, columns=columns, months=months)
    df = get_hierarchy(df, columns)
    perc = "Вклад в выполнение FC1 2024, руб б/НДС"
    fact = "Факт 2024 руб б/НДС"
    plan = "FC1 2024 руб б/НДС"
    prev_fact = "Факт 2023 руб б/НДС"
    try:
        df["Факт 2024 vs FC1 2024, руб б/НДС"] = (df[fact] / df[plan] - 1)*100
        df["Факт 2024 vs 2023, руб б/НДС"] = (df[fact] / df[prev_fact] - 1)*100
        df[perc] = 0
        for i in range(len(df)):
            value = (df.loc[i, fact] - df.loc[i, plan]) / df.loc[0, plan]*100
            df.loc[i, perc] = value
    except BaseException:
        pass
    df.drop_duplicates(inplace=True)
    build_aggrid(df=df, show=SHOW_COLUMNS)
else:
    warning()
