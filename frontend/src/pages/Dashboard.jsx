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

import {
  Bell,
  MapPin,
  AlertTriangle,
  Clock,
  Image,
  Video,
  Mic,
  ArrowRight,
} from "lucide-react";

import Navbar from "../components/Navbar";
import ResponderChatbot from "../components/ResponderChatbot";

const API = "http://localhost:8000";

function Dashboard() {
  const navigate = useNavigate();

  const [reports, setReports] = useState([]);
  const [filter, setFilter] = useState("all");
  const [notificationOpen, setNotificationOpen] = useState(false);

  // Fetch only incidents submitted through the current UI
  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const response = await fetch(`${API}/incidents/`);

        if (!response.ok) {
          throw new Error("Failed to fetch incidents");
        }

        const data = await response.json();

        const visibleIds = JSON.parse(
          localStorage.getItem("visibleIncidentIds") || "[]"
        ).map(Number);

        const newReports = data
          .filter((item) => visibleIds.includes(Number(item.id)))
          .sort((a, b) => Number(b.id) - Number(a.id))
          .map((item) => ({
            id: item.id,
            latitude: Number(item.latitude),
            longitude: Number(item.longitude),

            location: `${item.latitude}, ${item.longitude}`,

            description: item.description,
            created_at: item.created_at,

            aiAssessment: item.ai_assessment || null,
            cvAssessment: item.severity || null,

            evidence: {
              image: item.image_url || null,
              video: item.video_url || null,
              audio: item.audio_url || null,
            },
          }));

        // Restore locally saved image for latest report
        const saved = localStorage.getItem("rnrReport");

        if (saved) {
          try {
            const localReport = JSON.parse(saved);

            setReports(
              newReports.map((item) =>
                Number(item.id) === Number(localReport.id)
                  ? {
                      ...item,
                      evidence: {
                        ...item.evidence,
                        image:
                          localReport.evidence?.image ||
                          item.evidence.image,
                      },
                    }
                  : item
              )
            );

            return;
          } catch {
            // Ignore invalid localStorage data
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
    const aiPriority =
      report?.aiAssessment?.priority?.toLowerCase();

    if (["high", "medium", "low"].includes(aiPriority)) {
      return aiPriority;
    }

    const severity =
      report?.cvAssessment?.severity_level?.toLowerCase();

    if (severity === "severe") return "high";
    if (severity === "moderate") return "medium";
    if (severity === "low") return "low";

    return "unknown";
  };

  const filteredReports = useMemo(() => {
    if (filter === "all") return reports;

    return reports.filter((report) => {
      const severity =
        report.cvAssessment?.severity_level?.toLowerCase();

      return severity === filter;
    });
  }, [reports, filter]);

  const latest = filteredReports[0] || null;

  const counts = {
    high: reports.filter((r) => getPriority(r) === "high").length,
    medium: reports.filter((r) => getPriority(r) === "medium").length,
    low: reports.filter((r) => getPriority(r) === "low").length,
  };

  const openIncident = (incident) => {
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

        evidence: {
          image: incident.evidence?.image || null,
          video: incident.evidence?.video || null,
          audio: incident.evidence?.audio || null,
        },

        status: "ASSESSED",

        aiAssessment: incident.aiAssessment || null,
        cvAssessment: incident.cvAssessment || null,
      })
    );

    navigate("/incident");
  };

  const getMapLocation = (report) => {
    if (
      Number.isFinite(report?.latitude) &&
      Number.isFinite(report?.longitude)
    ) {
      return [report.latitude, report.longitude];
    }

    return [28.6139, 77.209];
  };

  const mapCenter = latest
    ? getMapLocation(latest)
    : [28.6139, 77.209];

  return (
    <div className="min-h-screen bg-[#F7F8F5] text-[#17201A]">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-10">

        {/* HEADER */}
        <div className="flex justify-between items-end gap-4">
          <div>
            <p className="text-xs tracking-[0.25em] text-[#2F7D4A] font-semibold">
              RESPONSE CENTER
            </p>

            <h1 className="text-4xl md:text-5xl font-bold mt-3">
              Incident Dashboard
            </h1>

            <p className="text-[#68736B] mt-3">
              Monitor newly submitted disaster incidents.
            </p>
          </div>

          <div className="flex items-center gap-2 px-4 py-2 rounded-full border border-[#BFDAC5] bg-[#EAF4EC]">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />

            <span className="text-xs text-[#2F7D4A] font-medium">
              SYSTEM LIVE
            </span>
          </div>
        </div>

        {/* FILTER */}
        <div className="flex items-center gap-2 mt-8">
          <span className="text-xs font-medium">
            Severity:
          </span>

          {["all", "low", "moderate", "severe"].map((item) => (
            <button
              key={item}
              onClick={() => setFilter(item)}
              className={`px-3 py-1.5 rounded-lg text-xs capitalize border ${
                filter === item
                  ? "bg-[#2F7D4A] text-white border-[#2F7D4A]"
                  : "bg-white border-[#DDE5DE] text-[#68736B]"
              }`}
            >
              {item}
            </button>
          ))}
        </div>

        {/* STATS */}
        <div className="grid md:grid-cols-4 gap-4 mt-6">
          <Stat
            title="High Priority"
            value={counts.high}
            text="Immediate attention"
          />

          <Stat
            title="Medium Priority"
            value={counts.medium}
            text="Requires monitoring"
          />

          <Stat
            title="Low Priority"
            value={counts.low}
            text="Low urgency"
          />

          <Stat
            title="Total Incidents"
            value={reports.length}
            text="New incidents"
          />
        </div>

        {/* LATEST + MAP */}
        {latest && (
          <div className="grid lg:grid-cols-5 gap-6 mt-8">

            {/* LATEST INCIDENT */}
            <div className="lg:col-span-2">
              <div className="flex justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold">
                    Latest Incident
                  </h2>

                  <p className="text-xs text-gray-600 mt-1">
                    Most recently submitted report
                  </p>
                </div>

                <button
                  onClick={() =>
                    setNotificationOpen(!notificationOpen)
                  }
                  className="relative"
                >
                  <Bell className="w-5 h-5 text-gray-500" />

                  <span className="absolute top-0 right-0 w-2.5 h-2.5 rounded-full bg-red-500" />
                </button>

                {notificationOpen && (
                  <div className="absolute mt-8 z-50 p-4 bg-white border rounded-xl shadow-lg">
                    <p className="text-sm font-semibold">
                      New Incident
                    </p>

                    <p className="text-xs text-gray-500 mt-1">
                      A new disaster report has been submitted.
                    </p>
                  </div>
                )}
              </div>

              <IncidentCard
                report={latest}
                priority={getPriority(latest)}
                onView={() => openIncident(latest)}
              />
            </div>

            {/* MAP */}
            <div className="lg:col-span-3">
              <div className="flex justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold">
                    Live Incident Map
                  </h2>

                  <p className="text-xs text-gray-600 mt-1">
                    Locations of all new incidents
                  </p>
                </div>

                <MapPin className="w-5 h-5 text-gray-500" />
              </div>

              <div className="h-[520px] rounded-2xl overflow-hidden border border-[#DDE5DE] shadow-sm">
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
                    const position = getMapLocation(report);
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
                            <b>
                              {report.aiAssessment?.disaster_type ||
                                "Possible Incident"}
                            </b>

                            <br />

                            Incident #{report.id}

                            <br />

                            Priority:{" "}
                            {getPriority(report).toUpperCase()}

                            <br />

                            Severity:{" "}
                            {cv?.severity_level || "N/A"}

                            <br />

                            <button
                              onClick={() => openIncident(report)}
                              className="mt-2 text-[#2F7D4A] font-semibold"
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

              <p className="text-xs text-gray-600 mt-2">
                {filteredReports.length} incident location
                {filteredReports.length !== 1 ? "s" : ""} shown
              </p>
            </div>
          </div>
        )}

        {/* EMPTY STATE */}
        {!latest && (
          <div className="mt-8 p-10 text-center bg-white border border-[#DDE5DE] rounded-2xl">
            <AlertTriangle className="w-8 h-8 mx-auto text-gray-400" />

            <h2 className="font-semibold mt-3">
              No new incidents
            </h2>

            <p className="text-sm text-gray-500 mt-1">
              New submitted reports will appear here automatically.
            </p>
          </div>
        )}

        {/* ALL NEW INCIDENTS */}
        {filteredReports.length > 0 && (
          <section className="mt-10">
            <div className="flex justify-between items-end mb-5">
              <div>
                <h2 className="text-lg font-semibold">
                  All New Incidents
                </h2>

                <p className="text-xs text-[#68736B] mt-1">
                  Newly submitted disaster reports remain saved.
                </p>
              </div>

              <span className="text-xs text-[#68736B]">
                Showing {filteredReports.length}
              </span>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredReports.map((incident) => (
                <IncidentCard
                  key={incident.id}
                  report={incident}
                  priority={getPriority(incident)}
                  onView={() => openIncident(incident)}
                />
              ))}
            </div>
          </section>
        )}

        <div className="flex justify-end items-center gap-2 text-xs text-gray-700 mt-6">
          <Clock className="w-3.5 h-3.5" />
          Dashboard updates automatically
        </div>
      </main>

      <ResponderChatbot report={latest} />
    </div>
  );
}

/* ---------------- COMPONENTS ---------------- */

function Stat({ title, value, text }) {
  return (
    <div className="p-5 rounded-2xl border border-[#DDE5DE] bg-white shadow-sm">
      <p className="text-sm text-[#68736B]">
        {title}
      </p>

      <p className="text-3xl font-bold mt-2">
        {value}
      </p>

      <p className="text-xs text-[#68736B] mt-2">
        {text}
      </p>
    </div>
  );
}

function IncidentCard({ report, priority, onView }) {
  const ai = report?.aiAssessment;
  const cv = report?.cvAssessment;
  const evidence = report?.evidence;

  const priorityClass =
    priority === "high"
      ? "bg-[#DC2626]"
      : priority === "medium"
      ? "bg-[#F59E0B]"
      : "bg-[#2F7D4A]";

  const reportTime = report.created_at
    ? new Date(report.created_at).toLocaleString("en-IN")
    : "Time unavailable";

  return (
    <div className="p-5 rounded-2xl border border-[#DDE5DE] bg-white shadow-sm">

      {/* PRIORITY */}
      <div className="flex justify-between items-center">
        <span
          className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-white text-[10px] font-bold ${priorityClass}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-white" />

          {priority.toUpperCase()} PRIORITY
        </span>

        <span className="text-xs text-gray-400">
          #{report.id}
        </span>
      </div>

      {/* TITLE */}
      <h3 className="text-lg font-semibold mt-4">
        {ai?.disaster_type || "Possible Incident"}
      </h3>

      {/* LOCATION */}
      <div className="flex items-center gap-2 text-xs text-[#68736B] mt-2">
        <MapPin className="w-3.5 h-3.5" />

        {report.location || "Location unavailable"}
      </div>

      {/* TIME */}
      <div className="flex items-center gap-2 text-xs text-[#68736B] mt-2">
        <Clock className="w-3.5 h-3.5" />

        {reportTime}
      </div>

      {/* GEMINI */}
      <div className="mt-4 p-3 rounded-xl bg-[#F3F7F3] border border-[#DDE5DE]">
        <p className="text-[10px] font-semibold text-[#2F7D4A]">
          GEMINI AI
        </p>

        <p className="text-xs text-[#68736B] mt-2">
          Likelihood:{" "}
          <b>{ai?.likelihood || "Unavailable"}</b>
        </p>

        {ai?.needs_human_verification && (
          <p className="text-[10px] text-orange-500 font-semibold mt-2">
            Human verification required
          </p>
        )}
      </div>

      {/* CVDL */}
      {cv && (
        <div className="mt-3 p-3 rounded-xl bg-[#F3F7F3] border border-[#DDE5DE]">
          <p className="text-[10px] font-semibold text-[#2F7D4A]">
            CVDL FLOOD ANALYSIS
          </p>

          <p className="text-xs text-[#68736B] mt-2">
            Severity: <b>{cv.severity_level}</b>
          </p>

          <p className="text-xs text-[#68736B] mt-1">
            Flood Coverage:{" "}
            <b>{cv.flood_coverage_pct}%</b>
          </p>
        </div>
      )}

      {/* EVIDENCE */}
      <div className="flex gap-2 mt-4 flex-wrap">
        {evidence?.image && (
          <span className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#F3F7F3] text-[10px] text-[#2F7D4A]">
            <Image className="w-3 h-3" />
            Image
          </span>
        )}

        {evidence?.video && (
          <span className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#F3F7F3] text-[10px] text-[#2F7D4A]">
            <Video className="w-3 h-3" />
            Video
          </span>
        )}

        {evidence?.audio && (
          <span className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#F3F7F3] text-[10px] text-[#2F7D4A]">
            <Mic className="w-3 h-3" />
            Audio
          </span>
        )}
      </div>

      {/* VIEW */}
      <button
        onClick={onView}
        className="w-full flex justify-between items-center mt-5 px-4 py-3 rounded-xl bg-[#2F7D4A] text-white text-xs font-semibold hover:bg-[#25663C]"
      >
        View Incident

        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}

export default Dashboard;