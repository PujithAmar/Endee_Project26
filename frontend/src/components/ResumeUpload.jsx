import { useCallback, useState } from "react";
import { FileText, Upload, X } from "lucide-react";

export default function ResumeUpload({ file, onFile, onText, text }) {
  const [drag, setDrag] = useState(false);
  const [mode, setMode] = useState("upload"); // upload | paste

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDrag(false);
      const f = e.dataTransfer.files?.[0];
      if (f && f.type === "application/pdf") onFile(f);
    },
    [onFile]
  );

  return (
    <div className="card p-6 fade-up" data-testid="resume-upload-card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FileText size={16} style={{ color: "var(--teal-bright)" }} />
          <h3 className="font-medium tracking-tight">Your Resume</h3>
        </div>
        <div className="flex items-center gap-1 text-xs">
          <button
            data-testid="mode-upload-btn"
            onClick={() => setMode("upload")}
            className={`px-3 py-1.5 rounded-full transition ${
              mode === "upload" ? "bg-[rgba(0,173,181,0.1)] text-white border border-[rgba(0,173,181,0.35)]" : "text-[color:var(--text-dim)] hover:text-white"
            }`}
          >
            Upload PDF
          </button>
          <button
            data-testid="mode-paste-btn"
            onClick={() => setMode("paste")}
            className={`px-3 py-1.5 rounded-full transition ${
              mode === "paste" ? "bg-[rgba(0,173,181,0.1)] text-white border border-[rgba(0,173,181,0.35)]" : "text-[color:var(--text-dim)] hover:text-white"
            }`}
          >
            Paste text
          </button>
        </div>
      </div>

      {mode === "upload" ? (
        file ? (
          <div
            className="flex items-center justify-between p-4 rounded-xl border border-[color:var(--line-2)]"
            style={{ background: "rgba(0,173,181,0.04)" }}
            data-testid="resume-file-chip"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                style={{ background: "rgba(0,173,181,0.1)", border: "1px solid rgba(0,173,181,0.35)" }}>
                <FileText size={18} style={{ color: "var(--teal-bright)" }} />
              </div>
              <div>
                <div className="text-sm font-medium">{file.name}</div>
                <div className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {(file.size / 1024).toFixed(1)} KB · PDF
                </div>
              </div>
            </div>
            <button
              data-testid="clear-file-btn"
              onClick={() => onFile(null)}
              className="p-2 rounded-full hover:bg-white/5 transition"
            >
              <X size={16} style={{ color: "var(--text-dim)" }} />
            </button>
          </div>
        ) : (
          <label
            htmlFor="resume-input"
            data-testid="resume-dropzone"
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={onDrop}
            className={`dropzone ${drag ? "drag" : ""} block cursor-pointer p-10 text-center`}
          >
            <input
              id="resume-input"
              data-testid="resume-file-input"
              type="file"
              accept="application/pdf"
              className="hidden"
              onChange={(e) => onFile(e.target.files?.[0] || null)}
            />
            <div className="w-12 h-12 mx-auto mb-4 rounded-full flex items-center justify-center"
              style={{ background: "rgba(0,173,181,0.08)", border: "1px solid rgba(0,173,181,0.25)" }}>
              <Upload size={20} style={{ color: "var(--teal-bright)" }} />
            </div>
            <div className="text-sm font-medium">Drop your resume PDF here</div>
            <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
              or click to browse · max 5 MB
            </div>
          </label>
        )
      ) : (
        <textarea
          data-testid="resume-text-input"
          value={text}
          onChange={(e) => onText(e.target.value)}
          placeholder="Paste your resume text here…"
          className="w-full h-60 resize-none bg-[rgba(255,255,255,0.02)] border border-[color:var(--line-2)] rounded-xl p-4 text-sm leading-relaxed focus:outline-none focus:border-[color:var(--teal)] transition"
          style={{ color: "var(--text)" }}
        />
      )}
    </div>
  );
}
