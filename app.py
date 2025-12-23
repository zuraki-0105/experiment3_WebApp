from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from sqlalchemy import create_engine, MetaData, Table, select, func

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers.timetable import router as timetable_router


# -------------------
# DB 設定（※パスを合わせる）
# -------------------
DATABASE_FILE = "restaurants.db"
engine = create_engine(
    f"sqlite:///{DATABASE_FILE}",
    connect_args={"check_same_thread": False},  # FastAPI で SQLite 使うときおまじない
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
    segment: str  #業態
    business_type: str  #営業の種類

class RestaurantListResponse(BaseModel):#ミスを減らすためのおまじない
    restaurants: List[Restaurant]   #リスト形式で複数のレストラン情報を格納
    count: int  #総数


class Station(BaseModel):   #クラス定義
    id: int   #id
    name: str   #駅名
    name_kana: str   #駅名（かな）
    address: str   #住所
    line: str   #路線
    company: str   #鉄道会社
    lat: float   #緯度
    lng: float   #経度


class StationListResponse(BaseModel):
    stations: List[Station]  #駅情報のリスト
    count: int  #総数


class BusStop(BaseModel):
    id: int   #id
    stop_no: Optional[int]   #停留所番号
    stop_no_branch: Optional[int]   #停留所番号（枝番）
    name: str   #停留所名
    lat: float   #緯度
    lng: float   #経度


class BusStopListResponse(BaseModel):   
    bus_stops: List[BusStop]  #バス停情報のリスト
    count: int  #総数


# ---------- FastAPI アプリ本体 ----------

app = FastAPI()
app.include_router(timetable_router)    # 時刻表ルーター

# staticフォルダを公開
app.mount("/static", StaticFiles(directory="static"), name="static")

# templatesフォルダをテンプレートとして利用
templates = Jinja2Templates(directory="templates")


# 動作確認用
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#/map エンドポイント
@app.get("/map")
def read_map(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})


# /restaurants エンドポイント
@app.get("/restaurants", response_model=RestaurantListResponse)
def list_restaurants(
    segment: Optional[str] = None,  # ?segment=student みたいに絞り込み用
    limit: int = 400,   #表示上限
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

    # row は dict っぽいオブジェクトになるので、そのまま展開して Pydantic に渡す
    restaurants = [Restaurant(**row) for row in rows]

    return RestaurantListResponse(
        restaurants=restaurants,
        count=total,
    )

# /stations エンドポイント
@app.get("/stations", response_model=StationListResponse)   #駅情報取得API
def list_stations(
    limit: int = 200,
    offset: int = 0,
):
    # DB から駅情報を取得
    with engine.connect() as conn:
        query = select(stations_table).offset(offset).limit(limit)
        count_query = select(func.count()).select_from(stations_table)

        rows = conn.execute(query).mappings().all()
        total = conn.execute(count_query).scalar()

    stations = [Station(**row) for row in rows] #Pydanticモデルに変換


    return StationListResponse(
        stations=stations,
        count=total,
    )

# /bus_stops エンドポイント
@app.get("/bus_stops", response_model=BusStopListResponse)
def list_bus_stops(
    limit: int = 500,
    offset: int = 0,
):
    # DB からバス停情報を取得
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

