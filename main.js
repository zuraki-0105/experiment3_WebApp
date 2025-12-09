// -------------------------
// 地図を作成（福井市中心）
// -------------------------
const map = L.map('map').setView([36.0641, 136.2193], 14);

// OpenStreetMap のタイル読み込み
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
}).addTo(map);

// マーカーを保持するための配列
let markers = [];

// -------------------------
// API から店舗データを取得
// -------------------------
async function loadRestaurants() {
    const res = await fetch("/restaurants");
    const data = await res.json();
    return data;
}

// -------------------------
// マーカー表示処理
// -------------------------
function showMarkers(restaurants) {
    // 既存マーカー消す
    markers.forEach(m => map.removeLayer(m));
    markers = [];

    restaurants.forEach(r => {
        const marker = L.marker([r.latitude, r.longitude])
            .addTo(map)
            .bindPopup(`<b>${r.name}</b><br>${r.address ?? ""}<br>カテゴリ: ${r.segment}`);

        markers.push(marker);
    });
}

// -------------------------
// フィルタ適用
// -------------------------
function applyFilter(restaurants) {
    // チェックされたカテゴリを取得
    const checked = Array.from(document.querySelectorAll("#filters input:checked"))
        .map(i => i.value);

    // チェックされた segment のみ表示
    const filtered = restaurants.filter(r => checked.includes(r.segment));
    showMarkers(filtered);
}

// -------------------------
// メイン処理
// -------------------------
(async function () {
    const restaurants = await loadRestaurants();

    // 初回表示（全件）
    showMarkers(restaurants);

    // フィルタUIのイベント
    document.querySelectorAll("#filters input").forEach(cb => {
        cb.addEventListener("change", () => applyFilter(restaurants));
    });
})();
