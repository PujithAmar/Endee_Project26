import { useEffect, useState } from "react";

export default function ScoreRing({ score = 0, size = 220, stroke = 14 }) {
  const [display, setDisplay] = useState(0);
  const radius = (size - stroke) / 2;
  const c = 2 * Math.PI * radius;
  const offset = c - (display / 100) * c;

  useEffect(() => {
    let raf;
    const start = performance.now();
    const from = 0;
    const to = Math.max(0, Math.min(100, score));
    const dur = 900;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / dur);
      const e = 1 - Math.pow(1 - p, 3);
      setDisplay(Math.round(from + (to - from) * e));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [score]);

  const colorFor = (s) => {
    if (s >= 75) return "var(--ok)";
    if (s >= 50) return "var(--teal-bright)";
    if (s >= 30) return "var(--warn)";
    return "var(--danger)";
  };

  return (
    <div className="relative inline-block" data-testid="match-score-ring">
      <svg width={size} height={size}>
        <defs>
          <linearGradient id="tealGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#1EE5EE" />
            <stop offset="100%" stopColor="#00ADB5" />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          className="ring-track"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          strokeDasharray={c}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          className="ring-progress"
        />
      </svg>
      <div
        className="absolute inset-0 flex flex-col items-center justify-center"
        style={{ pointerEvents: "none" }}
      >
        <div
          className="mono font-semibold"
          data-testid="match-score-value"
          style={{ fontSize: size * 0.28, color: colorFor(display), lineHeight: 1 }}
        >
          {display}
        </div>
        <div className="text-xs uppercase tracking-[0.2em]" style={{ color: "var(--text-muted)" }}>
          Match Score
        </div>
      </div>
    </div>
  );
}
