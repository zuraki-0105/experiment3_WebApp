document.addEventListener("DOMContentLoaded", () => {
  // ====== 地図の初期化 ======
  const map = L.map("map").setView([36.0641, 136.2193], 14);

  // Tile （背景地図）
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(map);

  // マーカーを保存する配列
  let restaurantsMarkers = [];
  let stationMarkers = [];
  let busStopMarkers = [];

  // fetchしてJSONを読む
  async function fetchJson(url) {
    const res = await fetch(url);

    // 原因表示
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`${url} failed: ${res.status} ${res.statusText}\n${text}`);
    }

    return res.json();
  }

  // 緯度経度のバリデーション
  function toLatLng(lat, lng) {
    const la = Number(lat);
    const ln = Number(lng);
    if (!Number.isFinite(la) || !Number.isFinite(ln)) return null;
    return [la, ln];
  }

  // /restaurants API からデータ取得
  async function loadRestaurants() {
    const data = await fetchJson("/restaurants");
    const restaurants = data.restaurants ?? [];

    console.log("API restaurants count:", restaurants.length);
    console.log("restaurants[0] =", restaurants[0]);

    restaurantsMarkers.forEach((m) => map.removeLayer(m));
    restaurantsMarkers = [];

    

    // マーカー作成
    restaurants.forEach((r, idx) => {
      const ll = toLatLng(r.lat, r.lng);
      // 緯度・経度が不正なデータはスキップ
      if (!ll) {
        console.warn("restaurants invalid lat/lng:", idx, r);
        return;
      }

      
      const nearestStation = findNearest(ll, stationMarkers); // 最も近い駅マーカーを取得
      const nearestBusStop = findNearest(ll, busStopMarkers); // 最も近いバス停マーカーを取得

      const nearestStationText = nearestStation
        ? `${nearestStation.marker.name}（${nearestStation.distance} m）`
        : "なし";

      const nearestBusStopText = nearestBusStop
        ? `${nearestBusStop.marker.name}（${nearestBusStop.distance} m）`
        : "なし";

      const raw = r.segment ?? r.business_type ?? "";
      const cate = classifyBySegment(raw);
      let cateStr = "";

      // 日本語表示
      if(cate === "restaurant") cateStr = "レストラン";
      else if(cate === "drugstore") cateStr = "ドラッグストア";
      else if(cate === "convenience") cateStr = "コンビニ";
      else if(cate === "cafe") cateStr = "カフェ・喫茶店";
      else if(cate === "super") cateStr = "スーパー";
      else cateStr = "None";

      //  ポップアップの表示・内容
      const marker = L.marker(ll).bindPopup(
        `<b>${r.name ?? ""}</b><br>
        ${r.address ?? ""}<br>
        (${cateStr})<br><br>最寄り駅　　  ： ${nearestStationText}<br>
        最寄りバス停  ： ${nearestBusStopText}`
      );

      // クリック時
      marker.on("click", () => {
        if (nearestStation) {
          showStationTimetable(nearestStation.marker.stationName);
        }
      });

      marker.category = cate; // フィルタ用
      marker.addTo(map);
      restaurantsMarkers.push(marker);
    });

    console.log("restaurant markers:", restaurantsMarkers.length);
  }

  // 駅データを取得し、地図上にマーカーとして表示する
  async function loadStations() {

    const data = await fetchJson("/stations");
    const stations = data.stations ?? [];

    console.log("API stations count:", stations.length);
    console.log("stations[0] =", stations[0]);

    // 駅のアイコン設定
    const icon = L.divIcon({
      html: "🚉",
      className: "",
      iconSize: [20, 20],
    });

    // 初期化
    stationMarkers.forEach((m) => map.removeLayer(m));
    stationMarkers = [];

    // マーカー生成
    stations.forEach((s, idx) => {

      const ll = toLatLng(s.lat, s.lng);
      if (!ll) {
        console.warn("stations invalid lat/lng:", idx, s);
        return;
      }

      const marker = L.marker(ll, { icon }).bindPopup(
        `<b>${s.name ?? ""}</b><br>
        ${s.line ?? ""}<br>
        ${s.company ?? ""}`
      );

      // 時刻表API用のキーを作成
      let key = (s.name ?? "")
        .replace(/（.*?）/g, "")     // カッコ除去
        .replace(/\s+/g, "")         // 空白除去
        .trim();

      // 福井駅だけは「駅」を消さない（CSV側が福井駅なので）
      if (key !== "福井駅") {
        key = key.replace(/駅$/, "");
      }

      marker.stationName = key;


      // マーカークリック時
      marker.on("click", async () => {
      const station = marker.stationName;

      try {
          // くだり・のぼりの時刻表を取得
          const [kRes, nRes] = await Promise.all([
            fetchJson(`/timetable?station=${encodeURIComponent(station)}&direction=kudari`),
            fetchJson(`/timetable?station=${encodeURIComponent(station)}&direction=nobori`),
          ]);

          const kudari = kRes.items ?? [];
          const nobori = nRes.items ?? [];

          // 列車種別の変換
          function prettyTrainType(type) {
            if (type === "電") return "普通";
            return type;
          }

          // 時刻表リストをHTML表示用に整形
          function render(list) {
            if (!list.length) return "（なし）";
            return list.slice(0, 30).map(x => {
              const time = x.time ?? "";
              const type = prettyTrainType(x.train_type ?? "");
              const dest = x.dest ?? "";
              const note = x.note ? ` / ${x.note}` : "";
              return `${time} ${type}：${dest}${note}`;
            }).join("<br>");
          }


          if (kudari.length === 0 && nobori.length === 0) {
            marker
              .bindPopup(`<b>${station}</b><br>時刻表データが見つかりません`)
              .openPopup();
            return;
          }
          
          // 時刻表をポップアップに表示
          marker.bindPopup(
            `<b>${station}</b><br>` +
            `<div style="max-height:260px; overflow:auto; font-size:12px; line-height:1.4;">` +
            `<b>くだり</b><br>${render(kudari)}<br><br>` +
            `<b>のぼり</b><br>${render(nobori)}` +
            `</div>`
          ).openPopup();

        } catch (e) {
          console.error(e);
          marker
            .bindPopup(`<b>${station}</b><br>時刻表の取得に失敗しました`)
            .openPopup();
        }
      });

      marker.name = s.name;

      // 地図にマーカー追加
      marker.addTo(map);
      stationMarkers.push(marker);
    });

    console.log("station markers:", stationMarkers.length);
  }

  // バス停データからマーカーを生成
  async function loadBusStops() {
    // データ取得
    const data = await fetchJson("/bus_stops");
    const busStops = data.bus_stops ?? [];

    console.log("API bus_stops count:", busStops.length);
    console.log("bus_stops[0] =", busStops[0]);

    // バス停アイコン設定
    const icon = L.divIcon({
      html: "🚌",
      className: "",
      iconSize: [16, 16],
    });

    // 初期化
    busStopMarkers.forEach((m) => map.removeLayer(m));
    busStopMarkers = [];

    busStops.forEach((b, idx) => {
      // 緯度経度チェック
      const ll = toLatLng(b.lat, b.lng);
      if (!ll) {
        console.warn("bus_stops invalid lat/lng:", idx, b);
        return;
      }

      // マーカーを作成
      const marker = L.marker(ll, { icon }).bindPopup(`<b>${b.name ?? ""}</b>`);
      marker.name = b.name;
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

  // 時刻表をサイドパネルに表示
  async function showStationTimetable(stationName) {
    const container = document.getElementById("timetable-content");
    container.innerHTML = "読み込み中…";

    try {
      const [kRes, nRes] = await Promise.all([
        fetchJson(`/timetable?station=${encodeURIComponent(stationName)}&direction=kudari`),
        fetchJson(`/timetable?station=${encodeURIComponent(stationName)}&direction=nobori`)
      ]);

      const kudari = kRes.items ?? [];
      const nobori = nRes.items ?? [];

      function prettyTrainType(type) {
        if (type === "電") return "普通";
        return type;
      }

      function render(list) {
        if (!list.length) return "（なし）";
        return list.slice(0, 30).map(x => {
          const time = x.time ?? "";
          const type = prettyTrainType(x.train_type ?? "");
          const dest = x.dest ?? "";
          const note = x.note ? ` / ${x.note}` : "";
          return `${time} ${type}：${dest}${note}`;
        }).join("<br>");
      }

      if (!kudari.length && !nobori.length) {
        container.innerHTML = `<b>${stationName}</b><br>時刻表データがありません`;
        return;
      }

      // 時刻表表示
      container.innerHTML = `
        <b>${stationName}</b><br><br>
        <b>くだり</b><br>${render(kudari)}<br><br>
        <b>のぼり</b><br>${render(nobori)}
      `;

    } catch (e) {
      console.error(e);
      container.innerHTML = "時刻表の取得に失敗しました";
    }
  }


  // チェックボックスにイベント追加
  document.querySelectorAll("#controls input, .controls input").forEach((cb) => {
    cb.addEventListener("change", applyFilter);
  });

  // 初期読み込み
  (async () => {
    try {
      await loadStations();
      await loadBusStops();
      await loadRestaurants();
    } catch (e) {
      console.error("load failed:", e);
    }
    applyFilter();
  })();
});