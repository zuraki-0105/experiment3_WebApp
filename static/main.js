document.addEventListener("DOMContentLoaded", () => {
  // ====== 地図の初期化 ======
  const map = L.map("map").setView([36.0641, 136.2193], 14);

  // Tile （背景地図）aaa
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(map);

  // マーカーを保存する配列
  let restaurantsMarkers = [];
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
    restaurantsMarkers.forEach((m) => map.removeLayer(m));
    restaurantsMarkers = [];

    // マーカー作成
    restaurants.forEach((r, idx) => {
      const ll = toLatLng(r.lat, r.lng);
      if (!ll) {
        console.warn("restaurants invalid lat/lng:", idx, r);
        return;
      }

      const raw = r.segment ?? r.business_type ?? "";
      const cate = classifyBySegment(raw);
      let cateStr = "";

      if(cate === "restaurant") cateStr = "レストラン";
      else if(cate === "drugstore") cateStr = "ドラッグストア";
      else if(cate === "convenience") cateStr = "コンビニ";
      else if(cate === "cafe") cateStr = "カフェ・喫茶店";
      else if(cate === "super") cateStr = "スーパー";
      else cateStr = "None";

      const marker = L.marker(ll).bindPopup(
        `<b>${r.name ?? ""}</b><br>${r.address ?? ""}<br>(${cateStr})<br><br>最寄り駅　　  ： <br>最寄りバス停  ： `
      );

            // ====== 駅名を保持して、クリックで時刻表取得 ======
      marker.stationName = s.name ?? "";

      marker.on("click", async () => {
        const station = marker.stationName;

        try {
          const data = await fetchJson(`/timetable?station=${encodeURIComponent(station)}`);
          const items = data.items ?? [];

          if (items.length === 0) {
            marker
              .bindPopup(`<b>${station}</b><br>時刻表データが見つかりません`)
              .openPopup();
            return;
          }

          // 表示用（長くなりすぎないように最大60件）
          const lines = items.slice(0, 60).map(x => {
            const time = x.time ?? "";
            const trainNo = x.train_no ?? "";
            const type = x.train_type ?? "";
            const dest = x.dest ?? "";
            const note = x.note ? ` / ${x.note}` : "";
            const event = x.event ? `(${x.event})` : "";
            return `${time}${event} ${trainNo} ${type} →${dest}${note}`;
          });

          marker.bindPopup(
            `<b>${station}</b><br>` +
            `<div style="max-height:220px; overflow:auto; font-size:12px; line-height:1.4;">` +
            lines.join("<br>") +
            `</div>`
          ).openPopup();
        } catch (e) {
          console.error(e);
          marker
            .bindPopup(`<b>${station}</b><br>時刻表の取得に失敗しました`)
            .openPopup();
        }
      });

      marker.category = cate; // フィルタ用
      marker.addTo(map);
      restaurantsMarkers.push(marker);
    });

    console.log("restaurant markers:", restaurantsMarkers.length);
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
    const showConvenience = document.getElementById("filter-convenience")?.checked ?? false;
    const showCafe        = document.getElementById("filter-cafe")?.checked ?? false;
    const showDrugstore   = document.getElementById("filter-drugstore")?.checked ?? false;
    const showSuper       = document.getElementById("filter-super")?.checked ?? false;
    const showOther       = document.getElementById("filter-other")?.checked ?? false;
    const showStations    = document.getElementById("filter-stations")?.checked ?? false;
    const showBusStops    = document.getElementById("filter-bus-stops")?.checked ?? false;

    // 駅
    stationMarkers.forEach((m) =>
      showStations ? m.addTo(map) : map.removeLayer(m)
    );

    // バス停
    busStopMarkers.forEach((m) =>
      showBusStops ? m.addTo(map) : map.removeLayer(m)
    );

    // 飲食店
    restaurantsMarkers.forEach((marker) => {
      const cate = marker.category ?? "";

      let shouldShow = false;

      if (cate === "convenience") shouldShow = showConvenience;
      else if (cate === "cafe") shouldShow = showCafe;
      else if (cate === "drugstore") shouldShow = showDrugstore;
      else if (cate === "super") shouldShow = showSuper;
      else shouldShow = showOther;

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
});