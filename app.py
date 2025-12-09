from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

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


# ---------- FastAPI アプリ本体 ----------

app = FastAPI()


# 動作確認用
@app.get("/")
def root():
    return {"message": "FastAPI is running!"}


# とりあえずのダミーデータ（あとでオープンデータに差し替え）
DUMMY_RESTAURANTS = [
    Restaurant(
        id=1,
        name="ラーメン太郎",
        lat=36.0641,
        lng=136.2196,
        address="福井県福井市中央1-1-1",
        segment="student",
    ),
    Restaurant(
        id=2,
        name="ファミリー食堂ハナ",
        lat=36.0650,
        lng=136.2200,
        address="福井県福井市中央2-2-2",
        segment="family",
    ),
]


# /restaurants エンドポイント
@app.get("/restaurants", response_model=RestaurantListResponse)
def list_restaurants(
    segment: Optional[str] = None,  # ?segment=student みたいに絞り込み用
    limit: int = 100,   #表示上限
    offset: int = 0,    #どこから表示するか
):
    # segment でフィルタ（指定があれば）
    filtered = DUMMY_RESTAURANTS
    if segment is not None:
        filtered = [r for r in filtered if r.segment == segment]

    # ページング（とりあえず単純にスライス）
    sliced = filtered[offset : offset + limit]  #上記の条件で整形

    return RestaurantListResponse(  #表示
        restaurants=sliced,
        count=len(filtered),
    )
