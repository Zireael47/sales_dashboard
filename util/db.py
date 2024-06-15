import pandas as pd
import sqlite3


def request_sql(db_path: str, request: str, headers=False):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        data = cursor.execute(request).fetchall()
        if headers:
            data = pd.DataFrame(
                data=data,
                columns=[el[0] for el in cursor.description]
            )
        return data


def get_sql_list(list, is_string=False):
    if is_string:
        return ', '.join([f"'{str(i)}'" for i in list])
    else:
        return ', '.join([str(i) for i in list])
