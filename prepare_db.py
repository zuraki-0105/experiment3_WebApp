import csv
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, MetaData, select

# --- 設定 ---
CSV_RESTAURANT = 'opendata/18201_food_business_all.csv'
CSV_STATION = 'opendata/fukuishieki_adress.csv'
CSV_BUS_STOP_SIMPLE = 'opendata/fukuitetsudo_adress.csv'
CSV_BUS_STOP_NUMBERED = 'opendata/keifuku_adress_bussstop.csv'

DATABASE_FILE = 'restaurants.db'

engine = create_engine(f'sqlite:///{DATABASE_FILE}')
metadata = MetaData()

# ==============================
# 飲食店
# ==============================
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

# ==============================
# 駅
# ==============================
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

# ==============================
# バス停
# ==============================
bus_stops_table = Table('bus_stops', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('stop_no', Integer, nullable=True),
    Column('stop_no_branch', Integer, nullable=True),
    Column('name', String),
    Column('lat', Float),
    Column('lng', Float)
)

# ------------------------------
# メイン処理
# ------------------------------
with engine.connect() as conn:
    metadata.drop_all(conn)
    metadata.create_all(conn)

    # ===== 飲食店 =====
    with open(CSV_RESTAURANT, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                name = row.get("営業施設名称、屋号又は商号", "")
                lat = float(row.get("緯度") or 0)
                lng = float(row.get("経度") or 0)
                address = row.get("営業施設所在地", "")
                segment = row.get("業態", "")
                business_type = row.get("営業の種類", "")

                if business_type not in ["① 飲食店営業", "⑬ その他の食料・飲料販売業"]:
                    continue
                if lat == 0 or lng == 0:
                    continue

                conn.execute(restaurant_temp.insert().values(
                    name=name,
                    lat=lat,
                    lng=lng,
                    address=address,
                    segment=segment,
                    business_type=business_type
                ))
            except Exception as e:
                print("飲食店CSVエラー:", e)

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
    with open(CSV_STATION, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row.get("緯度") or 0)
                lng = float(row.get("経度") or 0)
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
            except Exception as e:
                print("駅CSVエラー:", e)

    # ===== バス停（番号あり）=====
    with open(CSV_BUS_STOP_NUMBERED, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row.get("緯度") or 0)
                lng = float(row.get("経度") or 0)
                if lat == 0 or lng == 0:
                    continue

                conn.execute(bus_stops_table.insert().values(
                    stop_no=int(row.get("バス停番号") or 0),
                    stop_no_branch=int(row.get("バス停番号枝番") or 0),
                    name=row.get("バス停名", ""),
                    lat=lat,
                    lng=lng
                ))
            except Exception as e:
                print("バス停(番号あり)CSVエラー:", e)

    # ===== バス停（簡易）=====
    with open(CSV_BUS_STOP_SIMPLE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row.get("緯度") or 0)
                lng = float(row.get("経度") or 0)
                if lat == 0 or lng == 0:
                    continue

                conn.execute(bus_stops_table.insert().values(
                    stop_no=None,
                    stop_no_branch=None,
                    name=row.get("バス停名", ""),
                    lat=lat,
                    lng=lng
                ))
            except Exception as e:
                print("バス停(簡易)CSVエラー:", e)

    conn.commit()

print("restaurants.db を作成しました（飲食店・駅・バス停）")
