// ====== 地図の初期化 ======
const map = L.map("map").setView([36.0641, 136.2193], 14);

// Tile （背景地図）
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
}).addTo(map);

// マーカーを保存する配列
let markerList = [];
let stationMarkers = [];
let busStopMarkers = [];

// ====== 共通：fetchしてJSONを安全に読む ======
async function fetchJson(url) {
  const res = await fetch(url);

  // ここで落とさず、原因が見える形で例外化
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${url} failed: ${res.status} ${res.statusText}\n${text}`);
  }

  return res.json();
}

// ====== 共通：緯度経度のバリデーション ======
function toLatLng(lat, lng) {
  const la = Number(lat);
  const ln = Number(lng);
  if (!Number.isFinite(la) || !Number.isFinite(ln)) return null;
  return [la, ln];
}

// ====== /restaurants API からデータ取得 ======
async function loadRestaurants() {
  const data = await fetchJson("/restaurants");
  const restaurants = data.restaurants ?? [];

  console.log("API restaurants count:", restaurants.length);
  console.log("restaurants[0] =", restaurants[0]);

  // 初期化
  markerList.forEach((m) => map.removeLayer(m));
  markerList = [];

  // マーカー作成
  restaurants.forEach((r, idx) => {
    const ll = toLatLng(r.lat, r.lng);
    if (!ll) {
      console.warn("restaurants invalid lat/lng:", idx, r);
      return;
    }

    const cate = r.category ?? r.segment ?? r.business_type ?? r.type ?? "";

    const marker = L.marker(ll).bindPopup(
      `<b>${r.name ?? ""}</b><br>${r.address ?? ""}<br>${cate}`
    );

    marker.category = cate; // フィルタ用
    marker.addTo(map);
    markerList.push(marker);
  });

  console.log("restaurant markers:", markerList.length);
}

async function loadStations() {
  const data = await fetchJson("/stations");
  const stations = data.stations ?? [];

  console.log("API stations count:", stations.length);
  console.log("stations[0] =", stations[0]);

  const icon = L.divIcon({
    html: "🚉",
    className: "",
    iconSize: [20, 20],
  });

  // 初期化
  stationMarkers.forEach((m) => map.removeLayer(m));
  stationMarkers = [];

  stations.forEach((s, idx) => {
    const ll = toLatLng(s.lat, s.lng);
    if (!ll) {
      console.warn("stations invalid lat/lng:", idx, s);
      return;
    }

    const marker = L.marker(ll, { icon }).bindPopup(
      `<b>${s.name ?? ""}</b><br>${s.line ?? ""}<br>${s.company ?? ""}`
    );

    marker.addTo(map);
    stationMarkers.push(marker);
  });

  console.log("station markers:", stationMarkers.length);
}

async function loadBusStops() {
  const data = await fetchJson("/bus_stops");
  const busStops = data.bus_stops ?? [];

  console.log("API bus_stops count:", busStops.length);
  console.log("bus_stops[0] =", busStops[0]);

  const icon = L.divIcon({
    html: "🚌",
    className: "",
    iconSize: [16, 16],
  });

  // 初期化
  busStopMarkers.forEach((m) => map.removeLayer(m));
  busStopMarkers = [];

  busStops.forEach((b, idx) => {
    const ll = toLatLng(b.lat, b.lng);
    if (!ll) {
      console.warn("bus_stops invalid lat/lng:", idx, b);
      return;
    }

    const marker = L.marker(ll, { icon }).bindPopup(`<b>${b.name ?? ""}</b>`);
    // addTo(map) は applyFilter が制御
    busStopMarkers.push(marker);
  });

  console.log("bus stop markers:", busStopMarkers.length);
}

// ====== フィルタ処理 ======
function applyFilter() {
  // 学生/ファミリー
  const showStudent = document.getElementById("filter-student")?.checked ?? false;
  const showFamily = document.getElementById("filter-family")?.checked ?? false;

  const showConvenience =
    document.getElementById("filter-convenience")?.checked ?? false;
  const showCafe = document.getElementById("filter-cafe")?.checked ?? false;
  const showDrugstore =
    document.getElementById("filter-drugstore")?.checked ?? false;
  const showSuper = document.getElementById("filter-super")?.checked ?? false;

  // 駅
  const showStations =
    document.getElementById("filter-stations")?.checked ?? false;
  stationMarkers.forEach((m) =>
    showStations ? m.addTo(map) : map.removeLayer(m)
  );

  // バス停
  const showBusStops =
    document.getElementById("filter-bus-stops")?.checked ?? false;
  busStopMarkers.forEach((m) =>
    showBusStops ? m.addTo(map) : map.removeLayer(m)
  );

  // 飲食店：何もチェックが入ってないなら「全部表示」
  const anyRestaurantChecked =
    showStudent ||
    showFamily ||
    showConvenience ||
    showCafe ||
    showDrugstore ||
    showSuper;

  markerList.forEach((marker) => {
    const cate = marker.category ?? "";

    // ★デバッグしやすいように「未知カテゴリは表示」にしておく（必要なら消してOK）
    const shouldShow =
      !anyRestaurantChecked ||
      cate === "" ||
      (cate === "student" && showStudent) ||
      (cate === "family" && showFamily) ||
      (cate === "convenience" && showConvenience) ||
      (cate === "cafe" && showCafe) ||
      (cate === "drugstore" && showDrugstore) ||
      (cate === "super" && showSuper);

    shouldShow ? marker.addTo(map) : map.removeLayer(marker);
  });
}

// ====== チェックボックスにイベント追加 ======
// HTMLが「id=controls」でも「class=controls」でも拾えるように暫定対応
document.querySelectorAll("#controls input, .controls input").forEach((cb) => {
  cb.addEventListener("change", applyFilter);
});

// 初期読み込み
(async () => {
  const results = await Promise.allSettled([
    loadRestaurants(),
    loadStations(),
    loadBusStops(),
  ]);
  console.log("load results:", results);

  // rejected があるなら中身を出す
  results.forEach((r, i) => {
    if (r.status === "rejected") console.error("load failed:", i, r.reason);
  });

  applyFilter();
})();
