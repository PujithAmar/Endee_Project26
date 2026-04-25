import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Trash2, MessageSquare, ArrowUpRight } from "lucide-react";
import { getHistory, deleteHistoryItem } from "@/lib/api";

export default function History() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const data = await getHistory();
      setItems(data);
    } catch (e) {
      toast.error("Failed to load history");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const onDelete = async (id) => {
    try {
      await deleteHistoryItem(id);
      toast.success("Deleted");
      setItems((arr) => arr.filter((x) => x.id !== id));
    } catch {
      toast.error("Delete failed");
    }
  };

  const colorFor = (s) =>
    s >= 75 ? "var(--ok)" : s >= 50 ? "var(--teal-bright)" : s >= 30 ? "var(--warn)" : "var(--danger)";

  return (
    <main className="max-w-5xl mx-auto px-6 py-12" data-testid="history-page">
      <div className="flex items-end justify-between mb-10 fade-up">
        <div>
          <div className="text-xs uppercase tracking-[0.2em]" style={{ color: "var(--text-muted)" }}>
            Saved analyses
          </div>
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight mt-1">
            Your <span className="serif">history</span>
          </h1>
        </div>
        <Link to="/" className="btn-ghost text-sm">New analysis →</Link>
      </div>

      {loading && <div className="card p-6 animate-pulse h-32" />}
      {!loading && items.length === 0 && (
        <div className="card p-10 text-center" data-testid="history-empty">
          <div className="serif text-xl mb-2" style={{ color: "var(--text-dim)" }}>
            "Nothing here yet."
          </div>
          <p className="text-sm mb-5" style={{ color: "var(--text-muted)" }}>
            Run your first resume × job analysis.
          </p>
          <Link to="/" className="btn-primary text-sm inline-flex">Start analysing</Link>
        </div>
      )}

      <div className="space-y-3">
        {items.map((it, i) => (
          <div
            key={it.id}
            className="card p-5 flex items-center gap-5 fade-up"
            style={{ animationDelay: `${i * 0.03}s` }}
            data-testid={`history-item-${i}`}
          >
            <div
              className="mono text-2xl font-semibold shrink-0 w-16 text-center"
              style={{ color: colorFor(it.match_score) }}
              data-testid={`history-score-${i}`}
            >
              {it.match_score}
              <div className="text-[10px] tracking-[0.2em] uppercase" style={{ color: "var(--text-muted)" }}>
                match
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{it.candidate_title}</div>
              <div className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
                → {it.jd_title}
              </div>
              {it.fit_summary && (
                <div className="text-xs mt-1.5 leading-relaxed line-clamp-2" style={{ color: "var(--text-dim)" }}>
                  {it.fit_summary}
                </div>
              )}
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <Link
                to={`/chat/${it.session_id}`}
                className="p-2 rounded-full hover:bg-white/5 transition"
                title="Chat about this"
                data-testid={`history-chat-${i}`}
              >
                <MessageSquare size={16} style={{ color: "var(--text-dim)" }} />
              </Link>
              <Link
                to={`/history/${it.id}`}
                className="p-2 rounded-full hover:bg-white/5 transition"
                title="Open"
                data-testid={`history-open-${i}`}
              >
                <ArrowUpRight size={16} style={{ color: "var(--text-dim)" }} />
              </Link>
              <button
                onClick={() => onDelete(it.id)}
                className="p-2 rounded-full hover:bg-white/5 transition"
                title="Delete"
                data-testid={`history-delete-${i}`}
              >
                <Trash2 size={16} style={{ color: "var(--text-muted)" }} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
