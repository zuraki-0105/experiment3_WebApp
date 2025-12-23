import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

CSV_FUKUTETSU_KUDARI = BASE_DIR / "opendata" / "fukutetsu_time_kudari.csv"
CSV_FUKUTETSU_NOBORI = BASE_DIR / "opendata" / "fukutetsu_time_nobori.csv"
CSV_KATSUYAMA_KUDARI = BASE_DIR / "opendata" / "katsuyama_time_kudari.csv"
CSV_KATSUYAMA_NOBORI = BASE_DIR / "opendata" / "katsuyama_time_nobori.csv"
CSV_MIKUNI_KUDARI = BASE_DIR / "opendata" / "mikuni_time_kudari.csv"
CSV_MIKUNI_NOBORI = BASE_DIR / "opendata" / "mikuni_time_nobori.csv"

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
    形式A: 駅名_発/駅名_着 の列がある（既存の福鉄CSV想定）
    形式B: 駅名そのものが列名（勝山線/三国線のCSVがこれ）
    direction: "kudari" / "nobori"
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"timetable CSV not found: {csv_path.resolve()}")

    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))

    header = None
    for row in rows:
        if row and row[0].startswith("#property"):
            header = row[1:]
            break
    if not header:
        raise ValueError(f"Header (#property row) not found: {csv_path.name}")

    station_map = {}

    # ★形式判定：_発/_着 が1個でもあれば形式A
    is_format_a = any(h.endswith("_発") or h.endswith("_着") for h in header)

    for row in rows:
        if not row:
            continue
        first = (row[0] or "").strip()
        if not first.isdigit():
            continue

        # 先頭は便番号なので捨てる（勝山/三国も 1,2,3... なのでOK）
        row2 = row[1:]
        values = row2 + [""] * (len(header) - len(row2))
        data = dict(zip(header, values))

        if is_format_a:
            # ===== 形式A（既存）=====
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
                        "direction": direction,
                        "event": event,
                    }
                )

        else:
            # ===== 形式B（勝山線/三国線）=====
            # 列: 列車番号, 列車種別, 始発～行先, 以降が駅名列
            dest = (data.get("始発～行先") or "").strip()
            train_type = (data.get("列車種別") or "").strip()
            note = ""  # この形式には備考列が無さそう

            # 駅列は header の4列目以降
            for station in header[3:]:
                if not station:
                    continue
                raw_time = (data.get(station) or "").strip()
                if raw_time == "" or raw_time == "→":
                    continue

                norm_time = _normalize_time(raw_time)

                station_map.setdefault(station, []).append(
                    {
                        "time": norm_time,
                        "dest": dest,
                        "train_type": train_type,
                        "note": note,
                        "direction": direction,
                        "event": "発",  # このCSVは駅ごとの時刻＝基本「発」として扱う
                    }
                )

    # ソート
    for items in station_map.values():
        items.sort(key=lambda x: (x["time"], x["event"], x["dest"]))

    return station_map



def _merge_into_station_map(target: dict, src: dict):
    """station_map同士を target にマージ"""
    for st, items in src.items():
        target.setdefault(st, []).extend(items)


def _load_csv_to_cache():
    global _station_map
    _station_map = {}

    # ★全部読む（追加CSVもここ）
    maps = [
        _read_fukutetsu_csv(CSV_FUKUTETSU_KUDARI, "kudari"),
        _read_fukutetsu_csv(CSV_FUKUTETSU_NOBORI, "nobori"),
        _read_fukutetsu_csv(CSV_KATSUYAMA_KUDARI, "kudari"),
        _read_fukutetsu_csv(CSV_KATSUYAMA_NOBORI, "nobori"),
        _read_fukutetsu_csv(CSV_MIKUNI_KUDARI, "kudari"),
        _read_fukutetsu_csv(CSV_MIKUNI_NOBORI, "nobori"),
    ]

    for m in maps:
        _merge_into_station_map(_station_map, m)

    # ★全駅ぶんソート
    for st in _station_map.keys():
        _station_map[st].sort(
            key=lambda x: (x.get("direction", ""), x.get("time", ""), x.get("event", ""), x.get("dest", ""))
        )


def get_station_names():
    global _station_map
    if _station_map is None:
        _load_csv_to_cache()
    return sorted(_station_map.keys())


def get_timetable_by_station(station: str, direction: str | None = None):
    """
    direction:
      None -> 上下まとめて返す
      "kudari"/"nobori" -> 片方だけ

    さらに「発だけほしい」仕様:
      そのdirection内に発があれば発だけ返す。なければ着だけ返す。
    """
    global _station_map
    if _station_map is None:
        _load_csv_to_cache()

    items = _station_map.get(station, [])

    if direction in ("kudari", "nobori"):
        items = [x for x in items if x.get("direction") == direction]

    dep = [x for x in items if x.get("event") == "発"]
    if dep:
        return [{k: v for k, v in x.items() if k != "event"} for x in dep]

    arr = [x for x in items if x.get("event") == "着"]
    return [{k: v for k, v in x.items() if k != "event"} for x in arr]


def debug_summary():
    """今のキャッシュ状態を確認する用（/timetable_debug 用）"""
    global _station_map
    if _station_map is None:
        _load_csv_to_cache()

    return {
        "csv_files": {
            "fukutetsu_kudari": str(CSV_FUKUTETSU_KUDARI),
            "fukutetsu_nobori": str(CSV_FUKUTETSU_NOBORI),
            "katsuyama_kudari": str(CSV_KATSUYAMA_KUDARI),
            "katsuyama_nobori": str(CSV_KATSUYAMA_NOBORI),
            "mikuni_kudari": str(CSV_MIKUNI_KUDARI),
            "mikuni_nobori": str(CSV_MIKUNI_NOBORI),
        },
        "station_count": len(_station_map),
        "sample_stations": sorted(list(_station_map.keys()))[:30],
        "sample_items_first_station": _station_map.get(sorted(_station_map.keys())[0], [])[:5] if _station_map else [],
    }
