import logging
import os
import pandas as pd
from dadata import Dadata

from util.config import build_config
from util.db import request_sql
from util.db import get_sql_list
from . import mail
from . import process_report


class Updater:
    def __init__(self, cfg_path: str):
        cfg = build_config(cfg_path)
        self._logger = Updater._new_logger(cfg["UpdaterLogPath"])
        self._mail_auth_path = os.getcwd() + cfg["MailAuthPath"]
        self._db_path = cfg["DBPath"]
        self._service = mail.gmail_authenticate(self._mail_auth_path)
        self._dadata = Dadata(cfg["DadataToken"], cfg["DadataSecret"])

    def _new_logger(logpath: str):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(logpath, encoding='utf-8')
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _log(self, msg):
        self._logger.info(msg)

    def start(self):
        self._log("Начало работы")

    def update_date(self, theme, last_update: str):
        d = last_update.replace(theme, '')
        request_sql(self._db_path, "DELETE FROM last_update")
        request_sql(self._db_path, f"INSERT INTO last_update VALUES('{d}')")
        self._log('Обновлена дата')

    def update_clients(self, df: pd.DataFrame):
        new_clients_df = process_report.new_clients(
            self._db_path, self._dadata, df
        )
        if len(new_clients_df) > 0:
            for i in range(len(new_clients_df)):
                query = f"""INSERT INTO clients VALUES(
                    {get_sql_list(new_clients_df.iloc[i, :], True)}
                )"""
                request_sql(self._db_path, query)
                self._log(
                    f'Новый клиент: {new_clients_df.iloc[i, 1]}: '
                    f"{new_clients_df.iloc[i, 3]}"
                )
        else:
            self._log('Новых клиентов нет')

    def update_products(self, df: pd.DataFrame):
        new_products_df = process_report.new_products(self._db_path, df)
        if len(new_products_df) > 0:
            for i in range(len(new_products_df)):
                query = f"""INSERT INTO products VALUES(
                    {get_sql_list(new_products_df.iloc[i, :], True)}
                )"""
                request_sql(self._db_path, query)
                self._log(
                    f'Новый продукт: {new_products_df.iloc[i, 1]}: '
                    f"{new_products_df.iloc[i, 7]}"
                )
        else:
            self._log('Новых продуктов нет')

    def update_sales(self, df: pd.DataFrame):
        new_sales, years, monthes = process_report.new_sales(df)
        query = f"""DELETE FROM sales
                    WHERE type = 'Факт'
                        AND year in ({get_sql_list(years)})
                        AND month in ({get_sql_list(monthes)})
                        AND comment = 0"""
        request_sql(self._db_path, query)
        for i in range(len(new_sales)):
            query = f"""INSERT INTO sales VALUES(
                    {get_sql_list(new_sales.iloc[i, :], True)})"""
            request_sql(self._db_path, query)
        self._log('Обновлены продажи')

    def update_all(self, theme: str):
        df, subject = mail.get_file_by_mail_id(self._service, theme)
        df = process_report.prepare_df(df)
        self.update_date(theme, subject)
        self.update_clients(df)
        self.update_products(df)
        self.update_sales(df)
