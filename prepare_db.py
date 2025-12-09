import csv
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, MetaData, select

# --- 設定 ---
CSV_RESTAURANT = 'opendata/18201_food_business_all.csv'
DATABASE_FILE = 'restaurants.db'

# SQLAlchemy setting
engine = create_engine(f'sqlite:///{DATABASE_FILE}')
metadata = MetaData()

# --- 一時テーブル ---
restaurant_temp = Table('restaurant_temp', metadata,
    Column('name', String),
    Column('lat', Float),
    Column('lng', Float),
    Column('address', String),
    Column('segment', String),
    Column('business_type', String)
)

# --- 最終テーブル ---
restaurants_table = Table('restaurants', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String),
    Column('lat', Float),
    Column('lng', Float),
    Column('address', String),
    Column('segment', String),
    Column('business_type', String)
)

# ------------------------------
# メイン処理
# ------------------------------
with engine.connect() as conn:
    # 初期化
    metadata.drop_all(conn)
    metadata.create_all(conn)

    # 一時テーブルに CSV を読み込み
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

                # --- ⭐ 飲食店営業のみを残すフィルタ ---
                if business_type not in ["① 飲食店営業", "⑬ その他の食料・飲料販売業"]:
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
                print("CSV 読み込みエラー:", e)
                continue

    # 一時テーブル → 最終テーブルへコピー
    final_query = select(
        restaurant_temp.c.name,
        restaurant_temp.c.lat,
        restaurant_temp.c.lng,
        restaurant_temp.c.address,
        restaurant_temp.c.segment,
        restaurant_temp.c.business_type
    )

    conn.execute(
        restaurants_table.insert().from_select(
            ['name', 'lat', 'lng', 'address', 'segment', 'business_type'],
            final_query
        )
    )

    conn.commit()

print(f"データベース '{DATABASE_FILE}' を作成しました！（飲食店営業のみ）")
