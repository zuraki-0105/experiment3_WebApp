// ====== 地図の初期化 ======
const map = L.map('map').setView([36.0641, 136.2193], 14);

// Tile （背景地図）
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
}).addTo(map);

// マーカーを保存する配列
let markerList = [];


// ====== /restaurants API からデータ取得 ======
async function loadRestaurants() {
    const res = await fetch("/restaurants");
    const data = await res.json();

    const restaurants = data.restaurants;

    console.log("APIから取得したデータ:", restaurants);

    // マーカー作成
    restaurants.forEach(r => {
        const marker = L.marker([r.lat, r.lng])
            .bindPopup(`<b>${r.name}</b><br>${r.address}<br>${r.segment}`);

        marker.segment = r.segment;  // ← フィルタ用に保存

        marker.addTo(map);
        markerList.push(marker);
    });
}


// ====== フィルタ処理 ======
function applyFilter() {
    const showStudent = document.getElementById("filter-student").checked;
    const showFamily  = document.getElementById("filter-family").checked;

    markerList.forEach(marker => {
        const seg = marker.segment;

        // 表示条件
        const shouldShow =
            (seg === "student" && showStudent) ||
            (seg === "family"  && showFamily);

        if (shouldShow) {
            marker.addTo(map);
        } else {
            map.removeLayer(marker);
        }
    });
}


// ====== チェックボックスにイベント追加 ======
document.getElementById("filter-student").addEventListener("change", applyFilter);
document.getElementById("filter-family").addEventListener("change", applyFilter);


// 初期読み込み
loadRestaurants();
