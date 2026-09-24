import { useState } from "react";
import { Bot, Send, X } from "lucide-react";

const suggestions = [
  "Summarize this incident",
  "Why is this priority?",
  "Explain CVDL analysis",
  "What evidence was submitted?",
];

function ResponderChatbot({ report }) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (text = message) => {
    if (!text.trim() || loading) return;

    setMessages((m) => [...m, { type: "user", text }]);
    setMessage("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/incidents/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: text,
          incident: {
            description: report?.description,
            location: report?.location,
            ai_assessment: report?.aiAssessment,
            cvdl: report?.cvAssessment,
            evidence: report?.evidence,
            evidence_assessment: report?.evidenceAssessment,
            human_verification_required:
              report?.evidenceAssessment?.human_verification_required ||
              report?.aiAssessment?.needs_human_verification,
          },
        }),
      });

      if (!res.ok) throw new Error("Chat request failed");

      const data = await res.json();

      setMessages((m) => [
        ...m,
        {
          type: "bot",
          text: data.answer || "No response received from the AI assistant.",
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        { type: "bot", text: "Unable to connect to the AI assistant." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-5 right-5 z-[2000] w-12 h-12 rounded-full bg-[#3F6546] text-white shadow-lg flex items-center justify-center"
        >
          <Bot className="w-5 h-5" />
        </button>
      )}

      {open && (
        <div className="fixed bottom-5 right-5 z-[2000] w-[330px] bg-white border border-[#DDE4DB] rounded-xl shadow-xl overflow-hidden">

          <div className="px-4 py-3 bg-[#3F6546] text-white flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4" />
              <div>
                <p className="font-semibold text-xs">Lena · Response Assistant</p>
                <p className="text-[9px] text-white/70">Online</p>
              </div>
            </div>

            <button onClick={() => setOpen(false)}>
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="h-64 overflow-y-auto p-3 bg-[#F7F8F5]">
            {!messages.length && (
              <>
                <div className="p-3 bg-white border border-[#E0E6DE] rounded-lg text-xs">
                  <p className="font-semibold">Hi 👋</p>
                  <p className="text-[#78827A] mt-1">
                    Ask me about this incident or how to respond.
                  </p>
                </div>

                <div className="flex flex-wrap gap-1.5 mt-3">
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      onClick={() => sendMessage(s)}
                      className="px-2 py-1.5 rounded-md bg-white border border-[#DDE4DB] text-[9px] text-[#426A4A]"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </>
            )}

            {messages.map((m, i) => (
              <div
                key={i}
                className={`mb-2 p-2.5 rounded-lg text-xs ${
                  m.type === "user"
                    ? "ml-8 bg-[#3F6546] text-white"
                    : "mr-8 bg-white border border-[#DDE4DB]"
                }`}
              >
                {m.text}
              </div>
            ))}

            {loading && (
              <div className="mr-8 p-2.5 rounded-lg bg-white border text-xs text-gray-500">
                Analyzing incident...
              </div>
            )}
          </div>

          <div className="p-2 border-t border-[#DDE4DB] flex gap-2">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Type a message..."
              className="flex-1 px-3 py-2 rounded-lg bg-[#F5F7F3] text-xs outline-none"
            />

            <button
              onClick={() => sendMessage()}
              disabled={loading}
              className="w-9 rounded-lg bg-[#3F6546] text-white flex items-center justify-center disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default ResponderChatbot;