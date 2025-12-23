from fastapi import APIRouter, Query
from services.timetable_service import get_timetable_by_station

router = APIRouter(tags=["timetable"])

@router.get("/timetable")
def timetable(station: str = Query(..., description="駅名（例：西鯖江）")):
    items = get_timetable_by_station(station)
    return {"station": station, "count": len(items), "items": items}
