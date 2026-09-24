import Navbar from "../components/Navbar";
import { ArrowRight, Brain, Camera, Video, MapPin, Mic } from "lucide-react";
import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F8F9F6] text-[#263229]">
      <Navbar />

      <main className="max-w-7xl mx-auto px-5 md:px-8 py-16 md:py-20">

        <section className="text-center max-w-4xl mx-auto">
          <p className="text-[10px] tracking-[0.28em] font-bold text-[#53795A]">
            AI-POWERED FLOOD RESPONSE
          </p>

          <h1 className="mt-5 text-4xl md:text-6xl font-bold leading-[1.05]">
            See flooding as it happens.
            <br />
            <span className="text-[#647067]">Respond before it spreads.</span>
          </h1>

          <p className="max-w-2xl mx-auto mt-6 text-sm md:text-base leading-relaxed text-[#748078]">
            Citizens report with a photo, video or voice note. DisasterLens
            verifies evidence, scores severity and puts every incident on a
            live map for response teams.
          </p>

          <div className="flex justify-center gap-3 mt-7 flex-wrap">
            <button
              onClick={() => navigate("/report")}
              className="flex items-center gap-2 px-5 py-3 rounded-lg bg-[#3F6546] text-white text-xs font-semibold hover:bg-[#315338]"
            >
              Report an Incident
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => navigate("/dashboard")}
              className="flex items-center gap-2 px-5 py-3 rounded-lg border border-[#D8DED7] bg-white text-[#435247] text-xs font-semibold hover:bg-[#F1F4F0]"
            >
              <MapPin className="w-3.5 h-3.5" />
              View Live Dashboard
            </button>
          </div>

          <div className="inline-flex items-center gap-2 mt-5 px-3 py-1.5 rounded-full bg-[#EAF1E7] text-[10px] text-[#527057]">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
            3 incidents reported in the last hour
          </div>
        </section>

        <section className="grid md:grid-cols-3 gap-4 mt-14">

          <Step
            number="1"
            title="Submit evidence"
            text="Photo, video or audio location, in under a minute."
            icon={Camera}
          />

          <Step
            number="2"
            title="AI analysis"
            text="U-Net segmentation plus Gemini and CVDL scoring for severity."
            icon={Brain}
          />

          <Step
            number="3"
            title="Live on the map"
            text="Verified incidents appear for response teams instantly."
            icon={MapPin}
          />

        </section>

        <section className="mt-10 bg-white border border-[#E1E6DF] rounded-2xl p-7 md:p-10">

          <div className="flex justify-between items-start">
            <div>
              <p className="text-[9px] tracking-[0.2em] font-bold text-[#718075]">
                MULTIMODAL ANALYSIS
              </p>

              <h2 className="text-xl font-bold mt-2">
                One incident. Multiple evidence sources.
              </h2>
            </div>

            <span className="text-[10px] text-[#4E7656] font-semibold">
              ● AI READY
            </span>
          </div>

          <div className="grid md:grid-cols-4 gap-4 mt-8">

            <Evidence icon={Camera} label="Image" />
            <Evidence icon={Video} label="Video" />
            <Evidence icon={Mic} label="Audio" />

            <div className="rounded-xl bg-[#F6F8F4] border border-[#E1E6DF] p-4">
              <p className="text-[9px] tracking-wider text-[#789080]">
                OUTPUT
              </p>

              <p className="font-semibold text-sm mt-2">
                Priority Assessment
              </p>

              <span className="inline-block mt-2 px-2 py-1 rounded-md bg-[#FDE9E8] text-[9px] text-red-600 font-bold">
                POSSIBLE FLOOD
              </span>
            </div>

          </div>
        </section>
      </main>
    </div>
  );
}

function Step({ number, title, text, icon: Icon }) {
  return (
    <div className="bg-white border border-[#E1E6DF] rounded-xl p-5">
      <Icon className="w-4 h-4 text-[#4F7657]" />

      <p className="text-xs font-semibold mt-5">
        {number} · {title}
      </p>

      <p className="text-[10px] leading-relaxed text-[#778279] mt-2">
        {text}
      </p>
    </div>
  );
}

function Evidence({ icon: Icon, label }) {
  return (
    <div className="flex items-center gap-3 p-4 rounded-xl bg-[#F6F8F4] border border-[#E1E6DF]">
      <div className="w-9 h-9 rounded-lg bg-[#E7EFE5] flex items-center justify-center">
        <Icon className="w-4 h-4 text-[#4F7657]" />
      </div>

      <span className="text-xs font-medium">{label}</span>
    </div>
  );
}

export default Home;