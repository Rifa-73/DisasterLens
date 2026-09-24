import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  MapContainer,
  TileLayer,
  Marker,
  Circle,
  Popup,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

import { AlertTriangle, Clock, ArrowRight } from "lucide-react";

import Navbar from "../components/Navbar";
import ResponderChatbot from "../components/ResponderChatbot";

const API = "http://localhost:8000";

function Dashboard() {
  const navigate = useNavigate();

  const [reports, setReports] = useState([]);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const response = await fetch(`${API}/incidents/`);
        if (!response.ok) throw new Error("Failed to fetch incidents");

        const data = await response.json();

        const visibleIds = JSON.parse(
          localStorage.getItem("visibleIncidentIds") || "[]"
        ).map(Number);

        const newReports = data
          .filter((item) => visibleIds.includes(Number(item.id)))
          .sort((a, b) => Number(b.id) - Number(a.id))
          .map((item) => {
            const imageUrls =
              Array.isArray(item.image_urls)
                ? item.image_urls
                : Array.isArray(item.imageUrls)
                ? item.imageUrls
                : item.image_url
                ? [item.image_url]
                : [];

            return {
              id: item.id,
              latitude: Number(item.latitude),
              longitude: Number(item.longitude),
              location: `${item.latitude}, ${item.longitude}`,
              description: item.description,
              created_at: item.created_at,

              aiAssessment: item.ai_assessment || null,
              cvAssessment: item.severity || null,

              imageUrls,

              evidence: {
                images: imageUrls.map((url, i) => ({
                  data: url,
                  name: `Evidence image ${i + 1}`,
                })),
                image: imageUrls[0] || null,
                video: item.video_url || null,
                audio: item.audio_url || null,
              },
            };
          });

        const saved = localStorage.getItem("rnrReport");

        if (saved) {
          try {
            const localReport = JSON.parse(saved);

            setReports(
              newReports.map((item) =>
                Number(item.id) === Number(localReport.id)
                  ? {
                      ...item,

                      imageUrls:
                        localReport.imageUrls?.length
                          ? localReport.imageUrls
                          : item.imageUrls,

                      evidence: {
                        ...item.evidence,

                        images:
                          localReport.evidence?.images?.length
                            ? localReport.evidence.images
                            : item.evidence.images,

                        image:
                          localReport.evidence?.image ||
                          item.evidence.image,

                        video:
                          localReport.evidence?.video ||
                          item.evidence.video,

                        audio:
                          localReport.evidence?.audio ||
                          item.evidence.audio,
                      },

                      batchAnalysis:
                        localReport.batchAnalysis || null,

                      videoAnalysis:
                        localReport.videoAnalysis || null,
                    }
                  : item
              )
            );

            return;
          } catch {
            // Ignore invalid localStorage
          }
        }

        setReports(newReports);
      } catch (error) {
        console.error("Dashboard error:", error);
      }
    };

    fetchIncidents();
    const interval = setInterval(fetchIncidents, 5000);

    return () => clearInterval(interval);
  }, []);

  const getPriority = (report) => {
    const priority = report?.aiAssessment?.priority?.toLowerCase();

    if (["high", "medium", "low"].includes(priority)) return priority;

    const severity =
      report?.cvAssessment?.severity_level?.toLowerCase();

    if (severity === "severe") return "high";
    if (severity === "moderate") return "medium";
    if (severity === "low") return "low";

    return "unknown";
  };

  const filteredReports = useMemo(() => {
    if (filter === "all") return reports;

    return reports.filter(
      (report) =>
        report.cvAssessment?.severity_level?.toLowerCase() === filter
    );
  }, [reports, filter]);

  const counts = {
    high: reports.filter((r) => getPriority(r) === "high").length,
    medium: reports.filter((r) => getPriority(r) === "medium").length,
    low: reports.filter((r) => getPriority(r) === "low").length,
  };

  const openIncident = (incident) => {
    const images =
      incident.evidence?.images?.length
        ? incident.evidence.images
        : (incident.imageUrls || []).map((url, i) => ({
            data: url,
            name: `Evidence image ${i + 1}`,
          }));

    localStorage.setItem(
      "rnrReport",
      JSON.stringify({
        id: incident.id,
        incidentId: incident.id,
        latitude: incident.latitude,
        longitude: incident.longitude,
        location: incident.location,
        description: incident.description,
        created_at: incident.created_at,

        imageUrls: incident.imageUrls || [],

        evidence: {
          images,
          image:
            images[0]?.data ||
            incident.evidence?.image ||
            null,
          video: incident.evidence?.video || null,
          audio: incident.evidence?.audio || null,
        },

        batchAnalysis: incident.batchAnalysis || null,
        videoAnalysis: incident.videoAnalysis || null,

        status: "ASSESSED",
        aiAssessment: incident.aiAssessment || null,
        cvAssessment: incident.cvAssessment || null,
      })
    );

    navigate("/incident");
  };

  const mapLocation = (report) =>
    Number.isFinite(report?.latitude) &&
    Number.isFinite(report?.longitude)
      ? [report.latitude, report.longitude]
      : [28.6139, 77.209];

  const mapCenter = filteredReports.length
    ? mapLocation(filteredReports[0])
    : [28.6139, 77.209];

  return (
    <div className="min-h-screen bg-[#F8F9F6] text-[#263229]">
      <Navbar />

      <main className="max-w-7xl mx-auto px-5 md:px-8 py-8">

        {/* HEADER */}
        <div className="flex justify-between items-end gap-4">
          <div>
            <p className="text-[9px] tracking-[0.25em] font-bold text-[#527057]">
              RESPONSE CENTER
            </p>

            <h1 className="text-3xl md:text-4xl font-bold mt-2">
              Live Dashboard
            </h1>

            <p className="text-xs text-[#78827A] mt-2">
              Every incident reported, verified and mapped in real time.
            </p>
          </div>

          <div className="px-3 py-2 rounded-full bg-[#EEF4EC] text-[9px] text-[#4D7054] font-semibold">
            ● SYSTEM LIVE
          </div>
        </div>

        {/* FILTER */}
        <div className="flex flex-wrap gap-2 mt-6">
          {["all", "low", "moderate", "severe"].map((item) => (
            <button
              key={item}
              onClick={() => setFilter(item)}
              className={`px-3 py-1.5 rounded-md text-[10px] capitalize border ${
                filter === item
                  ? "bg-[#3F6546] text-white border-[#3F6546]"
                  : "bg-white text-[#69756D] border-[#E0E5DE]"
              }`}
            >
              {item}
            </button>
          ))}
        </div>

        {/* INCIDENT TABLE */}
        <section className="mt-6 bg-white border border-[#E1E6DF] rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-[#E8ECE6]">
            <h2 className="text-sm font-semibold">Incidents</h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-[#E8ECE6] text-[9px] uppercase tracking-wider text-[#849087]">
                  <th className="px-5 py-3 font-semibold">Report</th>
                  <th className="px-5 py-3 font-semibold">Location</th>
                  <th className="px-5 py-3 font-semibold">Time</th>
                  <th className="px-5 py-3 font-semibold">Severity</th>
                  <th className="px-5 py-3 text-right"></th>
                </tr>
              </thead>

              <tbody>
                {filteredReports.map((report) => {
                  const priority = getPriority(report);

                  return (
                    <tr
                      key={report.id}
                      className="border-b last:border-b-0 border-[#EDF0EB] hover:bg-[#FAFBF9]"
                    >
                      <td className="px-5 py-3 text-xs font-semibold">
                        Report #{report.id}
                      </td>

                      <td className="px-5 py-3 text-xs text-[#68736B]">
                        {report.location}
                      </td>

                      <td className="px-5 py-3 text-xs text-[#68736B]">
                        {report.created_at
                          ? new Date(report.created_at).toLocaleTimeString(
                              "en-IN",
                              {
                                hour: "2-digit",
                                minute: "2-digit",
                              }
                            )
                          : "N/A"}
                      </td>

                      <td className="px-5 py-3">
                        <SeverityBadge priority={priority} />
                      </td>

                      <td className="px-5 py-3 text-right">
                        <button
                          onClick={() => openIncident(report)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-[#DCE3DA] text-[10px] text-[#4A5F4E] hover:bg-[#EEF4EC]"
                        >
                          View
                          <ArrowRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {!filteredReports.length && (
            <div className="p-10 text-center">
              <AlertTriangle className="w-7 h-7 mx-auto text-gray-400" />
              <p className="text-sm font-semibold mt-3">
                No incidents
              </p>
              <p className="text-xs text-gray-500 mt-1">
                New submitted reports will appear automatically.
              </p>
            </div>
          )}
        </section>

        {/* SUMMARY */}
        <div className="grid md:grid-cols-4 gap-3 mt-4">
          <Summary title="HIGH" value={counts.high} type="high" />
          <Summary title="MODERATE" value={counts.medium} type="medium" />
          <Summary title="LOW" value={counts.low} type="low" />
          <Summary
            title="ACTIVE INCIDENTS"
            value={reports.length}
            type="active"
          />
        </div>

        {/* MAP */}
        <section className="mt-6 bg-white border border-[#E1E6DF] rounded-xl overflow-hidden">
          <div className="px-5 py-4">
            <h2 className="text-sm font-semibold">Incident Map</h2>
            <p className="text-[10px] text-[#7B867E] mt-1">
              Click markers to see severity, location and source.
            </p>
          </div>

          <div className="h-[430px]">
            <MapContainer
              center={mapCenter}
              zoom={11}
              scrollWheelZoom
              className="h-full w-full"
            >
              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {filteredReports.map((report) => {
                const position = mapLocation(report);
                const cv = report.cvAssessment;
                const coverage =
                  Number(cv?.flood_coverage_pct) || 0;

                const radius = Math.max(
                  300,
                  Math.min(3000, coverage * 30)
                );

                return (
                  <div key={report.id}>
                    <Marker position={position}>
                      <Popup>
                        <b>Report #{report.id}</b>
                        <br />
                        Priority: {getPriority(report).toUpperCase()}
                        <br />
                        Severity: {cv?.severity_level || "N/A"}
                        <br />

                        <button
                          onClick={() => openIncident(report)}
                          className="mt-2 text-[#3F6546] font-semibold"
                        >
                          View Incident →
                        </button>
                      </Popup>
                    </Marker>

                    {cv && (
                      <Circle
                        center={position}
                        radius={radius}
                        pathOptions={{
                          fillOpacity: 0.15,
                          weight: 2,
                        }}
                      />
                    )}
                  </div>
                );
              })}
            </MapContainer>
          </div>
        </section>

        <div className="flex justify-end gap-2 items-center mt-4 text-[10px] text-[#78827A]">
          <Clock className="w-3 h-3" />
          Dashboard updates automatically
        </div>
      </main>

      <ResponderChatbot report={filteredReports[0] || null} />
    </div>
  );
}

function SeverityBadge({ priority }) {
  const styles = {
    high: "bg-[#FDE7E6] text-[#D44743]",
    medium: "bg-[#FFF0DC] text-[#B56A18]",
    low: "bg-[#FFF8D9] text-[#8C7618]",
    unknown: "bg-gray-100 text-gray-500",
  };

  return (
    <span
      className={`px-2 py-1 rounded-md text-[8px] font-bold ${
        styles[priority] || styles.unknown
      }`}
    >
      {priority.toUpperCase()}
    </span>
  );
}

function Summary({ title, value, type }) {
  const styles = {
    high: "bg-[#FDE7E6] text-[#D44743]",
    medium: "bg-[#FFF0DC] text-[#B56A18]",
    low: "bg-[#FFF8D9] text-[#8C7618]",
    active: "bg-[#EAF2E7] text-[#4B704F]",
  };

  return (
    <div className={`rounded-xl p-4 ${styles[type]}`}>
      <p className="text-[9px] font-bold">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

export default Dashboard;