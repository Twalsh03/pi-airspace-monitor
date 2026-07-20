const map = L.map("map").setView([37.75, -122.42], 10);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19, attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);
const markers = new Map();
const colors = { aircraft: "#2674d9", drone: "#d93434", pilot: "#e68a25" };
const status = document.getElementById("status");
let reconnectDelay = 1000;

function popup(track) {
  const altitude = track.alt_m == null ? "—" :
    `${track.alt_m.toFixed(1)} m${track.type === "aircraft" ?
      ` (${(track.alt_m / 0.3048).toFixed(0)} ft)` : ""}`;
  const speed = track.speed_mps == null ? "—" : `${track.speed_mps.toFixed(1)} m/s`;
  const heading = track.heading_deg == null ? "—" : `${track.heading_deg.toFixed(1)}°`;
  return `<b>${track.id}</b><br>Type: ${track.type}` +
    (track.callsign ? `<br>Callsign: ${track.callsign}` : "") +
    `<br>Altitude: ${altitude}<br>Speed: ${speed}<br>Heading: ${heading}` +
    `<br>Source: ${track.source}`;
}
function updateState(message) {
  const current = new Set();
  for (const track of message.tracks) {
    current.add(track.id);
    const color = colors[track.type] || "#666";
    if (!markers.has(track.id)) {
      markers.set(track.id, L.circleMarker([track.lat, track.lon], {
        radius: 8, color, fillColor: color, fillOpacity: 0.85, weight: 2
      }).addTo(map));
    }
    markers.get(track.id).setLatLng([track.lat, track.lon]).bindPopup(popup(track));
  }
  for (const [id, marker] of markers) {
    if (!current.has(id)) { map.removeLayer(marker); markers.delete(id); }
  }
  status.textContent = `Connected · ${message.tracks.length} track(s)`;
  status.className = "panel connected";
}
function connect() {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${scheme}://${location.host}/ws`);
  socket.onopen = () => { reconnectDelay = 1000; };
  socket.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.type === "state") updateState(message);
  };
  socket.onerror = () => socket.close();
  socket.onclose = () => {
    status.textContent = "Reconnecting…";
    status.className = "panel reconnecting";
    setTimeout(connect, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 15000);
  };
}
connect();
