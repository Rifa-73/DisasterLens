import Navbar from "../components/Navbar";
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

function Dashboard() {
  const report = JSON.parse(localStorage.getItem("rnrReport"));

  return (
    <div className="min-h-screen bg-[#F7F8F5] text-[#17201A]">

      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-10">

        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">

          <div>
            <p className="text-xs tracking-[0.25em] text-[#2F7D4A] font-semibold">
              RESPONSE CENTER
            </p>
              
            <h1 className="text-4xl md:text-5xl font-bold mt-3 text-[#17201A]">
              Incident Dashboard
            </h1>
              
            <p className="text-[#68736B] mt-3">
              Monitor, verify and prioritize incoming disaster incidents.
            </p>

          </div>

          <div className="flex items-center gap-2 px-4 py-2 rounded-full border border-[#BFDAC5] bg-[#EAF4EC]">            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-[#2F7D4A] font-medium">
             SYSTEM LIVE
          </span>
          </div>

        </div>


        {/* STATS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-10">

          <div className="p-5 rounded-2xl border border-red-200 bg-white shadow-sm">
            <p className="text-sm text-[#68736B]">
              High Priority
            </p>

            <p className="text-3xl font-bold mt-2">
              3
            </p>

            <p className="text-xs text-red-400 mt-2">
              Immediate attention
            </p>
          </div>


          <div className="p-5 rounded-2xl border border-amber-200 bg-white shadow-sm">
            <p className="text-sm text-[#68736B]">
              Medium Priority
            </p>

            <p className="text-3xl font-bold mt-2">
              5
            </p>

            <p className="text-xs text-yellow-400 mt-2">
              Requires monitoring
            </p>
          </div>


          <div className="p-5 rounded-2xl border border-[#DDE5DE] bg-white shadow-sm">
            <p className="text-sm text-[#68736B]">
              Active Incidents
            </p>

            <p className="text-3xl font-bold mt-2">
              12
            </p>

            <p className="text-xs text-[#68736B] mt-2">
              Across monitored areas
            </p>
          </div>

        </div>


        {/* MAIN GRID */}
        <div className="grid lg:grid-cols-5 gap-6 mt-8">


          {/* INCIDENT LIST */}
          <div className="lg:col-span-2">

            <div className="flex items-center justify-between mb-4">

              <div>
                <h2 className="text-lg font-semibold">
                  Incoming Incidents
                </h2>

                <p className="text-xs text-gray-600 mt-1">
                  Latest reports requiring attention
                </p>
              </div>

              <Bell className="w-5 h-5 text-gray-500" />

            </div>


            {/* INCIDENT CARD */}
            <div className="p-5 rounded-2xl border border-red-200 bg-white shadow-sm">

              <div className="flex items-start justify-between">

                <div className="flex items-center gap-2">

                  <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />

                    <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#DC2626] text-white text-[11px] font-bold tracking-wide">
                      <span className="w-1.5 h-1.5 rounded-full bg-white" />
                      HIGH PRIORITY
                    </span>

                </div>

                <span className="text-xs text-gray-600">
                  Just now
                </span>

              </div>


              <h3 className="text-xl font-semibold mt-4">
                {report?.type || "Possible Flood"}
              </h3>


              <div className="flex items-center gap-2 text-sm text-[#68736B] mt-3">

                <MapPin className="w-4 h-4" />

                {report?.location || "Kalyanpur, Delhi"}

              </div>

              <div className="flex items-start gap-2 text-sm text-[#68736B] mt-2">
                <AlertTriangle className="w-4 h-4 mt-0.5" />
                
                <span>
                  {report?.description || "No description provided."}
                </span>
              </div>


              <div className="flex items-center gap-2 text-sm text-[#68736B] mt-2">

                <AlertTriangle className="w-4 h-4" />

                AI Confidence: 92%

              </div>


              {/* EVIDENCE */}
              <div className="flex gap-2 mt-5">

                <div className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-white/5 text-xs text-[#68736B]">
                  <Image className="w-3.5 h-3.5" />
                  Image
                </div>

                <div className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-white/5 text-xs text-[#68736B]">
                  <Video className="w-3.5 h-3.5" />
                  Video
                </div>

                <div className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-white/5 text-xs text-[#68736B]">
                  <Mic className="w-3.5 h-3.5" />
                  Audio
                </div>

              </div>


              <button className="w-full flex items-center justify-between mt-6 px-4 py-3 rounded-xl bg-[#2F7D4A] text-white text-sm font-semibold hover:bg-[#25663C] transition">

                View Incident

                <ArrowRight className="w-4 h-4" />

              </button>

            </div>


            {/* SECOND INCIDENT */}
            <div className="p-5 rounded-2xl border border-[#DDE5DE] bg-white shadow-sm mt-4">

              <div className="flex items-center justify-between">

                <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F59E0B] text-white text-[11px] font-bold tracking-wide">
                  <span className="w-1.5 h-1.5 rounded-full bg-white" />
                  MEDIUM PRIORITY
                </span>

                <span className="text-xs text-gray-600">
                  8 min ago
                </span>

              </div>

              <h3 className="text-lg font-semibold mt-4">
                Road Blockage
              </h3>

              <div className="flex items-center gap-2 text-sm text-[#68736B] mt-2">

                <MapPin className="w-4 h-4" />

                Sector 4, Delhi

              </div>

            </div>

          </div>


          {/* MAP PLACEHOLDER */}
          <div className="lg:col-span-3">

            <div className="flex items-center justify-between mb-4">

              <div>
                <h2 className="text-lg font-semibold">
                  Live Incident Map
                </h2>

                <p className="text-xs text-gray-600 mt-1">
                  Geographical overview of active incidents
                </p>
              </div>

              <MapPin className="w-5 h-5 text-gray-500" />

            </div>


            <div className="relative h-[520px] rounded-2xl border border-[#DDE5DE] bg-[#EEF3EE] overflow-hidden shadow-sm">

              {/* GRID */}
              <div className="absolute inset-0 opacity-20"
                style={{
                  backgroundImage:
                    "linear-gradient(rgba(47,125,74,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(47,125,74,0.08) 1px, transparent 1px)",
                  backgroundSize: "40px 40px",
                }}
              />


              {/* MAP LABEL */}
              <div className="absolute top-5 left-5 px-3 py-2 rounded-lg bg-white/90 border border-[#DDE5DE] shadow-sm backdrop-blur">

                <p className="text-xs text-[#68736B]">
                  LIVE MONITORING AREA
                </p>

                <p className="text-sm font-semibold mt-1">
                  Delhi Region
                </p>

              </div>


              {/* INCIDENT MARKERS */}

              <div className="absolute top-[30%] left-[45%]">

                <div className="relative">

                  <div className="absolute -inset-3 rounded-full bg-red-400/20 animate-ping" />

                  <div className="relative w-4 h-4 rounded-full bg-red-400 border-4 border-red-400/20" />

                </div>

              </div>


              <div className="absolute top-[55%] left-[65%]">

                <div className="w-4 h-4 rounded-full bg-yellow-400 border-4 border-yellow-400/20" />

              </div>


              <div className="absolute top-[65%] left-[30%]">

                <div className="w-4 h-4 rounded-full bg-emerald-400 border-4 border-emerald-400/20" />

              </div>


              {/* LEGEND */}
              <div className="absolute bottom-5 left-5 p-3 rounded-xl bg-black/50 border border-white/10 backdrop-blur">

                <div className="flex gap-5 text-xs">

                  <span className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-400" />
                    High
                  </span>

                  <span className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-yellow-400" />
                    Medium
                  </span>

                  <span className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    Low
                  </span>

                </div>

              </div>

            </div>

          </div>

        </div>


        {/* LAST UPDATED */}
        <div className="flex items-center justify-end gap-2 text-xs text-gray-700 mt-5">

          <Clock className="w-3.5 h-3.5" />

          Last updated just now

        </div>

      </main>

    </div>
  );
}

export default Dashboard;