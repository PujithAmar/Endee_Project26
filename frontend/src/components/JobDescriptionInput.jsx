import { Briefcase } from "lucide-react";

const SAMPLE = `Senior Backend Engineer
Company: Acme Cloud
Location: Remote

We are looking for a Senior Backend Engineer with 5+ years experience designing
distributed systems. You will own microservices on AWS, lead system design reviews,
and mentor engineers.

Requirements:
- Strong Python (FastAPI / Django) OR Go
- Deep experience with PostgreSQL and Redis
- Docker, Kubernetes, CI/CD (GitHub Actions)
- Event-driven architectures (Kafka / RabbitMQ)
- System design, scalability, observability (Prometheus, Grafana)
- Excellent written communication

Nice to have: Terraform, gRPC, ML pipelines.`;

export default function JobDescriptionInput({ value, onChange }) {
  return (
    <div className="card p-6 fade-up" data-testid="jd-card" style={{ animationDelay: ".05s" }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Briefcase size={16} style={{ color: "var(--teal-bright)" }} />
          <h3 className="font-medium tracking-tight">Job Description</h3>
        </div>
        <button
          data-testid="sample-jd-btn"
          onClick={() => onChange(SAMPLE)}
          className="text-xs px-3 py-1.5 rounded-full text-[color:var(--text-dim)] hover:text-white transition"
        >
          Use sample
        </button>
      </div>
      <textarea
        data-testid="jd-text-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Paste the job description you're targeting…"
        className="w-full h-[350px] resize-none bg-[rgba(255,255,255,0.02)] border border-[color:var(--line-2)] rounded-xl p-4 text-sm leading-relaxed focus:outline-none focus:border-[color:var(--teal)] transition"
        style={{ color: "var(--text)" }}
      />
      <div className="mt-3 text-xs flex items-center gap-3" style={{ color: "var(--text-muted)" }}>
        <span className="mono">{value.length.toLocaleString()} chars</span>
        <span>·</span>
        <span>Tip: include requirements + nice-to-haves for better analysis</span>
      </div>
    </div>
  );
}
