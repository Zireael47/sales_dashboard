JOINS = """
    FROM sales
    LEFT JOIN products
        ON products.code = sales.product_code
    LEFT JOIN categories
        ON categories.subcat = products.subcategory
    LEFT JOIN clients
        ON clients.code = sales.client_code
    LEFT JOIN regions
        ON clients.region = regions.region"""

ALL_COLS = {
    "Категория": "categories.category",
    "Субкатегория": "products.subcategory",
    "Base/ОЕМ": "categories.type",
    "Номенклатура.Наименование": "products.name",
    "Номенклатура.Артикул АП": "products.code_ap",
    "Ед.изм": "products.unit",
    "Менеджер": "sales.manager",
    "Клиент.Головное предприятие": "clients.head_name",
    "Клиент": "clients.name",
    "Юр/Физ лицо": "clients.type",
    "Регион": "clients.region",
    "Федеральный округ": "regions.federal_district",
    "Территориальный признак": "regions.terr_type"
}

SHOW_COLUMNS = [
    "Факт 2024 руб б/НДС",
    "Факт 2023 руб б/НДС",
    "FC1 2024 руб б/НДС",
    "Факт 2024 руб с/НДС",
    "Факт 2024 vs FC1 2024, руб б/НДС",
    "Факт 2024 vs 2023, руб б/НДС",
    "Вклад в выполнение FC1 2024, руб б/НДС"
]

SHOW_COLUMNS_MONTH = [
    'Факт 2023', 'Факт 2024', 'FC1 2024', 'Bdg 2024'
]

HIERARCHY_DICT = {
    "По категориям": [
        'categories.category',
        'products.subcategory',
    ],
    "По менеджерам": [
        'sales.manager',
        'clients.head_name',
    ]
}

NAVBAR = [
    [
        {
            "page": "pages/8_info.py",
            "label": "Инструкция"
        },
    ],
    [
        {
            "page": "pages/1_plan-fact.py",
            "label": "План-факт продаж"
        },
        {
            "page": "pages/2_factor_analysis.py",
            "label": "Факторный анализ"
        }
    ],
    [
        {
            "page": "pages/3_monthly.py",
            "label": "Динамика помесячно"
        },
        {
            "page": "pages/4_map.py",
            "label": "Продажи по регионам"
        },

    ],
    [
        {
            "page": "pages/6_abc.py",
            "label": "ABC-анализ"
        },
    ],
]

LIST_FORMAT = '  \n<b>{}</b>: {:.2f}'

COLOR_STRINGS = ['vs', 'Вклад']
UNITS = ['шт', 'руб б/НДС']

MONTH_DICT = {
    1: "Янв",
    2: "Фев",
    3: "Мар",
    4: "Апр",
    5: "Май",
    6: "Июн",
    7: "Июл",
    8: "Авг",
    9: "Сен",
    10: "Окт",
    11: "Ноя",
    12: "Дек"
}
