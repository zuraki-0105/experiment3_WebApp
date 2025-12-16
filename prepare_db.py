import csv
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, MetaData, select

CSV_RESTAURANT = 'opendata/18201_food_business_all.csv'
CSV_STATION = 'opendata/fukuishieki_adress.csv'
CSV_BUS_STOP_SIMPLE = 'opendata/fukuitetsudo_adress.csv'
CSV_BUS_STOP_NUMBERED = 'opendata/keifuku_adress_bussstop.csv'

DATABASE_FILE = 'restaurants.db'

engine = create_engine(f'sqlite:///{DATABASE_FILE}')
metadata = MetaData()

restaurant_temp = Table('restaurant_temp', metadata,
    Column('name', String),
    Column('lat', Float),
    Column('lng', Float),
    Column('address', String),
    Column('segment', String),
    Column('business_type', String)
)

restaurants_table = Table('restaurants', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String),
    Column('lat', Float),
    Column('lng', Float),
    Column('address', String),
    Column('segment', String),
    Column('business_type', String)
)

stations_table = Table('stations', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String),
    Column('name_kana', String),
    Column('address', String),
    Column('line', String),
    Column('company', String),
    Column('lat', Float),
    Column('lng', Float)
)

bus_stops_table = Table('bus_stops', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('stop_no', Integer, nullable=True),
    Column('stop_no_branch', Integer, nullable=True),
    Column('name', String),
    Column('lat', Float),
    Column('lng', Float)
)

def safe_float(v):
    try:
        s = ("" if v is None else str(v)).strip()
        if s == "" or s == "―":
            return 0.0
        return float(s)
    except:
        return 0.0

def safe_int(v):
    try:
        s = ("" if v is None else str(v)).strip()
        if s == "" or s == "―":
            return 0
        return int(float(s))
    except:
        return 0

with engine.connect() as conn:
    metadata.drop_all(conn)
    metadata.create_all(conn)

    # ===== 飲食店 =====
    with open(CSV_RESTAURANT, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat = safe_float(row.get("緯度"))
            lng = safe_float(row.get("経度"))
            if lat == 0 or lng == 0:
                continue

            business_type = row.get("営業の種類", "")
            if business_type not in ["① 飲食店営業", "⑬ その他の食料・飲料販売業"]:
                continue

            conn.execute(restaurant_temp.insert().values(
                name=row.get("営業施設名称、屋号又は商号", ""),
                lat=lat,
                lng=lng,
                address=row.get("営業施設所在地", ""),
                segment=row.get("業態", ""),
                business_type=business_type
            ))

    conn.execute(
        restaurants_table.insert().from_select(
            ['name', 'lat', 'lng', 'address', 'segment', 'business_type'],
            select(
                restaurant_temp.c.name,
                restaurant_temp.c.lat,
                restaurant_temp.c.lng,
                restaurant_temp.c.address,
                restaurant_temp.c.segment,
                restaurant_temp.c.business_type
            )
        )
    )

    # ===== 駅 =====
    with open(CSV_STATION, 'r', encoding='utf-8', errors='replace') as f:
        # #property 行まで飛ばす
        for line in f:
            if line.startswith("#property"):
                break

        next(f)  # #object_type_xsd
        next(f)  # #property_context

        reader = csv.DictReader(
            f,
            fieldnames=["id", "駅名", "えきめい_かな", "所在地", "路線", "鉄道会社", "緯度", "経度"]
        )

        for row in reader:
            lat = safe_float(row.get("緯度"))
            lng = safe_float(row.get("経度"))
            if lat == 0 or lng == 0:
                continue

            conn.execute(stations_table.insert().values(
                name=row.get("駅名", ""),
                name_kana=row.get("えきめい_かな", ""),
                address=row.get("所在地", ""),
                line=row.get("路線", ""),
                company=row.get("鉄道会社", ""),
                lat=lat,
                lng=lng
            ))


    # ===== バス停（番号あり）=====
    with open(CSV_BUS_STOP_NUMBERED, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith("#property"):
                break

        next(f)  # #object_type_xsd
        next(f)  # #property_context

        reader = csv.DictReader(
            f,
            fieldnames=[
                "id", "バス停番号", "バス停番号枝番", "バス停名", "緯度", "経度",
                "", "", "", ""   # 余分な空列
            ]
        )

        for row in reader:
            lat = safe_float(row.get("緯度"))
            lng = safe_float(row.get("経度"))
            if lat == 0 or lng == 0:
                continue

            conn.execute(bus_stops_table.insert().values(
                stop_no=safe_int(row.get("バス停番号")),
                stop_no_branch=safe_int(row.get("バス停番号枝番")),
                name=row.get("バス停名", ""),
                lat=lat,
                lng=lng
            ))


    # ===== バス停（簡易）=====
    with open(CSV_BUS_STOP_SIMPLE, 'r', encoding='utf-8', errors='replace') as f:
        # #property 行まで飛ばす
        for line in f:
            if line.startswith("#property"):
                break

        next(f)  # #object_type_xsd
        next(f)  # #property_context

        # ★ ID列が先頭にある想定
        reader = csv.DictReader(
            f,
            fieldnames=["id", "バス系統名", "バス停名", "緯度", "経度"]
        )

        for row in reader:
            lat = safe_float(row.get("緯度"))
            lng = safe_float(row.get("経度"))
            if lat == 0 or lng == 0:
                continue

            conn.execute(bus_stops_table.insert().values(
                stop_no=None,
                stop_no_branch=None,
                name=row.get("バス停名", ""),
                lat=lat,
                lng=lng
            ))


    conn.commit()

print("restaurants.db を作成しました（飲食店・駅・バス停）")
