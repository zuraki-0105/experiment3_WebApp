// ====== 地図の初期化 ======
const map = L.map('map').setView([36.0641, 136.2193], 14);

// Tile （背景地図）
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
}).addTo(map);

// マーカーを保存する配列
let markerList = [];
let stationMarkers = [];
let busStopMarkers = [];


// ====== /restaurants API からデータ取得 ======
async function loadRestaurants() {
  const res = await fetch("/restaurants");
  const data = await res.json();

  const restaurants = data.restaurants;
  console.log("APIから取得したデータ:", restaurants);
  console.log("restaurants[0] =", restaurants?.[0]);

  // 初期化
  markerList.forEach(m => map.removeLayer(m));
  markerList = [];

  // マーカー作成
  restaurants.forEach(r => {
    const cate = r.category ?? r.segment ?? r.business_type ?? r.type ?? "";

    const marker = L.marker([r.lat, r.lng])
      .bindPopup(`<b>${r.name}</b><br>${r.address}<br>${cate}`);

    marker.category = cate; // フィルタ用
    marker.addTo(map);
    markerList.push(marker);
  });
}

async function loadStations() {
  const res = await fetch("/stations");
  const data = await res.json();

  const icon = L.divIcon({
    html: "🚉",
    className: "",
    iconSize: [20, 20]
  });

  // 初期化（再読み込み時のため）
  stationMarkers.forEach(m => map.removeLayer(m));
  stationMarkers = [];

  data.stations.forEach(s => {
    const marker = L.marker([s.lat, s.lng], { icon })
      .bindPopup(`<b>${s.name}</b><br>${s.line}<br>${s.company}`);

    marker.addTo(map);
    stationMarkers.push(marker);
  });
}

async function loadBusStops() {
  const res = await fetch("/bus_stops");
  const data = await res.json();

  const icon = L.divIcon({
    html: "🚌",
    className: "",
    iconSize: [16, 16]
  });

  // 初期化（再読み込み時のため）
  busStopMarkers.forEach(m => map.removeLayer(m));
  busStopMarkers = [];

  data.bus_stops.forEach(b => {
    const marker = L.marker([b.lat, b.lng], { icon })
      .bindPopup(`<b>${b.name}</b>`);

    // 初期状態は「チェックボックスの状態に従う」方が自然なので、
    // ここでは addTo(map) しない（applyFilterが制御する）
    busStopMarkers.push(marker);
  });
}


// ====== フィルタ処理 ======
function applyFilter() {
  // 学生/ファミリー（コメントアウト解除）
  const showStudent = document.getElementById("filter-student")?.checked ?? false;
  const showFamily  = document.getElementById("filter-family")?.checked ?? false;

  const showConvenience = document.getElementById("filter-convenience")?.checked ?? false;
  const showCafe        = document.getElementById("filter-cafe")?.checked ?? false;
  const showDrugstore   = document.getElementById("filter-drugstore")?.checked ?? false;
  const showSuper       = document.getElementById("filter-super")?.checked ?? false;

  // 駅
  const showStations = document.getElementById("filter-stations")?.checked ?? false;
  stationMarkers.forEach(m => showStations ? m.addTo(map) : map.removeLayer(m));

  // バス停
  const showBusStops = document.getElementById("filter-bus-stops")?.checked ?? false;
  busStopMarkers.forEach(m => showBusStops ? m.addTo(map) : map.removeLayer(m));

  // 飲食店：何もチェックが入ってないなら「全部表示」にする（事故防止）
  const anyRestaurantChecked =
    showStudent || showFamily || showConvenience || showCafe || showDrugstore || showSuper;

  markerList.forEach(marker => {
    const cate = marker.category;

    const shouldShow =
      !anyRestaurantChecked ||
      (cate === "student"     && showStudent) ||
      (cate === "family"      && showFamily) ||
      (cate === "convenience" && showConvenience) ||
      (cate === "cafe"        && showCafe) ||
      (cate === "drugstore"   && showDrugstore) ||
      (cate === "super"       && showSuper);

    shouldShow ? marker.addTo(map) : map.removeLayer(marker);
  });
}


// ====== チェックボックスにイベント追加 ======
// ※HTML側を「id=controls」じゃなく「class=controls」にしてね！
document.querySelectorAll(".controls input").forEach(cb => {
  cb.addEventListener("change", applyFilter);
});


// 初期読み込み
(async () => {
  await loadRestaurants();
  await loadStations();
  await loadBusStops();
  applyFilter(); // ← 初期状態を反映
})();
