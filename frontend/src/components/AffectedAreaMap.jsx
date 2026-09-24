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

  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;

  const radius = Math.max(300, Math.min(3000, floodCoverage * 30));

  return (
    <div className="mt-6 bg-white border border-[#E1E6DF] rounded-xl p-5">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-[9px] tracking-[0.18em] font-bold text-[#718075]">
            AFFECTED AREA
          </p>

          <p className="text-xs text-[#7A847D] mt-1">
            Estimated impact zone from CVDL flood coverage
          </p>
        </div>

        <span className="px-2 py-1 rounded-md bg-[#EEF4EC] text-[9px] text-[#426A4A] font-semibold">
          {floodCoverage}%
        </span>
      </div>

      <div className="h-[380px] rounded-lg overflow-hidden mt-4">
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
            pathOptions={{ fillOpacity: 0.16, weight: 2 }}
          />
        </MapContainer>
      </div>
    </div>
  );
}