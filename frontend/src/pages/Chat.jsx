import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, Send, Sparkles, Loader2 } from "lucide-react";
import { sendChat, getChatHistory } from "@/lib/api";

const SUGGESTIONS = [
  "What skills am I missing for this role?",
  "How should I rewrite my resume summary?",
  "Am I a fit for this job overall?",
  "What projects should I build to stand out?",
];

export default function Chat() {
  const { sessionId } = useParams();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        const hist = await getChatHistory(sessionId);
        const msgs = [];
        for (const h of hist) {
          msgs.push({ role: "user", content: h.question });
          msgs.push({ role: "assistant", content: h.answer });
        }
        setMessages(msgs);
      } catch { /* empty */ }
    })();
  }, [sessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const ask = async (q) => {
    if (!q.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");
    setLoading(true);
    try {
      const { answer } = await sendChat(sessionId, q);
      setMessages((m) => [...m, { role: "assistant", content: answer }]);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Chat failed");
      setMessages((m) => [...m, { role: "assistant", content: "Sorry, I couldn't answer that." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="max-w-4xl mx-auto px-6 py-10 min-h-[calc(100vh-70px)] flex flex-col" data-testid="chat-page">
      <div className="flex items-center justify-between mb-6 fade-up">
        <Link to="/history" className="btn-ghost text-xs inline-flex items-center gap-2">
          <ArrowLeft size={14} /> Back to history
        </Link>
        <div className="text-xs mono" style={{ color: "var(--text-muted)" }}>
          session: {sessionId.slice(0, 10)}…
        </div>
      </div>

      <div className="mb-6 fade-up">
        <div className="inline-flex items-center gap-2 chip teal mb-3">
          <Sparkles size={12} /> Grounded chat
        </div>
        <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">
          Ask anything about your <span className="serif">profile</span>
        </h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-dim)" }}>
          Answers are retrieved from this session's resume + JD chunks.
        </p>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto card p-6 space-y-4 min-h-[320px]"
        data-testid="chat-messages"
      >
        {messages.length === 0 && !loading && (
          <div className="text-center py-10 fade-in">
            <div className="serif text-lg mb-4" style={{ color: "var(--text-dim)" }}>
              "What should I ask first?"
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => ask(s)}
                  className="chip hover:border-[color:var(--teal)] hover:text-white transition"
                  data-testid={`suggestion-${i}`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <Bubble key={i} msg={m} />
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
            <Loader2 size={14} className="animate-spin" /> thinking…
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
        className="mt-4 flex items-center gap-2"
        data-testid="chat-form"
      >
        <input
          data-testid="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your profile…"
          className="flex-1 bg-[rgba(255,255,255,0.02)] border border-[color:var(--line-2)] rounded-full px-5 py-3 text-sm focus:outline-none focus:border-[color:var(--teal)] transition"
          style={{ color: "var(--text)" }}
        />
        <button
          data-testid="chat-send"
          type="submit"
          disabled={!input.trim() || loading}
          className="btn-primary !px-5 !py-3"
        >
          <Send size={16} />
        </button>
      </form>
    </main>
  );
}

function Bubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} fade-in`}>
      <div
        className={`max-w-[85%] text-sm leading-relaxed rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-[rgba(0,173,181,0.1)] border border-[rgba(0,173,181,0.35)] text-white"
            : "bg-[rgba(255,255,255,0.03)] border border-[color:var(--line-2)] text-[color:var(--text)]"
        }`}
        style={{ whiteSpace: "pre-wrap" }}
      >
        {msg.content}
      </div>
    </div>
  );
}
