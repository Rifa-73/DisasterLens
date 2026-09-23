import {
  MapContainer,
  TileLayer,
  Marker,
  Circle,
  Popup,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function AffectedAreaMap({
  latitude,
  longitude,
  coverage = 0,
  severity = "N/A",
}) {
  const lat = Number(latitude);
  const lng = Number(longitude);
  const floodCoverage = Number(coverage) || 0;

  if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
    return null;
  }

  const radius = Math.max(
    300,
    Math.min(3000, floodCoverage * 30)
  );

  return (
    <div className="mt-8 p-6 rounded-2xl border border-[#DDE5DE] bg-white shadow-sm">
      <h2 className="text-lg font-semibold">Affected Area</h2>

      <p className="text-xs text-gray-600 mt-1">
        Estimated impact zone based on CVDL flood coverage
      </p>

      <div className="h-[400px] rounded-xl overflow-hidden mt-4">
        <MapContainer
          center={[lat, lng]}
          zoom={13}
          scrollWheelZoom
          className="h-full w-full"
        >
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <Marker position={[lat, lng]}>
            <Popup>
              <b>Incident Location</b>
              <br />
              Severity: {severity}
              <br />
              Flood Coverage: {floodCoverage}%
            </Popup>
          </Marker>

          <Circle
            center={[lat, lng]}
            radius={radius}
            pathOptions={{ fillOpacity: 0.2, weight: 2 }}
          />
        </MapContainer>
      </div>

      <div className="mt-3 text-sm text-gray-700">
        <b>Flood Coverage:</b> {floodCoverage}% &nbsp;•&nbsp;
        <b>Severity:</b> {severity}
      </div>
    </div>
  );
}