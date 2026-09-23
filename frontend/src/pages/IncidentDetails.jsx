import Navbar from "../components/Navbar";
import {
  ArrowLeft,
  MapPin,
  AlertTriangle,
  Video,
  Mic,
  ShieldAlert,
  CheckCircle,
  XCircle,
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

  const evidenceAssessment = report.evidenceAssessment;

  const reliability =
    evidenceAssessment?.reliability?.toLowerCase() || "unknown";

  const reliabilityStyle =
    reliability === "high"
      ? "text-[#2F7D4A]"
      : reliability === "moderate"
      ? "text-[#D97706]"
      : reliability === "low"
      ? "text-[#DC2626]"
      : "text-[#68736B]";

  const humanVerificationRequired =
    evidenceAssessment?.human_verification_required ||
    report.aiAssessment?.needs_human_verification;

  return (
    <div className="min-h-screen bg-[#F7F8F5] text-[#17201A]">
      <Navbar />

      <main className="max-w-5xl mx-auto px-6 py-10">

        {/* BACK */}
        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-2 text-sm text-[#68736B] hover:text-[#2F7D4A]"
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
              {report.aiAssessment?.disaster_type ||
                "Possible Incident"}
            </h1>

            <span
              className={`inline-flex w-fit px-4 py-2 rounded-full text-white text-xs font-bold ${priorityStyle}`}
            >
              {priority.toUpperCase()} PRIORITY
            </span>
          </div>

          <div className="flex items-center gap-2 text-sm text-[#68736B] mt-4">
            <MapPin className="w-4 h-4" />
            {report.location || "Location unavailable"}
          </div>
        </div>

        {/* HUMAN VERIFICATION STATUS */}
        <div
          className={`mt-6 p-6 rounded-2xl border shadow-sm ${
            humanVerificationRequired
              ? "bg-amber-50 border-amber-200"
              : "bg-[#EAF4EC] border-[#BFDAC5]"
          }`}
        >
          <div className="flex items-start gap-4">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                humanVerificationRequired
                  ? "bg-amber-100"
                  : "bg-white"
              }`}
            >
              {humanVerificationRequired ? (
                <AlertTriangle className="w-5 h-5 text-amber-600" />
              ) : (
                <CheckCircle className="w-5 h-5 text-[#2F7D4A]" />
              )}
            </div>

            <div>
              <p className="text-xs font-semibold tracking-wide">
                VERIFICATION STATUS
              </p>

              <h2
                className={`text-lg font-semibold mt-1 ${
                  humanVerificationRequired
                    ? "text-amber-700"
                    : "text-[#2F7D4A]"
                }`}
              >
                {humanVerificationRequired
                  ? "Human Verification Required"
                  : "No Human Verification Required"}
              </h2>

              <p className="text-sm mt-2 text-[#68736B]">
                {humanVerificationRequired
                  ? "AI-generated assessment or evidence cross-check requires responder review before action."
                  : "Available AI and evidence checks do not currently require additional human verification."}
              </p>
            </div>
          </div>
        </div>

        {/* AI ASSESSMENT */}
        <div className="mt-6 p-6 rounded-2xl bg-white border border-[#DDE5DE] shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#EAF4EC] flex items-center justify-center">
              <ShieldAlert className="w-5 h-5 text-[#2F7D4A]" />
            </div>

            <div>
              <h2 className="font-semibold">AI Assessment</h2>
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
                {report.aiAssessment?.disaster_type ||
                  "Unknown"}
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[#F7F8F5]">
              <p className="text-xs text-[#68736B]">
                AI Likelihood
              </p>
              <p className="font-semibold mt-1 capitalize">
                {report.aiAssessment?.likelihood ||
                  "Unknown"}
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
        </div>

        {/* EVIDENCE RELIABILITY */}
        {evidenceAssessment && (
          <div className="mt-6 p-6 rounded-2xl bg-white border border-[#DDE5DE] shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#EAF4EC] flex items-center justify-center">
                <ShieldAlert className="w-5 h-5 text-[#2F7D4A]" />
              </div>

              <div>
                <h2 className="font-semibold">
                  Evidence Reliability
                </h2>

                <p className="text-xs text-[#68736B]">
                  Cross-check between independent AI evidence sources
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-4 mt-6">

              {/* AGREEMENT */}
              <div className="p-4 rounded-xl bg-[#F7F8F5]">
                <p className="text-xs text-[#68736B]">
                  Evidence Agreement
                </p>

                <div className="flex items-center gap-2 mt-2">
                  {evidenceAssessment.agreement ? (
                    <>
                      <CheckCircle className="w-5 h-5 text-[#2F7D4A]" />
                      <span className="font-semibold text-[#2F7D4A]">
                        Consistent
                      </span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-5 h-5 text-[#DC2626]" />
                      <span className="font-semibold text-[#DC2626]">
                        Conflicting
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* RELIABILITY */}
              <div className="p-4 rounded-xl bg-[#F7F8F5]">
                <p className="text-xs text-[#68736B]">
                  Reliability
                </p>

                <p
                  className={`font-semibold mt-2 capitalize ${reliabilityStyle}`}
                >
                  {reliability}
                </p>
              </div>

              {/* CONTRADICTION */}
              <div className="p-4 rounded-xl bg-[#F7F8F5]">
                <p className="text-xs text-[#68736B]">
                  Contradiction
                </p>

                <p
                  className={`font-semibold mt-2 ${
                    evidenceAssessment.contradiction
                      ? "text-[#DC2626]"
                      : "text-[#2F7D4A]"
                  }`}
                >
                  {evidenceAssessment.contradiction
                    ? "Detected"
                    : "None detected"}
                </p>
              </div>
            </div>

            {/* REASON */}
            {evidenceAssessment.reason && (
              <div className="mt-5">
                <p className="text-xs text-[#68736B]">
                  Cross-Check Result
                </p>

                <p className="text-sm leading-relaxed mt-2">
                  {evidenceAssessment.reason}
                </p>
              </div>
            )}
          </div>
        )}

        {/* DESCRIPTION */}
        <div className="mt-6 p-6 rounded-2xl bg-white border border-[#DDE5DE] shadow-sm">
          <h2 className="font-semibold">
            Reporter Description
          </h2>

          <p className="text-sm text-[#68736B] mt-3 leading-relaxed">
            {report.description ||
              "No description provided."}
          </p>
        </div>

        {/* EVIDENCE */}
        <div className="mt-6">
          <h2 className="font-semibold">
            Submitted Evidence
          </h2>

          <div className="grid md:grid-cols-3 gap-4 mt-4">

            {/* IMAGE */}
            {report?.evidence?.image && (
              <div className="p-5 rounded-2xl bg-white border border-[#DDE5DE]">
                <p className="text-sm font-semibold mb-3">
                  Image Evidence
                </p>

                <img
                  src={report.evidence.image}
                  alt="Incident evidence"
                  className="w-full rounded-xl border border-[#DDE5DE]"
                />
              </div>
            )}

            {/* VIDEO */}
            {report.evidence?.video && (
              <div className="p-5 rounded-2xl bg-white border border-[#DDE5DE]">
                <Video className="w-6 h-6 text-[#2F7D4A]" />

                <p className="font-semibold mt-4">
                  Video Evidence
                </p>

                <video
                  src={`http://127.0.0.1:8000${report.evidence.video}`}
                  controls
                  className="w-full mt-3 rounded-xl"
                />
              </div>
            )}

            {/* AUDIO */}
            {report.evidence?.audio && (
              <div className="p-5 rounded-2xl bg-white border border-[#DDE5DE]">
                <Mic className="w-6 h-6 text-[#2F7D4A]" />

                <p className="font-semibold mt-4">
                  Audio Evidence
                </p>

                <audio
                  src={`http://127.0.0.1:8000${report.evidence.audio}`}
                  controls
                  className="w-full mt-3"
                />
              </div>
            )}
          </div>
        </div>

        {/* CVDL */}
        {report.cvAssessment && (
          <div className="mt-6 p-6 rounded-2xl bg-white border border-[#DDE5DE] shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#EAF4EC] flex items-center justify-center">
                <ShieldAlert className="w-5 h-5 text-[#2F7D4A]" />
              </div>

              <div>
                <h2 className="font-semibold">
                  CVDL Flood Analysis
                </h2>

                <p className="text-xs text-[#68736B]">
                  Computer vision based flood assessment
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-4 mt-6">
              <div className="p-4 rounded-xl bg-[#F7F8F5]">
                <p className="text-xs text-[#68736B]">
                  Severity
                </p>

                <p className="font-semibold mt-1 capitalize">
                  {report.cvAssessment.severity_level ||
                    "Unknown"}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#F7F8F5]">
                <p className="text-xs text-[#68736B]">
                  Flood Coverage
                </p>

                <p className="font-semibold mt-1">
                  {report.cvAssessment.flood_coverage_pct ??
                    0}
                  %
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#F7F8F5]">
                <p className="text-xs text-[#68736B]">
                  Severity Score
                </p>

                <p className="font-semibold mt-1">
                  {report.cvAssessment.severity_score ??
                    0}
                  /100
                </p>
              </div>
            </div>
          </div>
        )}

        {/* STATUS */}
        <div className="mt-8 p-5 rounded-2xl bg-[#EAF4EC] border border-[#BFDAC5]">
          <p className="text-xs text-[#68736B]">
            CURRENT STATUS
          </p>

          <p className="text-sm font-semibold text-[#2F7D4A] mt-1">
            {report.status ||
              "AWAITING_VERIFICATION"}
          </p>
        </div>
      </main>
    </div>
  );
}

export default IncidentDetails;