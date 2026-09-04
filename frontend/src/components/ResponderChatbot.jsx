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

  const ai = report?.aiAssessment;
  const cv = report?.cvAssessment;


  const sendMessage = async (text = message) => {
    if (!text.trim()) return;
  
    setMessages((m) => [...m, { type: "user", text }]);
    setMessage("");
  
    try {
      const res = await fetch("http://localhost:8000/incidents/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: text,
          incident: {
            description: report?.description,
            ai_assessment: report?.aiAssessment,
            cvdl: report?.cvAssessment,
            location: report?.location,
            evidence: report?.evidence, 
          },
        }),
      });
  
      const data = await res.json();
  
      setMessages((m) => [...m, { type: "bot", text: data.answer }]);
    } catch {
      setMessages((m) => [
        ...m,
        { type: "bot", text: "Unable to connect to the AI assistant." },
      ]);
    }
  };
  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-[2000] w-14 h-14 rounded-full bg-[#2F7D4A] text-white shadow-lg flex items-center justify-center hover:bg-[#25663C] transition"
        >
          <Bot className="w-6 h-6" />
        </button>
      )}

      {open && (
        <div className="fixed bottom-6 right-6 z-[2000] w-80 md:w-96 bg-white border border-[#DDE5DE] rounded-2xl shadow-xl overflow-hidden">
          <div className="flex justify-between items-center px-5 py-4 bg-[#2F7D4A] text-white">
            <div className="flex items-center gap-3">
              <Bot className="w-5" />
              <div>
                <p className="font-semibold text-sm">Responder Assistant</p>
                <p className="text-xs text-white/80">Incident support</p>
              </div>
            </div>
            <button onClick={() => setOpen(false)}>
              <X className="w-5" />
            </button>
          </div>

          <div className="h-72 overflow-y-auto p-4 bg-[#F7F8F5]">
            {!messages.length && (
              <>
                <div className="p-3 rounded-xl bg-white border border-[#DDE5DE] text-sm">
                  <p className="font-medium">Hello 👋</p>
                  <p className="text-[#68736B] mt-1">
                    I can help you understand this incident.
                  </p>
                </div>

                <div className="flex flex-wrap gap-2 mt-4">
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      onClick={() => sendMessage(s)}
                      className="px-3 py-2 rounded-lg bg-white border border-[#DDE5DE] text-xs text-[#2F7D4A] hover:bg-[#EAF4EC]"
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
                className={`mb-3 p-3 rounded-xl text-sm ${
                  m.type === "user"
                    ? "ml-8 bg-[#2F7D4A] text-white"
                    : "mr-8 bg-white border border-[#DDE5DE]"
                }`}
              >
                {m.text}
              </div>
            ))}
          </div>

          <div className="p-3 border-t border-[#DDE5DE] flex gap-2">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Ask about this incident..."
              className="flex-1 px-3 py-2 rounded-lg border border-[#DDE5DE] text-sm outline-none focus:border-[#2F7D4A]"
            />
            <button
              onClick={() => sendMessage()}
              className="w-10 rounded-lg bg-[#2F7D4A] text-white flex items-center justify-center"
            >
              <Send className="w-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default ResponderChatbot;