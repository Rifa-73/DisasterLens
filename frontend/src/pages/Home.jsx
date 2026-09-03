import Navbar from "../components/Navbar";
import {
  ArrowRight,
  Brain,
  Camera,
  Video,
  MapPin,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F7F8F5] text-[#17201A]">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid lg:grid-cols-2 gap-16 items-center">

          {/* LEFT */}
          <section>
            <div className="inline-flex items-center gap-2 px-3 py-2 rounded-full border border-[#DDE5DE] bg-white text-xs text-[#68736B]">
              <span className="w-2 h-2 rounded-full bg-[#2F7D4A] animate-pulse" />
              MULTIMODAL DISASTER INTELLIGENCE
            </div>

            <h1 className="mt-7 text-5xl md:text-6xl font-bold leading-tight">
              From scattered
              <br />
              information
              <br />
              <span className="text-[#68736B]">
                to life-saving action.
              </span>
            </h1>

            <p className="mt-6 max-w-xl text-lg text-[#68736B] leading-relaxed">
              RNR combines images, videos, audio and reports with AI
              to help identify and prioritize disaster situations faster.
            </p>

            <div className="flex flex-wrap gap-4 mt-8">
              <button
                onClick={() => navigate("/report")}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-[#2F7D4A] text-white font-semibold hover:bg-[#25663C] transition"
              >
                Report an Incident
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => navigate("/dashboard")}
                className="flex items-center gap-2 px-6 py-3 rounded-xl border border-[#DDE5DE] bg-white hover:bg-[#F3F7F3] transition"
              >
                <MapPin className="w-4 h-4 text-[#2F7D4A]" />
                Live Dashboard
              </button>
            </div>
          </section>

          {/* AI VISUAL */}
          <section>
            <div className="h-[420px] rounded-3xl border border-[#DDE5DE] bg-white p-6 relative overflow-hidden shadow-sm">

              <div className="flex justify-between">
                <div>
                  <p className="text-sm font-semibold">
                    MULTIMODAL ANALYSIS
                  </p>
                  <p className="text-xs text-[#68736B] mt-1">
                    Combining multiple evidence sources
                  </p>
                </div>

                <span className="text-xs text-[#2F7D4A]">
                  ● AI READY
                </span>
              </div>

              {/* AI CENTER */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="relative">
                  <div className="absolute -inset-8 bg-[#2F7D4A]/10 blur-3xl rounded-full" />
                  <div className="relative w-28 h-28 rounded-full border border-[#8FBE9C] bg-[#EAF4EC] flex items-center justify-center">
                    <Brain className="w-10 h-10 text-[#2F7D4A]" />
                  </div>
                </div>
              </div>

              {/* INPUTS */}
              <div className="absolute top-28 left-10 text-center">
                <div className="w-14 h-14 rounded-2xl bg-[#EAF4EC] flex items-center justify-center">
                  <Camera className="text-[#2F7D4A]" />
                </div>
                <p className="text-xs text-[#68736B] mt-2">Image</p>
              </div>

              <div className="absolute top-40 right-10 text-center">
                <div className="w-14 h-14 rounded-2xl bg-[#EAF4EC] flex items-center justify-center">
                  <Video className="text-[#2F7D4A]" />
                </div>
                <p className="text-xs text-[#68736B] mt-2">Video</p>
              </div>

              <div className="absolute bottom-20 left-16 text-center">
                <div className="w-14 h-14 rounded-2xl bg-[#F3F7F3] flex items-center justify-center">
                  <div className="flex gap-1 items-end">
                    {[3, 5, 4, 6].map((h, i) => (
                      <span
                        key={i}
                        style={{ height: `${h * 4}px` }}
                        className="w-1 bg-[#2F7D4A] rounded-full animate-pulse"
                      />
                    ))}
                  </div>
                </div>
                <p className="text-xs text-[#68736B] mt-2">Audio</p>
              </div>

              {/* RESULT */}
              <div className="absolute bottom-16 right-8 px-4 py-3 rounded-xl bg-[#FFF4F2] border border-[#F3D5D0]">
                <p className="text-xs text-red-600 font-semibold">
                  PRIORITY ASSESSMENT
                </p>
                <p className="text-sm mt-1 font-medium">
                  Possible Flood
                </p>
                <p className="text-xs text-[#68736B] mt-1">
                  Requires further assessment
                </p>
              </div>

              <div className="absolute bottom-4 left-6 right-6 flex justify-between text-[10px] text-[#8A938C]">
                <span>IMAGE • VIDEO • AUDIO • TEXT</span>
                <span>MULTIMODAL AI</span>
              </div>

            </div>
          </section>

        </div>
      </main>
    </div>
  );
}

export default Home;