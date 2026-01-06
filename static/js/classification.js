// データの業種に対して分類わけ
window.classifyBySegment = function(segment){
  if (!segment) return "restaurant";
  const s = segment.trim();

  if (s.includes("ドラッグ")) return "drugstore";
  if (s.includes("コンビニ")) return "convenience";
  if (s.includes("喫茶") || s.includes("カフェ") || s.includes("バー") || s.includes("ラウンジ"))
    return "cafe";
  if (s.includes("スーパー") || s.includes("小売") || s.includes("百貨店"))
    return "super";

  return "restaurant";
}
