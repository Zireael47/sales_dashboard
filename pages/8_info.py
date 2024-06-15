import streamlit as st

from util.config import build_config
from webapp.util import setup, subheader


cfg = build_config('config.yaml')
db_path, last_update_month, last_update_year = setup(cfg)

# -----------------------------О ПРОЕКТЕ---------------------------------------
st.header('О проекте')
st.write(
    "Веб-приложение предназначено для <b>анализа продаж</b> компании, занимающ"
    "ейся продажей монтажных инструментов. Все данные, представленные в при"
    "ложении, сгенерированы автоматически и используются исключительно для дем"
    "онстрационных целей."
    "  \n  \n<b>Цель этого приложения</b> – предоставить пользователям удобный"
    " и интуитивно понятный интерфейс для анализа и визуализации данных о прод"
    "ажах. "
    "Вы можете просматривать, фильтровать и взаимодействовать с данными, "
    "получая ценную информацию для принятия  управленческих решений."
    "  \n  \n<b>Интеграция с 1С</b> компании позволяет автоматически получать "
    "обновления и проводить анализ данных в реальном времени.",
    unsafe_allow_html=True
)

# -----------------------------ОБЩАЯ ИНФОРМАЦИЯ--------------------------------
st.header('Основные возможности')
st.write(
    "Приложение включает в себя несколько интерактивных страниц,"
    " отображающих <b>таблицы</b> и <b>графики</b>. "
    "Настройка отчетов осуществляется с помощью <b>кнопок</b> с выбором "
    "одного или нескольких вариантов.",
    unsafe_allow_html=True
)
col1, col2, col3 = st.columns([1, 1, 1])

# -----------------------------Таблицы-----------------------------------------
with col1:
    subheader("Работа с таблицами", 5)
    st.write(
        "1. Таблицы можно <b>сортировать</b> нажатием на заголовок столбца, "
        "появившаяся стрелка '↑' или '↓' показывает порядок сортировки.",
        unsafe_allow_html=True
    )
    st.write(
        "2. Можно <b>добавлять и скрывать</b> столбцы в таблице. "
        "Для этого - навести на название любого столбца, нажать на '≡', "
        "затем на '▩', отметить '✔' нужные столбцы.",
        unsafe_allow_html=True
    )
    st.write(
        "3. В таблицах с группировкой можно <b>раскрывать и скрывать строки."
        "</b>Для этого нужно нажать на символ '>' или 'v' в начале строки.",
        unsafe_allow_html=True
    )
    st.write(
        "4. Все таблицы можно <b>скачивать</b>. Для этого нужно нажать "
        "правой кнопкой мыши на таблицу, выбрать 'Export' -> 'Excel Export'.",
        unsafe_allow_html=True
    )

# -----------------------------Графики-----------------------------------------
with col2:
    subheader("Работа с графиками", 5)
    st.write(
        "1. Графики можно <b>масштабировать</b> нажатием на '+' и '-' в правом"
        " верхнем углу графика. Чтобы вернуть исходный масштаб, нужно нажать н"
        "а '⟰'.",
        unsafe_allow_html=True
    )
    st.write(
        "2. Графики можно <b>скачивать</b>. Для этого нужно нажать на символ "
        "фотооаппарата в правом верхнем углу графика.",
        unsafe_allow_html=True
    )

# -----------------------------Кнопки------------------------------------------
with col3:
    subheader("Настройка отчетов", 5)
    st.write('Для настройки отчета используются два типа кнопок:')
    st.radio(
        'Выбор одного варианта из предложенных',
        ['Кнопка 1', 'Кнопка 2', 'Кнопка 3'],
    )
    st.multiselect(
        'Выбор нескольких вариантов из предложенных',
        ['Все', 'Кнопка 1', 'Кнопка 2', 'Кнопка 3']
    )

# -----------------------------ОТЧЕТЫ------------------------------------------
# -----------------------------План-факт---------------------------------------
st.header('План-факт продаж')
st.write(
    "Отчет представляет собой <b>таблицу</b>, в которой по годам и различным "
    "показателям (категория/менеджер/клиент и др.) сгруппированы "
    "<b>фактические и плановые продажи</b> в шт, руб б/НДС и руб с/НДС.",
    unsafe_allow_html=True
)
col4, col5, col6 = st.columns([1, 1, 1])
col4.write(
    "В заголовке отчета можно выбрать <b>месяц</b> (по умолчанию будут выбраны"
    " все месяцы с января по текущий) и <b>группировку</b> отчета:"
    "  \n1. <b>По категориям</b>: Категория -> Субкатегория"
    "  \n2. <b>По менеджерам</b>: Менеджер -> Клиент"
    "  \n3. <b>Настраиваемая</b>: Выберите показатели в нужном порядке",
    unsafe_allow_html=True
)
col4.warning(
    "Чем больше показателей выбираете в настраиваемой группировке,"
    " тем дольше загрузка отчета!"
)
col5.write(
    "По умолчанию в таблице отображаются следующие <b>показатели</b>:"
    "  \n1. Последний <b>план</b> (Bdg/FC1/FC2/FC3) в <b>руб б/НДС</b>"
    "  \n2. Факт продаж <b>прошлого</b> года в <b>руб б/НДС</b>"
    "  \n3. Факт продаж <b>текущего</b> года в <b>руб б/НДС</b>"
    "  \n4. Факт продаж <b>текущего</b> года в <b>руб с НДС</b>"
    "  \n5. <b>Приросты</b> (<b style='color:red'>отрицательные</b> и "
    "<b style='color:MediumSeaGreen'>положительные</b>): "
    "  \n5.1 Факт текущего года к плану продаж в <b>руб б/НДС</b>"
    "  \n5.2 Факт текущего года к прошлому в <b>руб б/НДС</b>"
    "  \n 6. Вклад в выполнение плана в <b>руб б/НДС</b>",
    unsafe_allow_html=True
)
col6.write(
    "<span style='color:grey'>Вклад показывает, какой % из общего прироста "
    "занимает категория. Сумма всех вкладов = общий прирост. Может быть"
    " расхождение в 1% из-за округления."
    "  \nСм. пример: 17% + 1% + 1% + 0% + (-2%) = 18%</span>",
    unsafe_allow_html=True
)
col6.image('./data/pics/contribution.jpg', use_column_width=True)

# -----------------------------Факторный анализ--------------------------------
st.header('Факторный анализ')
col7, col8 = st.columns([1, 2])
col7.write(
    "Факторный анализ показывает, за счет чего <b style='color:MediumSeaGreen'"
    ">растет</b> или <b style='color:red'>падает</b> выручка "
    "за период в разрезе факторов:"
    "  \n1. Шт  \n2. Цена  \n3. Вывод (продукты, выведенные из ассортимента)"
    "  \n4. Лонч (новые продукты)  \n5. Исключения (комплекты, услуги и пр.)",
    unsafe_allow_html=True
)
col7.write(
    "Справа от графика расписано, какие товары выводятся из ассортимента"
    ", а какие являются новыми.",
    unsafe_allow_html=True
)
col7.write(
    "Для настройки отчета нужно выбрать <b>месяц</b>, <b>тип</b>"
    " (факт/план и год) и <b>категорию</b> (одну из предложенных или все).",
    unsafe_allow_html=True
)
col7.warning(
    "При выборе типа отчета первым нужно отметить более ранний период."
    "  \nПрим. справа: сначала Факт 2023, затем Факт 2024"
)
col8.image("./data/pics/factor_analysis.jpg", use_column_width=True)

# -----------------------------Динамика помесячно------------------------------
st.header('Динамика помесячно')
col9, col10 = st.columns([1, 2])
col9.write(
    "На странице расположены графики продаж по месяцам в шт (слева) и "
    "руб б/НДС (справа)."
)
col9.write(
    "Для настройки отчета нужно выбрать <b>тип</b> "
    " (факт/план и год) и при необходимости <b>фильтры</b>. "
    "  \nВыбранные типы наносятся на график линиями, в расчет включаются "
    "только значения, заданные фильтрами.",
    unsafe_allow_html=True
)
col9.write(
    "Таблица со значениями графиков расположена внизу страницы."
)
col10.image('./data/pics/monthly.jpg', use_column_width=True)

# -----------------------------Продажи по регионам-----------------------------
st.header('Продажи по регионам')
col11, col12, col13 = st.columns([1, 1, 1])
with col11:
    subheader("Общая информация", 5)
    st.write(
        "Для настройки отчета необходимо выбрать <b>год</b>."
        "  \nВ правом верхнем углу находится круговая диаграмма "
        "распределения продаж по РФ, СНГ и другим странам.",
        unsafe_allow_html=True
    )
    col1, col2 = st.columns([1, 1])
    col1.image('./data/pics/map_total.jpg', use_column_width=True)
    col1.image('./data/pics/map_pie.jpg', use_column_width=True)
with col12:
    subheader("Продажи по России", 5)
    st.write(
        "За выбранный период генируется карта России с нанесением на нее"
        " фактических продаж в руб б/НДС по регионам. При наведении на "
        "регион отображается сумма продаж по этому региону."
    )
    st.image("./data/pics/map.jpg", use_column_width=True)
with col13:
    subheader("Центры ответственности", 5)
    col1, col2 = st.columns([1, 1])
    col1.write(
        "Справа от карты расположена краткая справка по региону: "
        "  \n1. Общая сумма продаж по региону"
        "  \n2. Сумма продаж по менеджерам, которые работают в этом регионе"
        "  \n3. Продажи по клиентам в этом регионе"
    )
    col2.image("./data/pics/map_managers.jpg", use_column_width=True)
# -----------------------------ABC-анализ--------------------------------------
st.header('ABC-анализ')
st.write(
    "<b>Отчет делит товары на три категории:"
    "  \nA:</b> наиболее ходовые товары, которые составляют 80% от всех продаж"
    "  \n<b>B:</b> менее ходовые товары, которые составляют 15% от всех продаж"
    "  \n<b>C:</b> товары, которые покупают реже всего - 5% от всех продаж"
    "  \nДля настройки отчета необходимо выбрать период и товарную категорию "
    " в верхней части страницы.",
    unsafe_allow_html=True
)
col11, col12 = st.columns([1, 1])
with col11:
    subheader("Категории abc-анализа", 5)
    col11.write(
        "За выбранный период генерируется таблица с указанием категории"
        " (A, B, C) для каждого товара, сумма продаж, % продаж:"
    )
    col11.image("./data/pics/abc.jpg", use_column_width=False)
with col12:
    subheader("Динамика продаж", 5)
    st.write(
        "За выбранный период генерируется график: динамика продаж товаров"
        " по категориям (A, B, C) и месяцам:",
        unsafe_allow_html=True
    )
    st.image('./data/pics/abc_monthly.jpg')
