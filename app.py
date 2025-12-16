from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from sqlalchemy import create_engine, MetaData, Table, select, func

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# -------------------
# DB 設定（※パスを合わせる）
# -------------------
DATABASE_FILE = "restaurants.db"
engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},  # FastAPI で SQLite 使うときおまじないああああああ
)
metadata = MetaData()

# ETL スクリプトで作ったテーブル構造と合わせる
restaurants_table = Table(
    "restaurants",
    metadata,
    autoload_with=engine,  # 既存DBからカラム情報を読み込む
)

stations_table = Table(
    "stations",
    metadata,
    autoload_with=engine,
)

bus_stops_table = Table(
    "bus_stops",
    metadata,
    autoload_with=engine,
)


# ---------- Pydantic モデル定義 ----------

class Restaurant(BaseModel):#クラス定義
    id: int     #id
    name: str   #店名
    lat: float  #緯度
    lng: float  #経度
    address: str    #住所
    segment: str  # "student" / "family" など
    business_type: str

class RestaurantListResponse(BaseModel):#ミスを減らすためのおまじない
    restaurants: List[Restaurant]
    count: int


class Station(BaseModel):
    id: int
    name: str
    name_kana: str
    address: str
    line: str
    company: str
    lat: float
    lng: float


class StationListResponse(BaseModel):
    stations: List[Station]
    count: int


class BusStop(BaseModel):
    id: int
    stop_no: Optional[int]
    stop_no_branch: Optional[int]
    name: str
    lat: float
    lng: float


class BusStopListResponse(BaseModel):
    bus_stops: List[BusStop]
    count: int


# ---------- FastAPI アプリ本体 ----------

app = FastAPI()

# staticフォルダを公開
app.mount("/static", StaticFiles(directory="static"), name="static")

# templatesフォルダをテンプレートとして利用
templates = Jinja2Templates(directory="templates")


# 動作確認用
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



# /restaurants エンドポイント
@app.get("/restaurants", response_model=RestaurantListResponse)
def list_restaurants(
    segment: Optional[str] = None,  # ?segment=student みたいに絞り込み用
    limit: int = 300,   #表示上限
    offset: int = 0,    #どこから表示するか
):
    with engine.connect() as conn:
        # ベースとなる SELECT 文
        query = select(restaurants_table)
        count_query = select(func.count()).select_from(restaurants_table)

        # segment（業態）でフィルタ
        if segment is not None:
            query = query.where(restaurants_table.c.segment == segment)
            count_query = count_query.where(restaurants_table.c.segment == segment)

        # ページング
        query = query.offset(offset).limit(limit)

        # 実行
        rows = conn.execute(query).mappings().all()
        total = conn.execute(count_query).scalar()

    # row は dict っぽいオブジェクトになるので、そのまま展開して Pydantic に渡すうぇええ
    restaurants = [Restaurant(**row) for row in rows]

    return RestaurantListResponse(
        restaurants=restaurants,
        count=total,
    )

@app.get("/stations", response_model=StationListResponse)
def list_stations(
    limit: int = 200,
    offset: int = 0,
):
    with engine.connect() as conn:
        query = select(stations_table).offset(offset).limit(limit)
        count_query = select(func.count()).select_from(stations_table)

        rows = conn.execute(query).mappings().all()
        total = conn.execute(count_query).scalar()

    stations = [Station(**row) for row in rows]

    return StationListResponse(
        stations=stations,
        count=total,
    )


@app.get("/bus_stops", response_model=BusStopListResponse)
def list_bus_stops(
    limit: int = 500,
    offset: int = 0,
):
    with engine.connect() as conn:
        query = select(bus_stops_table).offset(offset).limit(limit)
        count_query = select(func.count()).select_from(bus_stops_table)

        rows = conn.execute(query).mappings().all()
        total = conn.execute(count_query).scalar()

    bus_stops = [BusStop(**row) for row in rows]

    return BusStopListResponse(
        bus_stops=bus_stops,
        count=total,
    )

