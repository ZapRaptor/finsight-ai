"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  TrendingUp,
  RefreshCw,
} from "lucide-react";
import {
  fetchReport,
  fetchMetrics,
  type ReportResponse,
  type MetricPeriod,
} from "@/lib/api";
import { formatPercent, formatLargeNumber } from "@/lib/utils";
import MemoCard from "@/components/report/MemoCard";
import {
  RevenueChart,
  MarginChart,
  RatiosChart,
} from "@/components/charts/FinancialCharts";

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const symbol = (params.ticker as string)?.toUpperCase() || "";

  const [report, setReport] = useState<ReportResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricPeriod[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState("");

  useEffect(() => {
    if (!symbol) return;

    let cancelled = false;

    async function loadData() {
      setLoading(true);
      setError(null);
      setActiveStep("Generating investment memo...");

      try {
        const [reportData, metricsData] = await Promise.all([
          fetchReport(symbol),
          fetchMetrics(symbol).catch(() => []),
        ]);

        if (cancelled) return;

        setReport(reportData);
        setMetrics(metricsData);
        setActiveStep("");
      } catch (err: unknown) {
        if (cancelled) return;
        setError(
          err instanceof Error ? err.message : "Failed to generate report"
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadData();
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/")}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.03] text-slate-400 transition-all hover:border-white/[0.15] hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                {symbol}
              </h1>
              {report?.memo?.recommendation && (
                <span
                  className={`rounded-full border px-3 py-0.5 text-xs font-semibold ${
                    report.memo.recommendation === "BUY"
                      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                      : report.memo.recommendation === "SELL"
                      ? "border-red-500/30 bg-red-500/10 text-red-400"
                      : "border-amber-500/30 bg-amber-500/10 text-amber-400"
                  }`}
                >
                  {report.memo.recommendation}
                </span>
              )}
            </div>
            <p className="mt-0.5 text-sm text-slate-500">
              AI-Generated Investment Memo & Analysis
            </p>
          </div>
        </div>

        {!loading && (
          <button
            onClick={() => window.location.reload()}
            className="flex items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-slate-400 transition-all hover:border-white/[0.15] hover:text-white"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <div className="relative">
            <div className="h-16 w-16 rounded-2xl bg-emerald-500/10 flex items-center justify-center glow-accent">
              <TrendingUp className="h-8 w-8 text-emerald-400" />
            </div>
            <Loader2 className="absolute -right-1 -top-1 h-5 w-5 text-emerald-400 animate-spin" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-white">
              Analyzing {symbol}
            </p>
            <p className="mt-1 text-xs text-slate-500 animate-pulse">
              {activeStep || "Running agentic pipeline..."}
            </p>
          </div>
          <div className="flex gap-2 mt-2">
            {[
              "Fetch",
              "Compute",
              "Retrieve",
              "Assemble",
              "Generate",
            ].map((step, i) => (
              <div
                key={step}
                className="h-1.5 w-8 rounded-full bg-white/[0.06] overflow-hidden"
              >
                <div
                  className="h-full rounded-full bg-emerald-500 animate-shimmer"
                  style={{ animationDelay: `${i * 0.3}s` }}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <div className="h-16 w-16 rounded-2xl bg-red-500/10 flex items-center justify-center">
            <AlertCircle className="h-8 w-8 text-red-400" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-white">Analysis Failed</p>
            <p className="mt-1 max-w-md text-xs text-slate-500">{error}</p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-400"
          >
            Retry
          </button>
        </div>
      )}

      {/* Report Content */}
      {!loading && !error && report && (
        <div className="space-y-6 animate-fade-in">
          {/* Key Metrics Row */}
          {metrics.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-2">
              {[
                {
                  label: "Revenue",
                  value: formatLargeNumber(metrics[0]?.revenue),
                  prefix: "$",
                },
                {
                  label: "Net Income",
                  value: formatLargeNumber(metrics[0]?.net_income),
                  prefix: "$",
                },
                {
                  label: "Gross Margin",
                  value: formatPercent(metrics[0]?.gross_margin),
                },
                {
                  label: "Net Margin",
                  value: formatPercent(metrics[0]?.net_margin),
                },
                { label: "P/E Ratio", value: metrics[0]?.pe_ratio?.toFixed(1) || "N/A" },
                {
                  label: "ROE",
                  value: formatPercent(metrics[0]?.roe),
                },
              ].map(({ label, value, prefix }) => (
                <div key={label} className="glass rounded-xl px-4 py-3">
                  <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
                    {label}
                  </p>
                  <p className="mt-1 text-lg font-semibold text-white">
                    {prefix || ""}{value}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Investment Memo */}
          <MemoCard memo={report.memo} />

          {/* Charts */}
          {metrics.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Financial Visualizations
              </h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <RevenueChart data={metrics} />
                <MarginChart data={metrics} />
              </div>
              <RatiosChart data={metrics} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
