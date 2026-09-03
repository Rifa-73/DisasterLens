import Navbar from "../components/Navbar";
import ResponderChatbot from "../components/ResponderChatbot";
import {
  MapContainer,
  TileLayer,
  Marker,
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

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();
  const [report, setReport] = useState(null);

  useEffect(() => {
    const saved = localStorage.getItem("rnrReport");
    if (saved) setReport(JSON.parse(saved));
  }, []);

  const location = report?.location
    ? report.location.split(",").map(Number)
    : [28.6139, 77.209];

  const ai = report?.aiAssessment;
  const cv = report?.cvAssessment;

  const aiPriority = ai?.priority?.toLowerCase();
  
  const priority =
    ["high", "medium", "low"].includes(aiPriority)
      ? aiPriority
      : cv?.severity_level === "severe"
      ? "high"
      : cv?.severity_level === "moderate"
      ? "medium"
      : cv?.severity_level === "low"
      ? "low"
      : "unknown";
  
  const priorityCount = {
    high: priority === "high" ? 1 : 0,
    medium: priority === "medium" ? 1 : 0,
    low: priority === "low" ? 1 : 0,
  };

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

        {/* STATS */}
        <div className="grid md:grid-cols-4 gap-4 mt-10">
          {[
            ["High Priority", priorityCount.high, "Immediate attention"],
            ["Medium Priority", priorityCount.medium, "Requires monitoring"],
            ["Low Priority", priorityCount.low, "Low urgency"],
            ["Active Incidents", report ? 1 : 0, "Across monitored areas"],
          ].map(([title, count, text]) => (
            <div
              key={title}
              className="p-5 rounded-2xl border border-[#DDE5DE] bg-white shadow-sm"
            >
              <p className="text-sm text-[#68736B]">{title}</p>
              <p className="text-3xl font-bold mt-2">{count}</p>
              <p className="text-xs text-[#68736B] mt-2">{text}</p>
            </div>
          ))}
        </div>

        {/* MAIN */}
        <div className="grid lg:grid-cols-5 gap-6 mt-8">

          {/* INCIDENT */}
          <div className="lg:col-span-2">
            <div className="flex justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold">
                  Incoming Incident
                </h2>
                <p className="text-xs text-gray-600 mt-1">
                  Latest report requiring attention
                </p>
              </div>
              <Bell className="w-5 h-5 text-gray-500" />
            </div>

            <div className="p-5 rounded-2xl border border-red-200 bg-white shadow-sm">

              {/* PRIORITY */}
              <span
                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-white text-[11px] font-bold ${
                  priority === "high"
                    ? "bg-[#DC2626]"
                    : priority === "medium"
                    ? "bg-[#F59E0B]"
                    : "bg-[#2F7D4A]"
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-white" />
                {priority ? priority.toUpperCase() : "UNKNOWN"} PRIORITY
              </span>

              {/* DETAILS */}
              <h3 className="text-xl font-semibold mt-4">
                {ai?.disaster_type || "Possible Incident"}
              </h3>

              <div className="flex items-center gap-2 text-sm text-[#68736B] mt-3">
                <MapPin className="w-4 h-4" />
                {report?.location || "Location unavailable"}
              </div>

              <div className="flex items-start gap-2 text-sm text-[#68736B] mt-2">
                <AlertTriangle className="w-4 h-4 mt-0.5" />
                {report?.description || "No description provided."}
              </div>

              {/* GEMINI */}
              <div className="mt-4 p-4 rounded-xl bg-[#F3F7F3] border border-[#DDE5DE]">
                <p className="text-xs font-semibold text-[#2F7D4A]">
                  GEMINI AI ASSESSMENT
                </p>

                <p className="text-sm text-[#68736B] mt-2">
                  Likelihood:{" "}
                  <b>{ai?.likelihood || "N/A"}</b>
                </p>

                <p className="text-sm text-[#68736B] mt-2 leading-relaxed">
                  {ai?.reason || "No AI assessment available."}
                </p>

                {ai?.needs_human_verification && (
                  <p className="text-xs text-amber-600 font-semibold mt-3">
                    ⚠ Human verification required
                  </p>
                )}
              </div>

              {/* CVDL */}
              {cv && (
                <div className="mt-3 p-4 rounded-xl bg-[#F3F7F3] border border-[#DDE5DE]">
                  <p className="text-xs font-semibold text-[#2F7D4A]">
                    CVDL FLOOD ANALYSIS
                  </p>

                  <p className="text-sm text-[#68736B] mt-2">
                    Severity: <b>{cv.severity_level}</b>
                  </p>

                  <p className="text-sm text-[#68736B] mt-1">
                    Flood Coverage: <b>{cv.flood_coverage_pct}%</b>
                  </p>

                  <p className="text-sm text-[#68736B] mt-1">
                    Severity Score: <b>{cv.severity_score}/100</b>
                  </p>
                </div>
              )}

              {/* EVIDENCE */}
              <div className="flex gap-2 mt-5 flex-wrap">
                {report?.evidence?.image && (
                  <button
                    onClick={() => navigate("/incident")}
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#F3F7F3] text-xs text-[#2F7D4A]"
                  >
                    <Image className="w-3.5 h-3.5" />
                    View Image
                  </button>
                )}

                {report?.evidence?.video && (
                  <span className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#F3F7F3] text-xs text-[#2F7D4A]">
                    <Video className="w-3.5 h-3.5" />
                    Video
                  </span>
                )}

                {report?.evidence?.audio && (
                  <span className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#F3F7F3] text-xs text-[#2F7D4A]">
                    <Mic className="w-3.5 h-3.5" />
                    Audio
                  </span>
                )}
              </div>

              <button
                onClick={() => navigate("/incident")}
                className="w-full flex justify-between mt-6 px-4 py-3 rounded-xl bg-[#2F7D4A] text-white text-sm font-semibold"
              >
                View Incident
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* MAP */}
          <div className="lg:col-span-3">
            <div className="flex justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold">
                  Live Incident Map
                </h2>
                <p className="text-xs text-gray-600 mt-1">
                  Geographical overview of the incident
                </p>
              </div>

              <MapPin className="w-5 h-5 text-gray-500" />
            </div>

            <div className="h-[520px] rounded-2xl overflow-hidden border border-[#DDE5DE] shadow-sm">
              <MapContainer
                center={location}
                zoom={12}
                scrollWheelZoom
                className="h-full w-full"
              >
                <TileLayer
                  attribution="&copy; OpenStreetMap contributors"
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <Marker position={location}>
                  <Popup>
                    <b>{ai?.disaster_type || "Possible Incident"}</b>
                    <br />
                    Priority: {priority.toUpperCase()}
                    <br />
                    Location: {report?.location || "Delhi"}
                  </Popup>
                </Marker>
              </MapContainer>
            </div>
          </div>
        </div>

        <div className="flex justify-end items-center gap-2 text-xs text-gray-700 mt-5">
          <Clock className="w-3.5 h-3.5" />
          Last updated just now
        </div>

      </main>
      <ResponderChatbot report={report}/>
    </div>
  );
}

export default Dashboard;