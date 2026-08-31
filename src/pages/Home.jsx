import Navbar from "../components/Navbar";
import { ArrowRight, Brain, Camera, MapPin, Video } from "lucide-react";

function Home() {
  return (
    <div className="min-h-screen bg-[#F7F8F5] text-[#17201A]">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 pt-20">

        <div className="grid lg:grid-cols-2 gap-16 items-center">

          {/* LEFT SIDE */}
          <div>

            <div className="inline-flex items-center gap-2 px-3 py-2 rounded-full border border-white/10 bg-white/5 text-xs text-gray-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              MULTIMODAL DISASTER INTELLIGENCE
            </div>

              <h1 className="mt-7 text-5xl md:text-6xl font-bold leading-tight text-[#17201A]">
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

            <div className="flex gap-4 mt-8">

              <button
                onClick={() => window.location.href = "/report"}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-white text-black font-semibold hover:bg-gray-200 transition"
              >
                Report an Incident
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => window.location.href = "/dashboard"}
                className="flex items-center gap-2 px-6 py-3 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 transition"
              >
                <MapPin className="w-4 h-4" />
                Live Dashboard
              </button>

            </div>

          </div>


          {/* RIGHT SIDE — AI VISUAL */}
          <div className="relative">

            <div className="h-[420px] rounded-3xl border border-[#DDE5DE] bg-white p-6 relative overflow-hidden shadow-sm">

              {/* Heading */}
              <div className="flex justify-between items-center">

                <div>
                  <p className="text-sm font-semibold">
                    MULTIMODAL ANALYSIS
                  </p>

                  <p className="text-xs text-gray-500 mt-1">
                    Processing incoming evidence
                  </p>
                </div>

                <span className="text-xs text-emerald-400">
                  ● LIVE
                </span>

              </div>


              {/* AI CENTER */}
              <div className="absolute inset-0 flex items-center justify-center">

                <div className="relative">

                  <div className="absolute -inset-8 bg-cyan-400/10 blur-3xl rounded-full" />

                  <div className="relative w-28 h-28 rounded-full border border-[#8FBE9C] bg-[#EAF4EC] flex items-center justify-center">

                    <Brain className="w-10 h-10 text-[#2F7D4A]" />

                  </div>

                </div>

              </div>


              {/* IMAGE */}
              <div className="absolute top-28 left-10">

                <div className="w-14 h-14 rounded-2xl bg-[#EAF4EC] border border-[#DDE5DE] flex items-center justify-center">
                  <Camera className="text-[#2F7D4A]" />
                </div>

                <p className="text-xs text-gray-500 mt-2">
                  Image
                </p>

              </div>


              {/* VIDEO */}
              <div className="absolute top-40 right-10">

                <div className="w-14 h-14 rounded-2xl bg-[#EAF4EC] border border-[#DDE5DE] flex items-center justify-center">
                  <Video className="text-[#2F7D4A]" />
                </div>

                <p className="text-xs text-gray-500 mt-2">
                  Video
                </p>

              </div>


              {/* AUDIO */}
              <div className="absolute bottom-20 left-16">

                <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">

                  <div className="flex gap-1 items-end">

                    <span className="w-1 h-3 bg-[#2F7D4A] rounded-full animate-pulse" />
                    <span className="w-1 h-5 bg-[#2F7D4A] rounded-full animate-pulse" />
                    <span className="w-1 h-4 bg-[#2F7D4A] rounded-full animate-pulse" />
                    <span className="w-1 h-6 bg-[#2F7D4A] rounded-full animate-pulse" />
                  </div>

                </div>

                <p className="text-xs text-gray-500 mt-2">
                  Audio
                </p>

              </div>


              {/* RESULT */}
              <div className="absolute bottom-16 right-8">

                <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-400/20">

                  <p className="text-xs text-red-400 font-semibold">
                    HIGH PRIORITY
                  </p>

                  <p className="text-sm mt-1">
                    Possible Flood
                  </p>

                  <p className="text-xs text-gray-500 mt-1">
                    Confidence 92%
                  </p>

                </div>

              </div>


              {/* Bottom */}
              <div className="absolute bottom-4 left-6 right-6 flex justify-between text-[10px] text-gray-600">

                <span>
                  IMAGE • VIDEO • AUDIO • TEXT
                </span>

                <span>
                  AI READY
                </span>

              </div>

            </div>

          </div>

        </div>

      </main>

    </div>
  );
}

export default Home;