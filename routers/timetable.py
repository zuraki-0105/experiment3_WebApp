from fastapi import APIRouter, Query
from services.timetable_service import get_timetable_by_station

router = APIRouter(tags=["timetable"])

@router.get("/timetable")
def timetable(
    station: str = Query(...),
    direction: str | None = Query(None, description="kudari / nobori / None(両方)"),
):
    items = get_timetable_by_station(station, direction=direction)
    return {"station": station, "direction": direction, "count": len(items), "items": items}

@router.get("/timetable_debug")
def timetable_debug():
    from services.timetable_service import debug_summary
    return debug_summary()



