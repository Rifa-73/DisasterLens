import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import Navbar from "../components/Navbar";
import ResponderChatbot from "../components/ResponderChatbot";

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
  CheckCircle,
} from "lucide-react";

function Dashboard() {
  const navigate = useNavigate();

  const [reports, setReports] = useState([]);
  const [filter, setFilter] = useState("all");
  const [notificationOpen, setNotificationOpen] = useState(false);

  const [lastSeenId, setLastSeenId] = useState(
    Number(localStorage.getItem("lastSeenIncidentId") || 0)
  );

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const res = await fetch("http://localhost:8000/incidents/");

        if (!res.ok) {
          throw new Error("Failed to fetch incidents");
        }

        const data = await res.json();

        const formatted = data
          .map((item) => ({
            id: item.id,
            latitude: Number(item.latitude),
            longitude: Number(item.longitude),
            location: `${item.latitude}, ${item.longitude}`,
            description: item.description,
            created_at: item.created_at,
            aiAssessment: item.ai_assessment,
            cvAssessment: item.severity,
            evidence: {
              image: null,
              video: item.video_url || null,
              audio: item.audio_url || null,
            },
          }))
          .sort((a, b) => Number(b.id) - Number(a.id));

        /*
         * The current user's latest report contains the uploaded
         * image in localStorage because GET /incidents/ does not
         * currently return image_url.
         */
        const saved = localStorage.getItem("rnrReport");

        if (saved && formatted.length) {
          const localReport = JSON.parse(saved);

          const index = formatted.findIndex(
            (item) => Number(item.id) === Number(localReport.id)
          );

          if (index !== -1) {
            formatted[index] = {
              ...formatted[index],
              evidence: {
                ...formatted[index].evidence,
                image: localReport.evidence?.image || null,
              },
            };
          }
        }

        setReports(formatted);
      } catch (error) {
        console.error("Failed to fetch incidents:", error);
      }
    };

    fetchIncidents();

    const interval = setInterval(fetchIncidents, 5000);

    return () => clearInterval(interval);
  }, []);

  const filteredReports =
    filter === "all"
      ? reports
      : reports.filter(
          (report) =>
            report.cvAssessment?.severity_level?.toLowerCase() ===
            filter
        );

  const latest = reports[0] || null;

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

  const priorityCounts = {
    high: reports.filter((r) => getPriority(r) === "high").length,
    medium: reports.filter((r) => getPriority(r) === "medium").length,
    low: reports.filter((r) => getPriority(r) === "low").length,
  };

  const openIncident = (report) => {
    localStorage.setItem(
      "rnrReport",
      JSON.stringify(report)
    );

    navigate("/incident");
  };

  const latestLocation =
    latest &&
    Number.isFinite(latest.latitude) &&
    Number.isFinite(latest.longitude)
      ? [latest.latitude, latest.longitude]
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
              Monitor and prioritize incoming disaster incidents.
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
        <div className="flex items-center gap-2 mt-8 flex-wrap">
          <span className="text-sm font-medium mr-2">
            Severity:
          </span>

          {["all", "low", "moderate", "severe"].map((item) => (
            <button
              key={item}
              onClick={() => setFilter(item)}
              className={`px-4 py-2 rounded-lg text-xs font-medium border ${
                filter === item
                  ? "bg-[#2F7D4A] text-white border-[#2F7D4A]"
                  : "bg-white border-[#DDE5DE] text-[#68736B]"
              }`}
            >
              {item === "all"
                ? "All"
                : item.charAt(0).toUpperCase() + item.slice(1)}
            </button>
          ))}
        </div>

        {/* STATS */}
        <div className="grid md:grid-cols-4 gap-4 mt-6">
          {[
            [
              "High Priority",
              priorityCounts.high,
              "Immediate attention",
            ],
            [
              "Medium Priority",
              priorityCounts.medium,
              "Requires monitoring",
            ],
            [
              "Low Priority",
              priorityCounts.low,
              "Low urgency",
            ],
            [
              "Total Incidents",
              reports.length,
              "Saved incidents",
            ],
          ].map(([title, count, text]) => (
            <div
              key={title}
              className="p-5 rounded-2xl border border-[#DDE5DE] bg-white shadow-sm"
            >
              <p className="text-sm text-[#68736B]">
                {title}
              </p>

              <p className="text-3xl font-bold mt-2">
                {count}
              </p>

              <p className="text-xs text-[#68736B] mt-2">
                {text}
              </p>
            </div>
          ))}
        </div>

        {/* LATEST INCIDENT + MAP */}
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

                <div className="relative">
                  <button
                    onClick={() => {
                      setNotificationOpen(!notificationOpen);

                      localStorage.setItem(
                        "lastSeenIncidentId",
                        latest.id
                      );

                      setLastSeenId(latest.id);
                    }}
                  >
                    <Bell className="w-5 h-5 text-gray-500" />

                    {latest.id > lastSeenId && (
                      <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full bg-red-500 border-2 border-white" />
                    )}
                  </button>

                  {notificationOpen && (
                    <div className="absolute right-0 top-12 z-50 w-72 p-4 bg-white border border-[#DDE5DE] rounded-2xl shadow-xl">
                      <div className="flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-red-500" />

                        <div>
                          <p className="font-semibold text-sm">
                            Latest Incident
                          </p>

                          <p className="text-xs text-[#68736B] mt-1">
                            Incident #{latest.id} has been submitted.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <IncidentCard
                report={latest}
                getPriority={getPriority}
                onView={openIncident}
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
                    Locations of all saved incidents
                  </p>
                </div>

                <MapPin className="w-5 h-5 text-gray-500" />
              </div>

              <div className="h-[520px] rounded-2xl overflow-hidden border border-[#DDE5DE] shadow-sm">
                <MapContainer
                  center={latestLocation}
                  zoom={11}
                  scrollWheelZoom
                  className="h-full w-full"
                >
                  <TileLayer
                    attribution="&copy; OpenStreetMap contributors"
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />

                  {reports.map((report) => {
                    if (
                      !Number.isFinite(report.latitude) ||
                      !Number.isFinite(report.longitude)
                    ) {
                      return null;
                    }

                    const position = [
                      report.latitude,
                      report.longitude,
                    ];

                    const coverage =
                      Number(
                        report.cvAssessment?.flood_coverage_pct
                      ) || 0;

                    const radius = Math.max(
                      300,
                      Math.min(3000, coverage * 30)
                    );

                    return (
                      <div key={report.id}>
                        <Marker position={position}>
                          <Popup>
                            <b>
                              Incident #{report.id}
                            </b>

                            <br />

                            Severity:{" "}
                            {report.cvAssessment?.severity_level ||
                              "N/A"}

                            <br />

                            Priority:{" "}
                            {getPriority(report).toUpperCase()}

                            <br />

                            Flood Coverage: {coverage}%

                            <br />

                            Location: {report.location}
                          </Popup>
                        </Marker>

                        {report.cvAssessment && (
                          <Circle
                            center={position}
                            radius={radius}
                            pathOptions={{
                              fillOpacity: 0.15,
                              weight: 1,
                            }}
                          />
                        )}
                      </div>
                    );
                  })}
                </MapContainer>
              </div>

              <div className="mt-3 text-xs text-gray-600">
                <b>{reports.length}</b> incident locations shown
              </div>
            </div>
          </div>
        )}

        {/* ALL INCIDENTS */}
        <section className="mt-10">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-xl font-semibold">
                All Incidents
              </h2>

              <p className="text-xs text-[#68736B] mt-1">
                Every submitted disaster report remains saved.
              </p>
            </div>

            <span className="text-xs text-[#68736B]">
              Showing {filteredReports.length} of {reports.length}
            </span>
          </div>

          {filteredReports.length === 0 ? (
            <div className="p-8 text-center bg-white border border-[#DDE5DE] rounded-2xl">
              <p className="text-sm text-[#68736B]">
                No incidents found for this severity.
              </p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">
              {filteredReports.map((report) => (
                <IncidentCard
                  key={report.id}
                  report={report}
                  getPriority={getPriority}
                  onView={openIncident}
                  compact
                />
              ))}
            </div>
          )}
        </section>

        {/* LAST UPDATED */}
        <div className="flex justify-end items-center gap-2 text-xs text-gray-700 mt-6">
          <Clock className="w-3.5 h-3.5" />
          Dashboard updates automatically
        </div>
      </main>

      {latest && <ResponderChatbot report={latest} />}
    </div>
  );
}

function IncidentCard({
  report,
  getPriority,
  onView,
  compact = false,
}) {
  const ai = report.aiAssessment;
  const cv = report.cvAssessment;

  const priority = getPriority(report);

  const priorityStyle =
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

      <div className="flex justify-between items-start gap-3">
        <span
          className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-white text-[10px] font-bold ${priorityStyle}`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-white" />
          {priority.toUpperCase()} PRIORITY
        </span>

        <span className="text-xs text-[#68736B]">
          #{report.id}
        </span>
      </div>

      <h3 className="text-lg font-semibold mt-4">
        {ai?.disaster_type || "Possible Incident"}
      </h3>

      <div className="flex items-center gap-2 text-xs text-[#68736B] mt-3">
        <MapPin className="w-3.5 h-3.5" />
        {report.location}
      </div>

      <div className="flex items-center gap-2 text-xs text-[#68736B] mt-2">
        <Clock className="w-3.5 h-3.5" />
        {reportTime}
      </div>

      {!compact && report.description && (
        <p className="text-sm text-[#68736B] mt-3">
          {report.description}
        </p>
      )}

      {/* AI */}
      {ai && (
        <div className="mt-4 p-3 rounded-xl bg-[#F3F7F3] border border-[#DDE5DE]">
          <p className="text-[10px] font-semibold text-[#2F7D4A]">
            GEMINI AI
          </p>

          <p className="text-xs text-[#68736B] mt-1">
            Likelihood:{" "}
            <b>{ai.likelihood || "N/A"}</b>
          </p>

          {ai.needs_human_verification && (
            <p className="text-[10px] text-amber-600 font-semibold mt-2">
              Human verification required
            </p>
          )}
        </div>
      )}

      {/* CVDL */}
      {cv && (
        <div className="mt-3 p-3 rounded-xl bg-[#F3F7F3] border border-[#DDE5DE]">
          <p className="text-[10px] font-semibold text-[#2F7D4A]">
            CVDL FLOOD ANALYSIS
          </p>

          <p className="text-xs text-[#68736B] mt-1">
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
        {report.evidence?.image && (
          <span className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#F3F7F3] text-[10px] text-[#2F7D4A]">
            <Image className="w-3 h-3" />
            Image
          </span>
        )}

        {report.evidence?.video && (
          <span className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#F3F7F3] text-[10px] text-[#2F7D4A]">
            <Video className="w-3 h-3" />
            Video
          </span>
        )}

        {report.evidence?.audio && (
          <span className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#F3F7F3] text-[10px] text-[#2F7D4A]">
            <Mic className="w-3 h-3" />
            Audio
          </span>
        )}
      </div>

      <button
        onClick={() => onView(report)}
        className="w-full flex justify-between mt-5 px-4 py-3 rounded-xl bg-[#2F7D4A] text-white text-sm font-semibold"
      >
        View Incident
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}

export default Dashboard;