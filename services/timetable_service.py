import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

CSV_KUDARI = BASE_DIR / "opendata" / "fukutetsu_time_kudari.csv"
CSV_NOBORI = BASE_DIR / "opendata" / "fukutetsu_time_nobori.csv"

_station_map = None  # { station: [items...] }


def _normalize_time(t: str) -> str:
    t = (t or "").strip()
    if not t or t == "→":
        return ""
    if ":" in t:
        h, m = t.split(":", 1)
        if h.isdigit() and m.isdigit():
            return f"{int(h):02d}:{int(m):02d}"
    return t


def _read_fukutetsu_csv(csv_path: Path, direction: str) -> dict:
    """
    #property 行がヘッダのオープンデータCSVを読み、station->items を返す
    direction: "kudari" / "nobori"
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"timetable CSV not found: {csv_path.resolve()}")

    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    header = None
    for row in rows:
        if row and row[0].startswith("#property"):
            header = row[1:]  # "#property" の後ろがカラム名
            break
    if not header:
        raise ValueError(f"Header (#property row) not found: {csv_path.name}")

    station_map = {}

    for row in rows:
        if not row:
            continue
        first = row[0].strip()
        if not first.isdigit():
            continue

        # 先頭は便番号なので捨てる
        row2 = row[1:]
        values = row2 + [""] * (len(header) - len(row2))
        data = dict(zip(header, values))

        train_no = (data.get("列車番号") or "").strip()
        dest = (data.get("行き先") or "").strip()
        train_type = (data.get("種別") or "").strip()
        note = (data.get("備考") or "").strip()

        for key, value in data.items():
            if not key:
                continue
            if not (key.endswith("_発") or key.endswith("_着")):
                continue

            raw_time = (value or "").strip()
            if raw_time == "" or raw_time == "→":
                continue

            station = key.replace("_発", "").replace("_着", "")
            event = "発" if key.endswith("_発") else "着"
            norm_time = _normalize_time(raw_time)

            station_map.setdefault(station, []).append(
                {
                    "time": norm_time,
                    "dest": dest,
                    "train_type": train_type,
                    "note": note,
                    "direction": direction,  # ★追加
                    "event": event,
                    # "train_no": train_no,  # いらないならコメントのまま
                }
            )

    # ソート
    for items in station_map.values():
        items.sort(key=lambda x: (x["time"], x["event"], x["dest"]))

    return station_map


def _load_csv_to_cache():
    global _station_map
    _station_map = {}

    kudari_map = _read_fukutetsu_csv(CSV_KUDARI, "kudari")
    nobori_map = _read_fukutetsu_csv(CSV_NOBORI, "nobori")

    # マージ
    stations = set(kudari_map.keys()) | set(nobori_map.keys())
    for st in stations:
        _station_map[st] = (kudari_map.get(st, []) + nobori_map.get(st, []))
        _station_map[st].sort(key=lambda x: (x["direction"], x["time"], x["event"], x["dest"]))


def get_station_names():
    global _station_map
    if _station_map is None:
        _load_csv_to_cache()
    return sorted(_station_map.keys())


def get_timetable_by_station(station: str, direction: str | None = None):
    global _station_map
    if _station_map is None:
        _load_csv_to_cache()

    items = _station_map.get(station, [])

    if direction in ("kudari", "nobori"):
        items = [x for x in items if x.get("direction") == direction]

    dep = [x for x in items if x.get("event") == "発"]
    if dep:
        # ★コピーして event を落とす（キャッシュは触らない）
        return [{k: v for k, v in x.items() if k != "event"} for x in dep]

    arr = [x for x in items if x.get("event") == "着"]
    return [{k: v for k, v in x.items() if k != "event"} for x in arr]


def debug_summary():
    global _cache
    if _cache is None:
        _load_cache()

    k = _cache["kudari"]
    n = _cache["nobori"]

    return {
        "kudari_csv": str(CSV_KUDARI),
        "nobori_csv": str(CSV_NOBORI),
        "kudari_station_count": len(k),
        "nobori_station_count": len(n),
        "kudari_sample_stations": sorted(list(k.keys()))[:20],
        "nobori_sample_stations": sorted(list(n.keys()))[:20],
    }
