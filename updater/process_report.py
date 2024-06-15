import pandas as pd
from dadata import Dadata
from fuzzywuzzy import fuzz

from util.db import request_sql
from updater.const import CLIENT_HEAD, CLIENT_COLS, PRODUCT_COLS, UNITS
from updater.const import SALES_COLS


def prepare_df(df: pd.DataFrame):
    """
    Функция подготавливает датафрейм, полученный с почты, к дальнейшней
    обработке: заполняются даты, удаляются пустые строки.
    """
    row = list(df.iloc[:, 0]).index('Клиент.Код')  # поиск строки с заголовками
    df.columns = df.iloc[row, :]
    df = df.iloc[row+1:, :]
    df.reset_index(inplace=True, drop=True)
    df.fillna(0, inplace=True)

    ind = list(df[df["Клиент.Наименование"] == 0].index)  # поиск строк-дат
    df["Дата"] = 0
    date_ind = list(df.columns).index("Дата")
    ind = [0] + ind
    k = 1
    for i in range(len(df)):  # заполнение столбца Дата
        try:
            if i < ind[k]:
                df.iloc[i, date_ind] = df.iloc[ind[k-1], 0]
            else:
                df.iloc[i, date_ind] = df.iloc[ind[k], 0]
                k += 1
        except BaseException:
            df.iloc[i, date_ind] = df.iloc[ind[k-1], 0]
    df.drop(df[(df["Дата"] == 0)].index, inplace=True)
    df.drop(df[(df["Клиент.Наименование"] == 0)].index, inplace=True)
    df.reset_index(inplace=True, drop=True)
    df["Год"] = df["Дата"].apply(lambda x: int(x.split('.')[2]))
    df["Месяц"] = df["Дата"].apply(lambda x: int(x.split('.')[1]))
    df["Признак"] = "Факт"
    return df


def analogue_value(search: list, dict_val: dict) -> dict:
    """
    Для каждого элемента из df_search найти наиболее похожий на него
    аналог из df_dict и вернуть соответствующее этому аналогу значение.

    1. Список search - список значений, к которым подбирается аналог из
    существующих значений в бд
    2. Словарь dict_val - содержит пару аналог-значение из бд

    ПРИМЕР: искомое значение - новый товар "CTH-KM-20".
    Функция вернет "KM" - категория "CTH-KM-2", который наиболее похож
    на "CTH-KM-20".
    """
    df_search = pd.DataFrame(search, columns=['search'])
    df_dict = pd.DataFrame.from_dict(dict_val, orient='index').reset_index()
    df_dict.columns = ['analogue', 'value']
    cross = pd.merge(df_search, df_dict, how="cross")
    cross["ratio"] = 0
    for i in range(len(cross)):  # расчет коэф-та схожести в кросс-таблице
        cross.iloc[i, -1] = fuzz.token_sort_ratio(
            cross.iloc[i, 0], cross.iloc[i, 1]
        )
    df_search["value"] = 0  # поиск значения с max коэф-м схожести
    for i in range(len(df_search)):
        value = cross.iloc[
            cross[cross["search"] == df_search.iloc[i, 0]]["ratio"].idxmax(),
            2
        ]
        df_search.iloc[i, -1] = value
    return df_search.set_index('search')["value"].to_dict()


def new_clients(db_path: str, dadata: Dadata, df: pd.DataFrame):
    """
    Функция получает обработанный датафрейм и возвращает датафрейм, вклю-
    чающий в себя хар-ки новых клиентов, который нужно загрузить в бд.
    """
    clients = df[CLIENT_COLS].drop_duplicates()
    clients.columns = ["code", "name", "head_name", "type", "adress"]
    db = request_sql(db_path, "SELECT code, name FROM clients", headers=True)
    clients = pd.merge(clients, db, how='left', on='code')
    clients = clients[clients["name_y"].isna()]
    if len(clients) > 0:
        clients["head_name"] = clients.apply(  # название головной организации
            lambda x:
                x["head_name"] if x["head_name"] not in CLIENT_HEAD
                else x["name_x"],
            axis=1
        )
        clients.dropna(axis=1, inplace=True)
        clients["region"] = clients["adress"].apply(  # нормализация адреса
            lambda x: dadata.clean("address", x)['region']
        )
        client_reg = analogue_value(  # подбор региона из бд
            list(clients["region"]),
            pd.DataFrame(
                request_sql(db_path, "SELECT region, region FROM regions")
            ).set_index(0)[1].to_dict()
        )
        clients["region"] = clients["region"].apply(lambda x: client_reg[x])
        return clients[["code", "name_x", "head_name", "region", "type"]]
    else:
        return pd.DataFrame([])  # если новых клиентов нет - вернуть пустой


def new_products(db_path: str, df: pd.DataFrame):
    """
    Функция получает обработанный датафрейм и возвращает датафрейм, вклю-
    чающий в себя хар-ки новых продуктов, который нужно загрузить в бд.
    """
    products = df[PRODUCT_COLS].drop_duplicates()
    products.columns = ["code", "vendor_code", "name", "type", "unit"]
    db = request_sql(db_path, "SELECT * FROM products", headers=True)
    products = pd.merge(products, db, on="code", how="left")
    products = products[products["subcategory"].isna()]
    if len(products) > 0:
        products_subcat = analogue_value(  # подбор субкатегории из бд
            list(products["name_x"]),
            db[["name", "subcategory"]]\
            .set_index("name")["subcategory"].to_dict()
        )
        products["subcategory"] = products["name_x"].apply(
            lambda x: products_subcat[x]
        )
        products["ord"] = [0] * len(products)
        products["code_ap"] = [0] * len(products)
        products["unit_x"] = products["unit_x"].apply(lambda x: UNITS[x])
        return products[
            [
                "code", "name_x", "vendor_code_x", "code_ap",
                "type_x", "unit_x", "ord", "subcategory"
            ]
        ]
    else:
        return pd.DataFrame([])  # если новых продуктов нет - вернуть пустой


def new_sales(df: pd.DataFrame):
    monthes = list(df["Месяц"].unique())
    years = list(df["Год"].unique())
    df = df[SALES_COLS]
    df = pd.pivot_table(
        data=df,
        index=SALES_COLS[:-4],
        values=SALES_COLS[-4:],
        aggfunc='sum'
    )
    df.reset_index(inplace=True)
    df = df[SALES_COLS]
    df["Комментарий"] = '0'
    return df, years, monthes
