"use client";

import {
  TrendingUp,
  TrendingDown,
  Shield,
  Target,
  AlertTriangle,
  Zap,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import type { InvestmentMemo } from "@/lib/api";
import { cn, getRecommendationColor, getRecommendationBg } from "@/lib/utils";

export default function MemoCard({ memo }: { memo: InvestmentMemo }) {
  const confidence = Math.round(memo.confidence * 100);

  return (
    <div className="space-y-4 stagger-children">
      {/* Recommendation Banner */}
      <div
        className={cn(
          "glass rounded-2xl p-5 flex items-center justify-between",
          memo.recommendation === "BUY" && "glow-green",
          memo.recommendation === "SELL" && "glow-red"
        )}
      >
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
            AI Recommendation
          </p>
          <p
            className={cn(
              "mt-1 text-3xl font-bold tracking-tight",
              getRecommendationColor(memo.recommendation)
            )}
          >
            {memo.recommendation}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs font-medium text-slate-500">Confidence</p>
          <div className="mt-1 flex items-center gap-2">
            <div className="h-2 w-24 overflow-hidden rounded-full bg-white/[0.06]">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-1000",
                  memo.recommendation === "BUY"
                    ? "bg-emerald-500"
                    : memo.recommendation === "SELL"
                    ? "bg-red-500"
                    : "bg-amber-500"
                )}
                style={{ width: `${confidence}%` }}
              />
            </div>
            <span className="text-lg font-semibold text-white">
              {confidence}%
            </span>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="glass rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <BarChart3 className="h-4 w-4 text-blue-400" />
          <h3 className="text-sm font-semibold text-white">Executive Summary</h3>
        </div>
        <p className="text-sm leading-relaxed text-slate-300">{memo.summary}</p>
      </div>

      {/* Bull / Bear Cases */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Bull Case */}
        <div className="glass rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-4 w-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-emerald-400">
              Bull Case
            </h3>
          </div>
          <ul className="space-y-2.5">
            {memo.bull_case.map((point, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                <ArrowUpRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Bear Case */}
        <div className="glass rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <TrendingDown className="h-4 w-4 text-red-400" />
            <h3 className="text-sm font-semibold text-red-400">Bear Case</h3>
          </div>
          <ul className="space-y-2.5">
            {memo.bear_case.map((point, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                <ArrowDownRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-500" />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* SWOT */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <SwotQuadrant
          title="Strengths"
          items={memo.swot.strengths}
          icon={<Shield className="h-3.5 w-3.5" />}
          color="emerald"
        />
        <SwotQuadrant
          title="Weaknesses"
          items={memo.swot.weaknesses}
          icon={<AlertTriangle className="h-3.5 w-3.5" />}
          color="red"
        />
        <SwotQuadrant
          title="Opportunities"
          items={memo.swot.opportunities}
          icon={<Target className="h-3.5 w-3.5" />}
          color="blue"
        />
        <SwotQuadrant
          title="Threats"
          items={memo.swot.threats}
          icon={<Zap className="h-3.5 w-3.5" />}
          color="amber"
        />
      </div>

      {/* Guidance */}
      {memo.guidance && (
        <div className="glass rounded-2xl p-5">
          <h3 className="mb-2 text-sm font-semibold text-white">
            Forward Guidance
          </h3>
          <p className="text-sm leading-relaxed text-slate-300">
            {memo.guidance}
          </p>
        </div>
      )}
    </div>
  );
}

function SwotQuadrant({
  title,
  items,
  icon,
  color,
}: {
  title: string;
  items: string[];
  icon: React.ReactNode;
  color: "emerald" | "red" | "blue" | "amber";
}) {
  const colorMap = {
    emerald: "text-emerald-400 bg-emerald-500/10",
    red: "text-red-400 bg-red-500/10",
    blue: "text-blue-400 bg-blue-500/10",
    amber: "text-amber-400 bg-amber-500/10",
  };

  const [textColor, bgColor] = colorMap[color].split(" ");

  return (
    <div className="glass rounded-xl p-4">
      <div className={cn("flex items-center gap-1.5 mb-2.5", textColor)}>
        {icon}
        <h4 className="text-xs font-semibold">{title}</h4>
      </div>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="text-[11px] leading-snug text-slate-400">
            • {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
