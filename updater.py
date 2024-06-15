import schedule
from datetime import datetime, timedelta
import time
from updater import Updater


updater = Updater("config.yaml")
updater.start()


def update_sales():
    try:
        updater.update_all(theme="Продажи СТН (auto) от ")
    except BaseException:
        updater._log("Ошибка обновления")


start_time = (datetime.now()+timedelta(0, 15)).strftime('%H:%M:%S')
# update_time = "07:40"
schedule.every().day.at(start_time).do(update_sales)

while True:
    schedule.run_pending()
    time.sleep(1)
