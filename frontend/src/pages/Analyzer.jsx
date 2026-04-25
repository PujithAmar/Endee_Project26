import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowRight, Sparkles, Wand2, Loader2 } from "lucide-react";
import ResumeUpload from "@/components/ResumeUpload";
import JobDescriptionInput from "@/components/JobDescriptionInput";
import AnalysisResults from "@/components/AnalysisResults";
import { analyzeFile, getHistoryItem } from "@/lib/api";

const steps = [
  "Parsing your resume…",
  "Chunking & embedding (MiniLM-L6-v2)…",
  "Indexing in Endee vector DB…",
  "Retrieving top-K relevant context…",
  "Asking Gemini 3 for analysis…",
];

export default function Analyzer() {
  const { id } = useParams();
  const [file, setFile] = useState(null);
  const [resumeText, setResumeText] = useState("");
  const [jd, setJd] = useState("");
  const [loading, setLoading] = useState(false);
  const [stepIdx, setStepIdx] = useState(0);
  const [result, setResult] = useState(null);

  // Load history item if ?id
  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const doc = await getHistoryItem(id);
        setResumeText(doc.resume_text || "");
        setJd(doc.jd_text || "");
        setResult({ ...doc.result, session_id: doc.session_id });
      } catch (e) {
        toast.error("Failed to load history item");
      }
    })();
  }, [id]);

  // Rotate "step" messages while loading
  useEffect(() => {
    if (!loading) return;
    setStepIdx(0);
    const t = setInterval(() => setStepIdx((s) => (s + 1) % steps.length), 2200);
    return () => clearInterval(t);
  }, [loading]);

  const canAnalyze = (file || resumeText.trim().length > 50) && jd.trim().length > 40;

  const onAnalyze = async () => {
    if (!canAnalyze) {
      toast.error("Add a resume (PDF or text) and a job description (≥40 chars)");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeFile({
        resumeFile: file || undefined,
        resumeText: file ? undefined : resumeText,
        jdText: jd,
      });
      setResult(data);
      toast.success(`Analysis complete · ${data.match_score}% match`);
      // scroll results into view
      setTimeout(() => {
        document.getElementById("results-anchor")?.scrollIntoView({ behavior: "smooth" });
      }, 80);
    } catch (e) {
      console.error(e);
      toast.error(e?.response?.data?.detail || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="max-w-7xl mx-auto px-6 py-10 md:py-14">
      {/* Hero */}
      <div className="max-w-3xl fade-up">
        <div className="inline-flex items-center gap-2 chip teal mb-5">
          <Sparkles size={12} /> RAG · Endee · Gemini 3
        </div>
        <h1 className="text-4xl md:text-6xl font-semibold tracking-[-0.03em] leading-[1.02]">
          Land roles you <span className="serif">actually</span> fit<br />
          <span style={{ color: "var(--teal-bright)" }}>
            with retrieval-grounded
          </span>{" "}
          placement intel<span className="caret" />
        </h1>
        <p className="mt-5 text-[15px] md:text-base leading-relaxed max-w-xl" style={{ color: "var(--text-dim)" }}>
          SkillBridge analyses your resume against any job description using a
          custom RAG pipeline — then hands you a score, missing skills, a rewrite
          plan, and interview questions tailored to that exact role.
        </p>
      </div>

      {/* Input grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-12">
        <ResumeUpload
          file={file}
          onFile={setFile}
          text={resumeText}
          onText={setResumeText}
        />
        <JobDescriptionInput value={jd} onChange={setJd} />
      </div>

      {/* Analyze CTA */}
      <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4 fade-up" style={{ animationDelay: ".12s" }}>
        <button
          data-testid="analyze-btn"
          disabled={!canAnalyze || loading}
          onClick={onAnalyze}
          className="btn-primary inline-flex items-center gap-2 text-base"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Analyzing…
            </>
          ) : (
            <>
              <Wand2 size={18} strokeWidth={2.2} />
              Analyze
              <ArrowRight size={18} />
            </>
          )}
        </button>
        <div className="text-xs mono flex items-center gap-2" style={{ color: "var(--text-muted)" }}>
          <span className="inline-block w-1.5 h-1.5 rounded-full pulse-dot" style={{ background: "var(--teal-bright)" }} />
          {loading ? steps[stepIdx] : "Ready when you are"}
        </div>
      </div>

      <div className="divider my-14" />

      <div id="results-anchor" />
      {loading && <Skeleton />}
      {!loading && result && <AnalysisResults result={result} />}

      {!loading && !result && (
        <FeatureStrip />
      )}
    </main>
  );
}

function Skeleton() {
  return (
    <div className="space-y-6">
      <div className="card p-8 h-64 animate-pulse" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6 h-40 animate-pulse" />
        <div className="card p-6 h-40 animate-pulse" />
        <div className="card p-6 h-48 md:col-span-2 animate-pulse" />
      </div>
    </div>
  );
}

function FeatureStrip() {
  const items = [
    { n: "01", t: "Chunk + Embed", d: "Your docs split into 300-token chunks, encoded with all-MiniLM-L6-v2." },
    { n: "02", t: "Endee Vector Store", d: "384-dim vectors indexed with HNSW + cosine in Endee Serverless." },
    { n: "03", t: "Retrieve", d: "Top-K JD↔resume chunks retrieved for cross-grounded context." },
    { n: "04", t: "Gemini 3", d: "Grounded prompt → match score, gaps, suggestions, interview Qs." },
  ];
  return (
    <div className="mt-4">
      <div className="text-xs uppercase tracking-[0.2em] mb-6" style={{ color: "var(--text-muted)" }}>
        under the hood
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {items.map((it, i) => (
          <div key={i} className="fade-up" style={{ animationDelay: `${0.05 * i}s` }}>
            <div className="mono text-sm" style={{ color: "var(--teal-bright)" }}>{it.n}</div>
            <div className="mt-2 font-medium tracking-tight">{it.t}</div>
            <div className="mt-1 text-sm leading-relaxed" style={{ color: "var(--text-dim)" }}>{it.d}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
