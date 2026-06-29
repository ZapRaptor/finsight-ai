import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a large number with suffix (1.2T, 345B, 12.5M, etc.)
 */
export function formatLargeNumber(num: number | null | undefined): string {
  if (num == null) return "N/A";
  const abs = Math.abs(num);
  if (abs >= 1e12) return (num / 1e12).toFixed(2) + "T";
  if (abs >= 1e9) return (num / 1e9).toFixed(2) + "B";
  if (abs >= 1e6) return (num / 1e6).toFixed(1) + "M";
  if (abs >= 1e3) return (num / 1e3).toFixed(1) + "K";
  return num.toFixed(2);
}

/**
 * Format a percentage value.
 */
export function formatPercent(value: number | null | undefined): string {
  if (value == null) return "N/A";
  return (value * 100).toFixed(2) + "%";
}

/**
 * Get the color class for a recommendation.
 */
export function getRecommendationColor(rec: string): string {
  switch (rec?.toUpperCase()) {
    case "BUY":
      return "text-emerald-400";
    case "SELL":
      return "text-red-400";
    case "HOLD":
      return "text-amber-400";
    default:
      return "text-slate-400";
  }
}

/**
 * Get the background color class for a recommendation badge.
 */
export function getRecommendationBg(rec: string): string {
  switch (rec?.toUpperCase()) {
    case "BUY":
      return "bg-emerald-500/15 border-emerald-500/30";
    case "SELL":
      return "bg-red-500/15 border-red-500/30";
    case "HOLD":
      return "bg-amber-500/15 border-amber-500/30";
    default:
      return "bg-slate-500/15 border-slate-500/30";
  }
}
