// 座標から距離を計算
window.findNearest = function(latlng, markers) {
  let nearest = null;
  let minDist = Infinity;

  markers.forEach((m) => {
    const d = L.latLng(latlng).distanceTo(m.getLatLng());
    if (d < minDist) {
      minDist = d;
      nearest = m;
    }
  });

  if (!nearest) return null;

  return {
    marker: nearest,
    distance: Math.round(minDist), // メートル
  };
}
