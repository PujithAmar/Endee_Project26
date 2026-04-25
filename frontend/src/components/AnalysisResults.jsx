import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ScoreRing from "./ScoreRing";
import {
  AlertTriangle, Lightbulb, Target, BookOpen, Sparkles, Check,
  MessageSquare, TrendingUp,
} from "lucide-react";

const priorityStyle = (p) => ({
  high: "chip danger",
  medium: "chip warn",
  low: "chip",
}[p || "medium"] || "chip");

export default function AnalysisResults({ result }) {
  const navigate = useNavigate();
  const [tab, setTab] = useState("technical");

  if (!result) return null;
  const r = result;
  const iq = r.interview_questions || { technical: [], hr: [] };

  return (
    <div className="space-y-6 fade-up">
      {/* Headline score */}
      <div className="card p-8 relative overflow-hidden" data-testid="results-score-card">
        <div
          className="absolute -top-20 -right-20 w-80 h-80 rounded-full opacity-20 blur-3xl"
          style={{ background: "radial-gradient(circle, #00ADB5, transparent 70%)" }}
        />
        <div className="relative flex flex-col md:flex-row items-center gap-8">
          <ScoreRing score={r.match_score || 0} />
          <div className="flex-1">
            <div className="text-xs uppercase tracking-[0.2em] mb-2" style={{ color: "var(--text-muted)" }}>
              Result
            </div>
            <h2 className="text-2xl md:text-3xl font-semibold tracking-tight leading-tight">
              {r.match_score >= 75
                ? "Strong fit"
                : r.match_score >= 50
                ? "Promising fit with gaps"
                : r.match_score >= 30
                ? "Significant gaps to close"
                : "Low fit — major alignment needed"}
            </h2>
            <p className="serif text-lg mt-3 leading-snug" style={{ color: "var(--text-dim)" }}>
              "{r.fit_summary || r.score_reason || "Your analysis is ready."}"
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              {(r.matched_skills || []).slice(0, 8).map((s, i) => (
                <span key={i} className="chip ok" data-testid={`matched-skill-${i}`}>
                  <Check size={12} /> {s}
                </span>
              ))}
            </div>
            {r.session_id && (
              <button
                data-testid="open-chat-btn"
                onClick={() => navigate(`/chat/${r.session_id}`)}
                className="mt-6 btn-ghost text-sm inline-flex items-center gap-2"
              >
                <MessageSquare size={14} /> Ask anything about my profile
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Missing Skills */}
        <Section
          title="Missing Skills"
          icon={<AlertTriangle size={16} style={{ color: "var(--warn)" }} />}
          testid="missing-skills"
        >
          {(r.missing_skills || []).length === 0 ? (
            <Empty text="No critical gaps detected." />
          ) : (
            <div className="flex flex-wrap gap-2">
              {(r.missing_skills || []).map((s, i) => (
                <span key={i} className="chip danger" data-testid={`missing-skill-${i}`}>
                  {s}
                </span>
              ))}
            </div>
          )}
        </Section>

        {/* Strengths */}
        <Section
          title="Resume Strengths"
          icon={<TrendingUp size={16} style={{ color: "var(--ok)" }} />}
          testid="resume-strengths"
        >
          <ul className="space-y-2">
            {(r.resume_strengths || []).map((s, i) => (
              <li key={i} className="flex gap-2 text-sm leading-relaxed" data-testid={`strength-${i}`}>
                <span className="mt-1.5 inline-block w-1.5 h-1.5 rounded-full shrink-0"
                  style={{ background: "var(--ok)" }} />
                <span style={{ color: "var(--text-dim)" }}>{s}</span>
              </li>
            ))}
            {!(r.resume_strengths || []).length && <Empty text="No strengths extracted." />}
          </ul>
        </Section>

        {/* Suggestions */}
        <Section
          title="Suggestions"
          icon={<Lightbulb size={16} style={{ color: "var(--teal-bright)" }} />}
          testid="suggestions"
          wide
        >
          <ul className="space-y-3">
            {(r.suggestions || []).map((s, i) => (
              <li key={i} className="flex gap-3 text-sm leading-relaxed" data-testid={`suggestion-${i}`}>
                <span
                  className="mono text-xs rounded-md px-2 py-1 shrink-0 h-fit"
                  style={{ background: "rgba(0,173,181,0.08)", color: "var(--teal-bright)", border: "1px solid rgba(0,173,181,0.3)" }}
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span style={{ color: "var(--text)" }}>{s}</span>
              </li>
            ))}
            {!(r.suggestions || []).length && <Empty text="No suggestions." />}
          </ul>
        </Section>

        {/* Learning path */}
        <Section
          title="Learning Path"
          icon={<BookOpen size={16} style={{ color: "var(--teal-bright)" }} />}
          testid="learning-path"
          wide
        >
          <div className="space-y-3">
            {(r.learning_path || []).map((p, i) => (
              <div
                key={i}
                className="p-3 rounded-lg border border-[color:var(--line)] flex items-start justify-between gap-4"
                style={{ background: "rgba(255,255,255,0.015)" }}
                data-testid={`learning-item-${i}`}
              >
                <div>
                  <div className="text-sm font-medium">{p.skill}</div>
                  <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                    {p.resource}
                  </div>
                </div>
                <span className={priorityStyle(p.priority)}>{p.priority || "medium"}</span>
              </div>
            ))}
            {!(r.learning_path || []).length && <Empty text="No learning items." />}
          </div>
        </Section>
      </div>

      {/* Interview Questions */}
      <div className="card p-6" data-testid="interview-questions">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <Target size={16} style={{ color: "var(--teal-bright)" }} />
            <h3 className="font-medium tracking-tight">Interview Questions</h3>
          </div>
          <div className="flex items-center gap-1 text-xs">
            <TabBtn active={tab === "technical"} onClick={() => setTab("technical")} testid="iq-tab-tech">
              Technical <span className="mono opacity-60 ml-1">{(iq.technical || []).length}</span>
            </TabBtn>
            <TabBtn active={tab === "hr"} onClick={() => setTab("hr")} testid="iq-tab-hr">
              HR <span className="mono opacity-60 ml-1">{(iq.hr || []).length}</span>
            </TabBtn>
          </div>
        </div>

        <ol className="space-y-3">
          {(iq[tab] || []).map((q, i) => (
            <li
              key={i}
              className="flex gap-4 text-sm leading-relaxed"
              data-testid={`iq-${tab}-${i}`}
            >
              <span
                className="mono shrink-0 rounded-md px-2 py-1 h-fit text-xs"
                style={{ background: "rgba(255,255,255,0.03)", color: "var(--teal-bright)", border: "1px solid var(--line-2)" }}
              >
                Q{String(i + 1).padStart(2, "0")}
              </span>
              <span style={{ color: "var(--text)" }}>{q}</span>
            </li>
          ))}
          {!(iq[tab] || []).length && <Empty text="No questions for this tab." />}
        </ol>
      </div>

      {/* Extracted skills footer */}
      {(r.extracted_skills || []).length > 0 && (
        <div className="card p-6" data-testid="extracted-skills">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles size={14} style={{ color: "var(--teal-bright)" }} />
            <h3 className="font-medium tracking-tight text-sm">All Skills Detected in Your Resume</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {r.extracted_skills.map((s, i) => (
              <span key={i} className="chip" data-testid={`extracted-skill-${i}`}>{s}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Section({ title, icon, testid, wide, children }) {
  return (
    <div className={`card p-6 ${wide ? "md:col-span-2" : ""}`} data-testid={`section-${testid}`}>
      <div className="flex items-center gap-2 mb-4">
        {icon}
        <h3 className="font-medium tracking-tight text-[15px]">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function TabBtn({ active, onClick, testid, children }) {
  return (
    <button
      data-testid={testid}
      onClick={onClick}
      className={`px-3 py-1.5 rounded-full transition ${
        active
          ? "bg-[rgba(0,173,181,0.1)] text-white border border-[rgba(0,173,181,0.35)]"
          : "text-[color:var(--text-dim)] hover:text-white"
      }`}
    >
      {children}
    </button>
  );
}

function Empty({ text }) {
  return <div className="text-sm italic" style={{ color: "var(--text-muted)" }}>{text}</div>;
}
