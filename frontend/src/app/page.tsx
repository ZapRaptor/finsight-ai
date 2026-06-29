"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  TrendingUp,
  Zap,
  Brain,
  Database,
  Shield,
  ArrowRight,
  Loader2,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

const POPULAR_TICKERS = [
  { symbol: "AAPL", name: "Apple Inc." },
  { symbol: "MSFT", name: "Microsoft" },
  { symbol: "GOOGL", name: "Alphabet" },
  { symbol: "AMZN", name: "Amazon" },
  { symbol: "NVDA", name: "NVIDIA" },
  { symbol: "TSLA", name: "Tesla" },
  { symbol: "META", name: "Meta" },
  { symbol: "JPM", name: "JPMorgan" },
];

const FEATURES = [
  {
    icon: Brain,
    title: "Agentic AI Pipeline",
    desc: "6-node LangGraph state machine for structured analysis",
    color: "text-purple-400 bg-purple-500/10",
  },
  {
    icon: Database,
    title: "RAG-Enhanced",
    desc: "Qdrant vector search with semantic context retrieval",
    color: "text-blue-400 bg-blue-500/10",
  },
  {
    icon: Zap,
    title: "Real-Time Streaming",
    desc: "Token-by-token SSE streaming via Gemini 2.5 Flash",
    color: "text-amber-400 bg-amber-500/10",
  },
  {
    icon: Shield,
    title: "Institutional-Grade",
    desc: "SWOT analysis, Bull/Bear cases, and confidence scores",
    color: "text-emerald-400 bg-emerald-500/10",
  },
];

export default function DashboardPage() {
  const [ticker, setTicker] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleAnalyze = (symbol?: string) => {
    const target = (symbol || ticker).trim().toUpperCase();
    if (!target) return;
    setIsLoading(true);
    router.push(`/report/${target}`);
  };

  return (
    <div className="p-8">
      {/* Hero Section */}
      <div className="mb-10">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="h-4 w-4 text-emerald-500" />
          <span className="text-xs font-medium uppercase tracking-wider text-emerald-500">
            AI-Powered Research
          </span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Financial Research Dashboard
        </h1>
        <p className="mt-2 max-w-lg text-sm text-slate-500">
          Enter any ticker to generate an institutional-grade investment memo
          with AI-driven analysis, financial ratios, and interactive charts.
        </p>
      </div>

      {/* Search Bar */}
      <div className="mb-8">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAnalyze();
          }}
          className="flex gap-3"
        >
          <div className="relative flex-1 max-w-lg">
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="Enter ticker symbol (e.g., AAPL)"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] py-3.5 pl-11 pr-4 text-sm font-mono text-white placeholder-slate-600 outline-none transition-all focus:border-emerald-500/40 focus:ring-2 focus:ring-emerald-500/10"
            />
          </div>
          <button
            type="submit"
            disabled={!ticker.trim() || isLoading}
            className="flex items-center gap-2 rounded-xl bg-emerald-500 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/20 transition-all hover:bg-emerald-400 hover:shadow-emerald-500/30 disabled:opacity-40 disabled:shadow-none"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                Analyze
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </form>
      </div>

      {/* Popular Tickers */}
      <div className="mb-10">
        <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">
          Popular Tickers
        </h2>
        <div className="flex flex-wrap gap-2">
          {POPULAR_TICKERS.map(({ symbol, name }) => (
            <button
              key={symbol}
              onClick={() => handleAnalyze(symbol)}
              className="group glass glass-hover flex items-center gap-2.5 rounded-xl px-4 py-2.5 transition-all duration-200"
            >
              <span className="text-sm font-semibold text-white">{symbol}</span>
              <span className="text-xs text-slate-500 group-hover:text-slate-400">
                {name}
              </span>
              <ArrowRight className="h-3 w-3 text-slate-600 opacity-0 transition-all group-hover:opacity-100 group-hover:text-emerald-400" />
            </button>
          ))}
        </div>
      </div>

      {/* Features Grid */}
      <div>
        <h2 className="mb-4 text-xs font-medium uppercase tracking-wider text-slate-500">
          Platform Capabilities
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 stagger-children">
          {FEATURES.map(({ icon: Icon, title, desc, color }) => (
            <div
              key={title}
              className="glass glass-hover rounded-2xl p-5 transition-all duration-200"
            >
              <div
                className={cn(
                  "mb-3 flex h-10 w-10 items-center justify-center rounded-xl",
                  color
                )}
              >
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="text-sm font-semibold text-white">{title}</h3>
              <p className="mt-1 text-xs leading-relaxed text-slate-500">
                {desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
