import Navbar from "../components/Navbar";
import {
  ArrowLeft,
  MapPin,
  AlertTriangle,
  Image,
  Video,
  Mic,
  ShieldAlert,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

function IncidentDetails() {
  const navigate = useNavigate();
  const [report, setReport] = useState(null);

  useEffect(() => {
    const savedReport = localStorage.getItem("rnrReport");

    if (savedReport) {
      setReport(JSON.parse(savedReport));
    }
  }, []);

  if (!report) {
    return (
      <div className="min-h-screen bg-[#F7F8F5] text-[#17201A]">
        <Navbar />

        <main className="max-w-5xl mx-auto px-6 py-12">
          <p className="text-[#68736B]">
            No incident report found.
          </p>
        </main>
      </div>
    );
  }

  const priority =
    report.aiAssessment?.priority?.toLowerCase() || "unknown";

  const priorityStyle =
    priority === "high"
      ? "bg-[#DC2626]"
      : priority === "medium"
      ? "bg-[#F59E0B]"
      : "bg-[#2F7D4A]";

  return (
    <div className="min-h-screen bg-[#F7F8F5] text-[#17201A]">

      <Navbar />

      <main className="max-w-5xl mx-auto px-6 py-10">

        {/* BACK */}
        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2 text-sm text-[#68736B] hover:text-[#2F7D4A] transition"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to dashboard
        </button>

        {/* HEADER */}
        <div className="mt-8">

          <p className="text-xs tracking-[0.25em] text-[#2F7D4A] font-semibold">
            INCIDENT DETAILS
          </p>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mt-3">

            <h1 className="text-4xl font-bold">
              {report.aiAssessment?.disaster_type || "Possible Incident"}
            </h1>

            <span
              className={`inline-flex w-fit items-center gap-2 px-4 py-2 rounded-full text-white text-xs font-bold`}
            >
              <span
                className={`px-4 py-2 rounded-full ${priorityStyle}`}
              >
                {priority.toUpperCase()} PRIORITY
              </span>
            </span>

          </div>

          {/* LOCATION */}
          <div className="flex items-center gap-2 text-sm text-[#68736B] mt-4">
            <MapPin className="w-4 h-4" />
            {report.location || "Location unavailable"}
          </div>

        </div>


        {/* AI ASSESSMENT */}
        <div className="mt-8 p-6 rounded-2xl bg-white border border-[#DDE5DE] shadow-sm">

          <div className="flex items-center gap-3">

            <div className="w-10 h-10 rounded-xl bg-[#EAF4EC] flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 text-[#2F7D4A]" />
            </div>

            <div>
              <h2 className="font-semibold">
                AI Assessment
              </h2>

              <p className="text-xs text-[#68736B]">
                Automated disaster analysis
              </p>
            </div>

          </div>


          <div className="grid md:grid-cols-2 gap-4 mt-6">

            <div className="p-4 rounded-xl bg-[#F7F8F5]">
              <p className="text-xs text-[#68736B]">
                Disaster Type
              </p>

              <p className="font-semibold mt-1 capitalize">
                {report.aiAssessment?.disaster_type || "Unknown"}
              </p>
            </div>


            <div className="p-4 rounded-xl bg-[#F7F8F5]">
              <p className="text-xs text-[#68736B]">
                AI Likelihood
              </p>

              <p className="font-semibold mt-1 capitalize">
                {report.aiAssessment?.likelihood || "Unknown"}
              </p>
            </div>

          </div>


          <div className="mt-5">

            <p className="text-xs text-[#68736B]">
              AI Reasoning
            </p>

            <p className="text-sm leading-relaxed mt-2">
              {report.aiAssessment?.reason ||
                "No AI assessment available."}
            </p>

          </div>


          {report.aiAssessment?.needs_human_verification && (
            <div className="flex items-center gap-3 mt-5 p-4 rounded-xl bg-amber-50 border border-amber-200">

              <AlertTriangle className="w-5 h-5 text-amber-600" />

              <div>
                <p className="text-sm font-semibold text-amber-700">
                  Human verification required
                </p>

                <p className="text-xs text-amber-600 mt-1">
                  AI analysis should be reviewed before response action.
                </p>
              </div>

            </div>
          )}

        </div>


        {/* DESCRIPTION */}
        <div className="mt-6 p-6 rounded-2xl bg-white border border-[#DDE5DE] shadow-sm">

          <h2 className="font-semibold">
            Reporter Description
          </h2>

          <p className="text-sm text-[#68736B] mt-3 leading-relaxed">
            {report.description || "No description provided."}
          </p>

        </div>


        {/* EVIDENCE */}
        <div className="mt-6">

          <h2 className="font-semibold">
            Submitted Evidence
          </h2>

          <div className="grid md:grid-cols-3 gap-4 mt-4">
          {report?.evidence?.image && (
            <div className="mt-6">
              <p className="text-sm font-semibold text-[#17201A] mb-3">
                Uploaded Evidence
              </p>
          
              <img
                src={report.evidence.image}
                alt="Incident evidence"
                className="w-full max-w-2xl rounded-2xl border border-[#DDE5DE] shadow-sm"
              />
            </div>
          )}


            {report.evidence?.video && (
              <div className="p-5 rounded-2xl bg-white border border-[#DDE5DE]">
                <Video className="w-6 h-6 text-[#2F7D4A]" />
                        
                <p className="font-semibold mt-4">Video Evidence</p>
                        
                <video
                  src={`http://127.0.0.1:8000${report.evidence.video}`}
                  controls
                  className="w-full mt-3 rounded-xl"
                />
              </div>
            )}


            {report.evidence?.audio && (
              <div className="p-5 rounded-2xl bg-white border border-[#DDE5DE]">
                <Mic className="w-6 h-6 text-[#2F7D4A]" />

                <p className="font-semibold mt-4">
                  Audio
                </p>

                <p className="text-xs text-[#68736B] mt-1 break-all">
                  {report.evidence.audio}
                </p>
              </div>
            )}

          </div>

        </div>


        {/* STATUS */}
        <div className="mt-8 p-5 rounded-2xl bg-[#EAF4EC] border border-[#BFDAC5]">

          <p className="text-xs text-[#68736B]">
            CURRENT STATUS
          </p>

          <p className="text-sm font-semibold text-[#2F7D4A] mt-1">
            {report.status || "AWAITING_VERIFICATION"}
          </p>

        </div>

      </main>

    </div>
  );
}

export default IncidentDetails;