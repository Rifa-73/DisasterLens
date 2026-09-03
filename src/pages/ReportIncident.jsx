import Navbar from "../components/Navbar";
import {
  ArrowLeft,
  Camera,
  Video,
  Mic,
  MapPin,
  Upload,
  X,
  CheckCircle,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

function ReportIncident() {
  const navigate = useNavigate();

  const [images, setImages] = useState([]);
  const [location, setLocation] = useState(null);
  const [video, setVideo] = useState(null);
  const [audio, setAudio] = useState(null);
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(null);

  const handleImages = (e) => {
    const selected = Array.from(e.target.files || []);
    setImages((prev) => [...prev, ...selected]);
    e.target.value = "";
  };

  const removeImage = (index) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
  };

  const detectLocation = () => {
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        setLocation(`${pos.coords.latitude}, ${pos.coords.longitude}`),
      () => setLocation("Please allow location access in your browser.")
    );
  };

  const handleSubmit = async () => {
    if (!images.length || !location || !location.includes(",")) {
      alert("Please upload an image and detect your location.");
      return;
    }

    setLoading(true);

    const [latitude, longitude] = location.split(",").map(Number);
    const formData = new FormData();

    formData.append("latitude", latitude);
    formData.append("longitude", longitude);
    formData.append("description", description);
    formData.append("file", images[0]);

    if (video) formData.append("video", video);
    if (audio) formData.append("audio", audio);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/incidents/report",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) throw new Error("Report submission failed.");

      const result = await response.json();

      const reader = new FileReader();

      reader.onload = () => {
        localStorage.setItem(
          "rnrReport",
          JSON.stringify({
            description,
            location,
            evidence: {
              image: reader.result,
              imageName: images[0].name,
              video: video?.name || null,
              audio: audio?.name || null,
            },
            status: "AWAITING_VERIFICATION",
            aiAssessment: result.ai_assessment,
            cvAssessment: result.severity,
            incidentId: result.id,
          })
        );

        setSubmitted(result.id);
      };

      reader.readAsDataURL(images[0]);
    } catch (error) {
      console.error(error);
      alert("Could not analyze the report.");
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-[#F7F8F5] text-[#17201A]">
        <Navbar />

        <main className="max-w-2xl mx-auto px-6 py-24 text-center">
          <CheckCircle className="w-16 h-16 text-[#2F7D4A] mx-auto" />

          <h1 className="text-3xl font-bold mt-6">
            Report Submitted Successfully
          </h1>

          <p className="text-[#68736B] mt-3">
            Your incident has been received and is being assessed.
          </p>

          <p className="text-sm text-[#68736B] mt-4">
            Incident ID: <b>#{submitted}</b>
          </p>

          <div className="flex justify-center gap-4 mt-8">
            <button
              onClick={() => navigate("/incident")}
              className="px-6 py-3 rounded-xl border border-[#DDE5DE] bg-white"
            >
              View Incident
            </button>

            <button
              onClick={() => navigate("/dashboard")}
              className="px-6 py-3 rounded-xl bg-[#2F7D4A] text-white font-semibold"
            >
              Go to Dashboard
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F7F8F5] text-[#17201A]">
      <Navbar />

      <main className="max-w-5xl mx-auto px-6 py-12">

        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-sm text-[#68736B] hover:text-[#2F7D4A] mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to home
        </button>

        <div className="max-w-2xl">
          <p className="text-xs tracking-[0.2em] text-[#68736B]">
            REPORT AN INCIDENT
          </p>

          <h1 className="text-4xl md:text-5xl font-bold mt-3">
            What did you observe?
          </h1>

          <p className="text-[#68736B] mt-4 leading-relaxed">
            Share whatever evidence you have. Images, videos, audio,
            and your description can help us understand the situation.
          </p>
        </div>

        {/* EVIDENCE */}
        <div className="mt-10">
          <h2 className="text-lg font-semibold">Add evidence</h2>

          <p className="text-sm text-[#68736B] mt-1">
            You can provide one or multiple types of evidence.
          </p>

          <div className="grid md:grid-cols-3 gap-4 mt-5">

            {/* IMAGES */}
            <label className="group p-6 rounded-2xl border border-[#DDE5DE] bg-white hover:border-[#2F7D4A] transition cursor-pointer">
              <Camera className="w-6 h-6 text-[#2F7D4A]" />

              <h3 className="font-semibold mt-5">Upload Images</h3>

              <p className="text-sm text-[#68736B] mt-2">
                Upload one or multiple photos of the incident.
              </p>

              <div className="flex items-center gap-2 text-xs text-[#2F7D4A] mt-5">
                <Upload className="w-3.5 h-3.5" />
                Choose images
              </div>

              <input
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={handleImages}
              />
            </label>

            {/* VIDEO */}
            <label className="group p-6 rounded-2xl border border-[#DDE5DE] bg-white hover:border-[#2F7D4A] transition cursor-pointer">
              <Video className="w-6 h-6 text-[#2F7D4A]" />

              <h3 className="font-semibold mt-5">Upload Video</h3>

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
                  {video.name}
                </p>
              )}
            </label>

            {/* AUDIO */}
            <label className="group p-6 rounded-2xl border border-[#DDE5DE] bg-white hover:border-[#2F7D4A] transition cursor-pointer">
              <Mic className="w-6 h-6 text-[#2F7D4A]" />

              <h3 className="font-semibold mt-5">Upload Audio</h3>

              <p className="text-sm text-[#68736B] mt-2">
                Voice recordings describing the emergency.
              </p>

              <div className="flex items-center gap-2 text-xs text-[#2F7D4A] mt-5">
                <Upload className="w-3.5 h-3.5" />
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
                  {audio.name}
                </p>
              )}
            </label>
          </div>

          {/* IMAGE PREVIEWS */}
          {images.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
              {images.map((img, index) => (
                <div
                  key={`${img.name}-${index}`}
                  className="relative rounded-xl overflow-hidden border border-[#DDE5DE] bg-white"
                >
                  <img
                    src={URL.createObjectURL(img)}
                    alt={`Evidence ${index + 1}`}
                    className="w-full h-36 object-cover"
                  />

                  <button
                    type="button"
                    onClick={() => removeImage(index)}
                    className="absolute top-2 right-2 p-1.5 rounded-full bg-white shadow"
                  >
                    <X className="w-4 h-4" />
                  </button>

                  <p className="text-xs p-2 truncate">
                    {img.name}
                  </p>
                </div>
              ))}
            </div>
          )}
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
            className="w-full h-32 mt-3 rounded-2xl border border-[#DDE5DE] bg-white p-4 text-sm outline-none focus:border-[#2F7D4A] resize-none"
          />
        </div>

        {/* LOCATION */}
        <div className="mt-8">
          <label className="text-sm font-semibold">Location</label>

          <button
            onClick={detectLocation}
            className="mt-3 w-full flex items-center justify-between p-4 rounded-2xl border border-[#DDE5DE] bg-white hover:bg-[#F3F7F3] transition"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                <MapPin className="w-5 h-5 text-[#2F7D4A]" />
              </div>

              <div className="text-left">
                <p className="text-sm">Add your location</p>

                <p className="text-xs text-[#68736B] mt-1">
                  {location ||
                    "Location helps response teams find the incident."}
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
            disabled={loading}
            className="flex items-center gap-3 px-7 py-3.5 rounded-xl bg-[#2F7D4A] text-white font-semibold hover:bg-[#25663C] disabled:opacity-60"
          >
            {loading ? "Analyzing..." : "Analyze Report"}

            {!loading && (
              <ArrowLeft className="w-4 h-4 rotate-180" />
            )}
          </button>
        </div>
      </main>
    </div>
  );
}

export default ReportIncident;