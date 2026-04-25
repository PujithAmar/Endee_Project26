import { Link, useLocation } from "react-router-dom";
import { Sparkles, History as HistoryIcon, MessageSquare } from "lucide-react";

export default function Navbar() {
  const { pathname } = useLocation();
  const is = (p) => pathname === p || pathname.startsWith(p + "/");

  return (
    <nav
      data-testid="navbar"
      className="sticky top-0 z-40 backdrop-blur border-b border-[color:var(--line)] bg-[rgba(14,17,23,0.7)]"
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link
          to="/"
          data-testid="nav-logo"
          className="flex items-center gap-2.5 group"
        >
          <span className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: "linear-gradient(180deg,#1EE5EE,#00ADB5)" }}>
            <Sparkles size={16} color="#04121a" strokeWidth={2.5} />
          </span>
          <span className="font-semibold tracking-tight text-[17px]">
            Skill<span style={{ color: "var(--teal-bright)" }}>Bridge</span>
          </span>
          <span className="hidden md:inline serif text-xs ml-2" style={{ color: "var(--text-muted)" }}>
            · your placement co-pilot
          </span>
        </Link>

        <div className="flex items-center gap-1">
          <Link
            to="/"
            data-testid="nav-analyzer"
            className={`btn-ghost text-sm flex items-center gap-2 ${is("/") && !is("/history") && !is("/chat") ? "text-white border-[color:var(--teal)]" : ""}`}
          >
            <Sparkles size={14} /> Analyzer
          </Link>
          <Link
            to="/history"
            data-testid="nav-history"
            className={`btn-ghost text-sm flex items-center gap-2 ${is("/history") ? "text-white border-[color:var(--teal)]" : ""}`}
          >
            <HistoryIcon size={14} /> History
          </Link>
        </div>
      </div>
    </nav>
  );
}
