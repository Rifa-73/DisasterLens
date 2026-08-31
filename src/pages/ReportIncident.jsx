import Navbar from "../components/Navbar";
import {
  ArrowLeft,
  Camera,
  Video,
  Mic,
  MapPin,
  Upload,
} from "lucide-react";

import { useNavigate } from "react-router-dom";
import { useState } from "react";

function ReportIncident() {
    const navigate = useNavigate();
    const [image, setImage] = useState(null);
    const [location, setLocation] = useState(null);
    const [video, setVideo] = useState(null);
    const [audio, setAudio] = useState(null);
    const [description, setDescription] = useState("");

  const handleSubmit = () => {
   const report = {
    description,
    location,
    evidence: {
      image: image?.name || null,
      video: video?.name || null,
      audio: audio?.name || null,
    },
    status: "AWAITING_VERIFICATION",
   };

    localStorage.setItem("rnrReport", JSON.stringify(report));
    navigate("/dashboard");
    };

  return (
      <div className="min-h-screen bg-[#F7F8F5] text-[#17201A]">
      <Navbar />

      <main className="max-w-5xl mx-auto px-6 py-12">

        {/* Back */}
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-sm text-[#68736B] hover:text-white transition mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to home
        </button>

        {/* Heading */}
        <div className="max-w-2xl">

          <p className="text-xs tracking-[0.2em] text-[#68736B]">
            REPORT AN INCIDENT
          </p>

          <h1 className="text-4xl md:text-5xl font-bold mt-3 text-[#17201A]">
            What did you observe?
          </h1>

          <p className="text-[#68736B] mt-4 leading-relaxed">
            Share whatever evidence you have. Images, videos, audio,
            and your description can help us understand the situation.
          </p>

        </div>


        {/* Evidence */}
        <div className="mt-10">

            <h2 className="text-lg font-semibold text-[#17201A]">
              Add evidence
            </h2>

            <p className="text-sm text-[#68736B] mt-1">
              You can provide one or multiple types of evidence.
            </p>


          <div className="grid md:grid-cols-3 gap-4 mt-5">

        {/* IMAGE */}

          <label className="group p-6 rounded-2xl border border-[#DDE5DE] bg-white hover:border-[#2F7D4A] transition cursor-pointer text-left">
            <Camera className="w-6 h-6 text-[#2F7D4A]" />
            
            <h3 className="font-semibold mt-5 text-[#17201A]">
              Upload Image
            </h3>
            
            <p className="text-sm text-[#68736B] mt-2">
              Photos of flooding, damage, blocked roads, etc.
            </p>
            
            <div className="text-xs text-[#2F7D4A] mt-5">
              Choose image
            </div>
            
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => setImage(e.target.files[0])}
            />
          </label>

            {image && (
             <div className="mt-4 rounded-2xl overflow-hidden border border-white/10 bg-white/[0.03]">
               <img
                  src={URL.createObjectURL(image)}
                  alt="Selected evidence"
                  className="w-full h-48 object-cover"
              />
    
                 <div className="px-4 py-3 text-xs text-gray-400">
                    Evidence selected: {image.name}
                 </div>
             </div>
            )}


            {/* VIDEO */}

            <label className="group p-6 rounded-2xl border border-[#DDE5DE] bg-white hover:border-[#2F7D4A] transition cursor-pointer text-left">

              <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center">
                <Video className="w-6 h-6 text-[#2F7D4A]" />
              </div>

              <h3 className="font-semibold mt-5">
                Upload Video
              </h3>

              <p className="text-sm text-[#68736B] mt-2">
                Short videos showing the situation.
              </p>

              <div className="flex items-center gap-2 text-xs text-[#2F7D4A] mt-5">
                <Upload className="w-3.5 h-3.5" />
                Choose file
              </div>

              <input
                type="file"
                accept="video/*"
                className="hidden"
                onChange={(e) => setVideo(e.target.files[0])}
              />

              {video && (
                <p className="text-xs text-[#2F7D4A] mt-2">
                  Video selected: {video.name}
                </p>
              )}

            </label>


            {/* AUDIO */}

            <label className="group p-6 rounded-2xl border border-[#DDE5DE] bg-white hover:border-[#2F7D4A] transition text-left">

              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center">
                <Mic className="w-6 h-6 text-[#2F7D4A]" />
              </div>

              <h3 className="font-semibold mt-5">
                Upload Audio
              </h3>

              <p className="text-sm text-[#68736B] mt-2">
                Voice recordings describing the emergency.
              </p>

              <div className="flex items-center gap-2 text-xs text-[#2F7D4A] mt-5">                <Upload className="w-3.5 h-3.5" />
                Choose file
              </div>

              <input
                type="file"
                accept="audio/*"
                className="hidden"
                onChange={(e) => setAudio(e.target.files[0])}
              />

              {audio && (
                <p className="text-xs text-[#2F7D4A] mt-2">
                  Audio selected: {audio.name}
                </p>
              )}

            </label>

          </div>

        </div>


        {/* DESCRIPTION */}
        <div className="mt-10">

          <label className="text-sm font-semibold">
            Describe what you observed
          </label>

            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="For example: Water has risen above the road near..."
              className="w-full h-32 mt-3 rounded-2xl border border-[#DDE5DE] bg-white p-4 text-sm text-[#17201A] placeholder:text-[#9AA39C] outline-none focus:border-[#2F7D4A] resize-none"
            />

        </div>


        {/* LOCATION */}
        <div className="mt-8">

          <label className="text-sm font-semibold">
            Location
          </label>

            <button
              onClick={() =>
                navigator.geolocation.getCurrentPosition(
                  (pos) =>
                    setLocation(`${pos.coords.latitude}, ${pos.coords.longitude}`),
                  () => setLocation("Please allow location access in your browser.")
                )
              }

              className="mt-3 w-full flex items-center justify-between p-4 rounded-2xl border border-[#DDE5DE] bg-white hover:bg-[#F3F7F3] transition"
            >
            <div className="flex items-center gap-3">

              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                <MapPin className="w-5 h-5 text-[#2F7D4A]" />
              </div>

              <div className="text-left">

                <p className="text-sm">
                  Add your location
                </p>

                <p className="text-xs text-[#68736B] mt-1">
                  {location || "Location helps response teams find the incident."}
                </p>

              </div>

            </div>

            <span className="text-xs text-[#2F7D4A]">
              Detect location
            </span>
          </button>

        </div>


        {/* SUBMIT */}
        <div className="mt-10 flex justify-end">

          <button
            onClick={handleSubmit}
            className="flex items-center gap-3 px-7 py-3.5 rounded-xl bg-[#2F7D4A] text-white font-semibold hover:bg-[#25663C] transition"
          >

            Analyze Report

            <ArrowLeft className="w-4 h-4 rotate-180" />

          </button>

        </div>

      </main>

    </div>
  );
}

export default ReportIncident;