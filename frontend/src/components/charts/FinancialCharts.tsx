"use client";

import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { MetricPeriod } from "@/lib/api";
import { formatLargeNumber } from "@/lib/utils";

/* ── Custom Tooltip ───────────────────────────────────────── */

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-lg px-3 py-2 shadow-xl">
      <p className="mb-1 text-xs font-medium text-slate-400">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="text-xs" style={{ color: entry.color }}>
          {entry.name}: {typeof entry.value === "number" ? entry.value.toFixed(2) : entry.value}
          {entry.unit || ""}
        </p>
      ))}
    </div>
  );
}

/* ── Revenue & Net Income Chart ───────────────────────────── */

export function RevenueChart({ data }: { data: MetricPeriod[] }) {
  const chartData = [...data].reverse().map((d) => ({
    period: d.period?.slice(0, 7) || "",
    Revenue: d.revenue ? d.revenue / 1e9 : 0,
    "Net Income": d.net_income ? d.net_income / 1e9 : 0,
  }));

  return (
    <div className="glass rounded-2xl p-5">
      <h3 className="mb-4 text-sm font-semibold text-white">
        Revenue vs Net Income
        <span className="ml-2 text-xs font-normal text-slate-500">($ Billions)</span>
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} barGap={4}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="period" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}B`} />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: "11px", color: "hsl(220,10%,60%)" }}
          />
          <Bar
            dataKey="Revenue"
            fill="hsl(217, 91%, 60%)"
            radius={[4, 4, 0, 0]}
            fillOpacity={0.8}
          />
          <Bar
            dataKey="Net Income"
            fill="hsl(152, 69%, 53%)"
            radius={[4, 4, 0, 0]}
            fillOpacity={0.8}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ── Margin Trends Chart ──────────────────────────────────── */

export function MarginChart({ data }: { data: MetricPeriod[] }) {
  const chartData = [...data].reverse().map((d) => ({
    period: d.period?.slice(0, 7) || "",
    Gross: d.gross_margin ? +(d.gross_margin * 100).toFixed(2) : 0,
    Operating: d.operating_margin
      ? +(d.operating_margin * 100).toFixed(2)
      : 0,
    Net: d.net_margin ? +(d.net_margin * 100).toFixed(2) : 0,
  }));

  return (
    <div className="glass rounded-2xl p-5">
      <h3 className="mb-4 text-sm font-semibold text-white">
        Margin Trends
        <span className="ml-2 text-xs font-normal text-slate-500">(%)</span>
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="grossGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(217,91%,60%)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="hsl(217,91%,60%)" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="opGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(38,92%,55%)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="hsl(38,92%,55%)" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="netGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(152,69%,53%)" stopOpacity={0.3} />
              <stop offset="95%" stopColor="hsl(152,69%,53%)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="period" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: "11px", color: "hsl(220,10%,60%)" }}
          />
          <Area
            type="monotone"
            dataKey="Gross"
            stroke="hsl(217,91%,60%)"
            fill="url(#grossGrad)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="Operating"
            stroke="hsl(38,92%,55%)"
            fill="url(#opGrad)"
            strokeWidth={2}
          />
          <Area
            type="monotone"
            dataKey="Net"
            stroke="hsl(152,69%,53%)"
            fill="url(#netGrad)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ── Key Ratios Chart ─────────────────────────────────────── */

export function RatiosChart({ data }: { data: MetricPeriod[] }) {
  const chartData = [...data].reverse().map((d) => ({
    period: d.period?.slice(0, 7) || "",
    "P/E": d.pe_ratio ? +d.pe_ratio.toFixed(2) : 0,
    ROE: d.roe ? +(d.roe * 100).toFixed(2) : 0,
    "D/E": d.debt_to_equity ? +d.debt_to_equity.toFixed(2) : 0,
  }));

  return (
    <div className="glass rounded-2xl p-5">
      <h3 className="mb-4 text-sm font-semibold text-white">
        Key Financial Ratios
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} barGap={4}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="period" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: "11px", color: "hsl(220,10%,60%)" }}
          />
          <Bar
            dataKey="P/E"
            fill="hsl(270, 70%, 60%)"
            radius={[4, 4, 0, 0]}
            fillOpacity={0.8}
          />
          <Bar
            dataKey="ROE"
            fill="hsl(152, 69%, 53%)"
            radius={[4, 4, 0, 0]}
            fillOpacity={0.8}
          />
          <Bar
            dataKey="D/E"
            fill="hsl(0, 72%, 60%)"
            radius={[4, 4, 0, 0]}
            fillOpacity={0.8}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
