import csv
from pathlib import Path

# ★ここだけ自分の配置に合わせて変えてOK
CSV_PATH = Path("opendata/fukutetsu_kudari.csv")

_station_map = None  # {station: [items...]}


def _normalize_time(t: str) -> str:
    """'6:02' -> '06:02' みたいに揃える（揃わなくても動くけど並び替えが安定する）"""
    t = (t or "").strip()
    if not t or t == "→":
        return ""
    # 例: 5:30, 05:30, 15:02
    if ":" in t:
        h, m = t.split(":", 1)
        if h.isdigit() and m.isdigit():
            return f"{int(h):02d}:{int(m):02d}"
    return t


def _load_csv_to_cache():
    global _station_map
    _station_map = {}

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"timetable CSV not found: {CSV_PATH.resolve()}")

    # # で始まるメタ行を除外してDictReaderに渡す
    def rows_without_meta(fp):
        for line in fp:
            if line.startswith("#"):
                continue
            yield line

    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(rows_without_meta(f))
        for row in reader:
            train_no = (row.get("列車番号") or "").strip()
            dest = (row.get("行き先") or "").strip()
            train_type = (row.get("種別") or "").strip()
            note = (row.get("備考") or "").strip()

            # 各駅カラム（xxx_発 / xxx_着）を走査
            for key, value in row.items():
                if not key:
                    continue
                if not (key.endswith("_発") or key.endswith("_着")):
                    continue

                raw_time = (value or "").strip()
                if raw_time == "" or raw_time == "→":
                    continue

                station = key.replace("_発", "").replace("_着", "")
                norm_time = _normalize_time(raw_time)

                _station_map.setdefault(station, []).append(
                    {
                        "time": norm_time,
                        "train_no": train_no,
                        "dest": dest,
                        "train_type": train_type,
                        "note": note,
                        "event": "発" if key.endswith("_発") else "着",
                        "col": key,  # デバッグ用
                    }
                )

    # 時刻順（同時刻なら train_no などで安定化）
    for items in _station_map.values():
        items.sort(key=lambda x: (x["time"], x["event"], x["train_no"]))


def get_timetable_by_station(station: str):
    global _station_map
    if _station_map is None:
        _load_csv_to_cache()
    return _station_map.get(station, [])


def reload_cache():
    """CSVを更新したときに再読み込みしたい場合用（任意）"""
    _load_csv_to_cache()
