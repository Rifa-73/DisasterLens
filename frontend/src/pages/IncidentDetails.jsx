import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Image,
  Video,
  Mic,
  Clock,
  MapPin,
} from "lucide-react";

import Navbar from "../components/Navbar";

const API = "http://localhost:8000";

function mediaUrl(url) {
  if (!url) return null;

  // Keep local data URLs unchanged
  if (url.startsWith("data:")) return url;

  // Keep complete URLs unchanged
  if (url.startsWith("http")) return url;

  return `${API}${url}`;
}

function IncidentDetails() {
  const navigate = useNavigate();
  const [report, setReport] = useState(null);

  useEffect(() => {
    const saved = localStorage.getItem("rnrReport");

    if (saved) {
      try {
        setReport(JSON.parse(saved));
      } catch {
        setReport(null);
      }
    }
  }, []);

  if (!report) {
    return (
      <div className="min-h-screen bg-[#F8F9F6]">
        <Navbar />

        <div className="max-w-4xl mx-auto px-6 py-20 text-center">
          <p className="text-sm text-gray-500">No incident selected.</p>

          <button
            onClick={() => navigate("/dashboard")}
            className="mt-4 text-sm font-semibold text-[#3F6546]"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const ai = report.aiAssessment || {};
  const cv = report.cvAssessment || {};
  const batch = report.batchAnalysis;
  const videoAnalysis = report.videoAnalysis;

  const priority =
    ai.priority?.toLowerCase() === "high"
      ? "high"
      : ai.priority?.toLowerCase() === "medium"
      ? "medium"
      : cv.severity_level?.toLowerCase() === "severe"
      ? "high"
      : cv.severity_level?.toLowerCase() === "moderate"
      ? "medium"
      : "low";

  // FIXED IMAGE HANDLING
  const storedImages = Array.isArray(report.evidence?.images)
    ? report.evidence.images
    : [];

  const backendImages =
    report.imageUrls ||
    report.image_urls ||
    [];

  const images =
    storedImages.length > 0
      ? storedImages
      : backendImages.map((url, i) => ({
          data: url,
          name: `Evidence image ${i + 1}`,
        }));

  const finalImages =
    images.length > 0
      ? images
      : report.evidence?.image
      ? [{ data: report.evidence.image, name: "Evidence image" }]
      : [];

  const video = mediaUrl(
    report.evidence?.video || report.video_url
  );

  const audio = mediaUrl(
    report.evidence?.audio || report.audio_url
  );

  const reportTime = report.created_at
    ? new Date(report.created_at).toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "N/A";

  return (
    <div className="min-h-screen bg-[#F8F9F6] text-[#263229]">
      <Navbar />

      <main className="max-w-7xl mx-auto px-5 md:px-8 py-7">
        {/* TOP BAR */}
        <div className="flex items-center gap-3 mb-5">
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-1 text-[10px] text-[#607067]"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Live Dashboard
          </button>

          <span className="text-gray-300">/</span>

          <span className="text-xs font-semibold">
            Report #{report.id}
          </span>

          <SeverityBadge priority={priority} />
        </div>

        {/* MAIN */}
        <div className="grid lg:grid-cols-2 bg-white border border-[#DDE4DB] rounded-xl overflow-hidden">

          {/* EVIDENCE */}
          <section className="p-5 md:p-6 border-b lg:border-b-0 lg:border-r border-[#E5EAE3]">
            <Label>SUBMITTED EVIDENCE</Label>

            {finalImages.length ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
                {finalImages.map((item, index) => (
                  <div
                    key={`${item.name}-${index}`}
                    className="border border-[#E1E6DF] rounded-xl overflow-hidden"
                  >
                    <div className="h-[190px] bg-[#EAF1E8]">
                      <img
                        src={mediaUrl(item.data)}
                        alt={item.name || `Evidence ${index + 1}`}
                        className="w-full h-full object-cover"
                      />
                    </div>

                    <div className="px-3 py-2 border-t text-[9px] text-[#7C867F] flex items-center gap-1">
                      <Image className="w-3 h-3" />
                      {item.name || `Evidence image ${index + 1}`}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-4 h-[230px] border border-[#E1E6DF] rounded-xl bg-[#EAF1E8] flex items-center justify-center text-center text-[#7D887F]">
                <div>
                  <Image className="w-8 h-8 mx-auto" />
                  <p className="text-xs mt-2">
                    Image evidence unavailable
                  </p>
                </div>
              </div>
            )}

            {finalImages.length > 1 && (
              <div className="mt-3 p-3 rounded-xl bg-[#F3F7F3] border border-[#E1E6DF]">
                <p className="text-[9px] font-bold text-[#718078]">
                  IMAGE EVIDENCE
                </p>

                <p className="text-sm font-semibold mt-1">
                  {finalImages.length} images submitted
                </p>
              </div>
            )}

            {/* VIDEO */}
            {video && (
              <div className="mt-3 border border-[#E1E6DF] rounded-xl overflow-hidden">
                <video
                  src={video}
                  controls
                  className="w-full max-h-[300px] bg-black"
                />

                <div className="px-3 py-2 border-t text-[9px] text-[#7C867F] flex items-center gap-1">
                  <Video className="w-3 h-3" />
                  Video evidence
                </div>
              </div>
            )}

            {/* AUDIO */}
            {audio && (
              <div className="mt-3 border border-[#E1E6DF] rounded-xl p-3">
                <div className="flex items-center gap-2 mb-2">
                  <Mic className="w-3.5 h-3.5 text-[#3F6546]" />
                  <span className="text-[9px] font-semibold">
                    Audio evidence
                  </span>
                </div>

                <audio
                  src={audio}
                  controls
                  className="w-full"
                />
              </div>
            )}
          </section>

          {/* GEMINI + CVDL */}
          <section className="p-5 md:p-6">
            <Label>GEMINI + CVDL ANALYSIS</Label>

            <div className="mt-4 p-4 rounded-xl bg-[#F8FAF7] border border-[#E1E6DF]">
              <p className="text-[10px] leading-relaxed text-[#69756D]">
                {ai.reason ||
                  "AI analysis is available for this incident. Review the evidence and CVDL assessment before dispatching a response team."}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-3">
              <div className="p-4 rounded-xl bg-[#FDE7E6]">
                <p className="text-[8px] font-bold text-[#B94A46]">
                  PRIORITY
                </p>

                <p className="text-2xl font-bold text-[#C83F3B] mt-1">
                  {priority.toUpperCase()}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#EAF2E7]">
                <p className="text-[8px] font-bold text-[#55755A]">
                  FLOOD COVERAGE
                </p>

                <p className="text-2xl font-bold text-[#45664B] mt-1">
                  {cv.flood_coverage_pct ?? 0}%
                </p>
              </div>
            </div>

            {ai.needs_human_verification && (
              <div className="mt-3 p-3 rounded-xl bg-[#FFF1DD] border border-[#F3D7AE]">
                <p className="text-[10px] font-bold text-[#9A671D]">
                  Human Verification Required
                </p>

                <p className="text-[9px] text-[#9A7A4C] mt-1">
                  Review the evidence before dispatching a response team.
                </p>
              </div>
            )}

            {/* REPORT DETAILS */}
            <div className="mt-5">
              <Label>REPORT DETAILS</Label>

              <div className="mt-3 border border-[#E1E6DF] rounded-xl overflow-hidden">
                <Detail label="Report" value={`#${report.id}`} />

                <Detail
                  label="Location"
                  value={report.location || "Unavailable"}
                  icon={MapPin}
                />

                <Detail
                  label="Time"
                  value={reportTime}
                  icon={Clock}
                />

                <Detail
                  label="Severity"
                  value={cv.severity_level || ai.priority || "N/A"}
                  badge
                />

                <Detail
                  label="Disaster Type"
                  value={ai.disaster_type || "Possible Flood"}
                />
              </div>
            </div>
          </section>
        </div>

        {/* MULTI IMAGE ANALYSIS */}
        {batch && (
          <section className="mt-5 bg-white border border-[#DDE4DB] rounded-xl p-5">
            <Label>MULTI-IMAGE ANALYSIS</Label>

            <h2 className="text-lg font-semibold mt-2">
              CVDL Evidence Ranking
            </h2>

            <p className="text-xs text-[#7A867D] mt-1">
              {batch.total_images} images analyzed and ranked by flood coverage.
            </p>

            <div className="grid md:grid-cols-2 gap-2 mt-5">
              {batch.results?.map((item) => (
                <div
                  key={item.filename}
                  className="flex justify-between items-center p-3 rounded-xl bg-[#F5F7F4] border border-[#E6EBE4]"
                >
                  <div className="min-w-0">
                    <p className="text-xs font-semibold truncate">
                      #{item.rank} · {item.filename}
                    </p>

                    <p className="text-[10px] text-[#7A867D] mt-1">
                      CVDL severity
                    </p>
                  </div>

                  <div className="text-right ml-3">
                    <p className="text-xs font-bold">
                      {item.severity?.severity_level}
                    </p>

                    <p className="text-[10px] text-[#68736B]">
                      {item.severity?.flood_coverage_pct}% coverage
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 p-4 rounded-xl bg-[#EAF4EC]">
              <p className="text-[9px] font-bold tracking-wider text-[#527057]">
                HIGHEST SEVERITY IMAGE
              </p>

              <p className="text-sm font-bold mt-1">
                {batch.highest_severity?.filename || "N/A"}
              </p>

              <p className="text-xs text-[#68736B] mt-1">
                {batch.highest_severity?.severity?.severity_level || "N/A"}
                {" · "}
                {batch.highest_severity?.severity?.flood_coverage_pct ?? 0}%
                flood coverage
              </p>
            </div>
          </section>
        )}

        {/* VIDEO ANALYSIS */}
        {videoAnalysis && (
          <section className="mt-5 bg-white border border-[#DDE4DB] rounded-xl p-5">
            <Label>VIDEO ANALYSIS</Label>

            <h2 className="text-lg font-semibold mt-2">
              Frame-by-Frame CVDL Assessment
            </h2>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
              <Metric
                label="FRAMES ANALYZED"
                value={videoAnalysis.frames_analyzed}
              />

              <Metric
                label="AVG COVERAGE"
                value={`${videoAnalysis.average_flood_coverage_pct ?? 0}%`}
              />

              <Metric
                label="PEAK COVERAGE"
                value={`${videoAnalysis.peak_flood_coverage_pct ?? 0}%`}
              />

              <Metric
                label="PEAK FRAME"
                value={`#${videoAnalysis.peak_frame ?? 0}`}
              />
            </div>

            <div className="grid grid-cols-3 gap-2 mt-3">
              <FrameStat label="HIGH FRAMES" value={videoAnalysis.high_frames} />
              <FrameStat label="MEDIUM FRAMES" value={videoAnalysis.medium_frames} />
              <FrameStat label="LOW FRAMES" value={videoAnalysis.low_frames} />
            </div>
          </section>
        )}

        {/* ACTIONS */}
        <div className="grid md:grid-cols-3 gap-2 mt-8">
          <button
            onClick={() => navigate("/dashboard")}
            className="px-3 py-2.5 rounded-lg border border-[#DDE4DB] text-[9px] font-semibold text-[#66736A]"
          >
            Back
          </button>

          <button className="px-3 py-2.5 rounded-lg border border-[#BFD0C0] text-[9px] font-semibold text-[#4B694F]">
            Assign Team
          </button>

          <button className="px-3 py-2.5 rounded-lg bg-[#D93636] text-white text-[9px] font-semibold">
            Escalate Now
          </button>
        </div>
      </main>
    </div>
  );
}

function Label({ children }) {
  return (
    <p className="text-[8px] tracking-[0.2em] font-bold text-[#7A867D]">
      {children}
    </p>
  );
}

function Metric({ label, value }) {
  return (
    <div className="p-3 rounded-xl bg-[#F5F7F4] border border-[#E5EAE3]">
      <p className="text-[8px] font-bold text-[#7A867D]">{label}</p>
      <p className="text-lg font-bold mt-1">{value ?? "N/A"}</p>
    </div>
  );
}

function FrameStat({ label, value }) {
  return (
    <div className="p-3 rounded-xl bg-[#F8F9F6] border border-[#E5EAE3] text-center">
      <p className="text-[8px] font-bold text-[#7A867D]">{label}</p>
      <p className="text-lg font-bold mt-1">{value ?? 0}</p>
    </div>
  );
}

function Detail({ label, value, icon: Icon, badge }) {
  return (
    <div className="grid grid-cols-[90px_1fr] items-center px-4 py-3 border-b last:border-b-0 border-[#EDF0EB]">
      <span className="text-[9px] text-[#879189]">{label}</span>

      <span className="flex items-center gap-1.5 text-[10px] font-medium">
        {Icon && <Icon className="w-3 h-3 text-[#718078]" />}

        {badge ? (
          <span className="px-2 py-1 rounded bg-[#FDE7E6] text-[#D44743] text-[8px] font-bold">
            {String(value).toUpperCase()}
          </span>
        ) : (
          value
        )}
      </span>
    </div>
  );
}

function SeverityBadge({ priority }) {
  const styles = {
    high: "bg-[#FDE7E6] text-[#D44743]",
    medium: "bg-[#FFF0DC] text-[#B56A18]",
    low: "bg-[#FFF8D9] text-[#8C7618]",
  };

  return (
    <span
      className={`px-2 py-1 rounded-md text-[8px] font-bold ${
        styles[priority] || "bg-gray-100 text-gray-500"
      }`}
    >
      {priority.toUpperCase()}
    </span>
  );
}

export default IncidentDetails;