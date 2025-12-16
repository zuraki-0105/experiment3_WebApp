# classification.py

def classify_by_segment(segment: str) -> str:
    """
    segment の文字列をもとにカテゴリを返す
    完全一致ではなく「含む」で判定する
    """

    if not segment:
        return "other"

    s = segment.strip()

    # ドラッグストアaaa
    if "ドラッグ" in s:
        return "drugstore"

    # コンビニ
    if "コンビニ" in s:
        return "convenience"

    # 喫茶・カフェ・バー・ラウンジ
    if any(k in s for k in ["喫茶", "カフェ", "バー", "ラウンジ"]):
        return "cafe_bar"

    # スーパー・小売
    if any(k in s for k in ["スーパー", "小売", "百貨店"]):
        return "super_retail"

    return "other"
