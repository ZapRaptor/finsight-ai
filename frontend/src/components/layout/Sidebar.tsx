"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  TrendingUp,
  Settings,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/chat", label: "AI Chat", icon: MessageSquare },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-white/[0.06] bg-[hsl(220,20%,4%)]">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-white/[0.06]">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/15 glow-accent">
          <TrendingUp className="h-5 w-5 text-emerald-400" />
        </div>
        <div>
          <h1 className="text-base font-semibold tracking-tight text-white">
            FinSight AI
          </h1>
          <p className="text-[10px] font-medium uppercase tracking-[0.15em] text-slate-500">
            Research Platform
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-emerald-500/10 text-emerald-400 shadow-[inset_0_1px_0_0_rgba(16,185,129,0.1)]"
                  : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
              )}
            >
              <Icon className="h-[18px] w-[18px]" />
              {label}
              {isActive && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse-glow" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Status Footer */}
      <div className="border-t border-white/[0.06] px-4 py-4">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Activity className="h-3.5 w-3.5 text-emerald-500" />
          <span>Gemini 2.5 Flash</span>
          <span className="ml-auto flex h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.5)]" />
        </div>
      </div>
    </aside>
  );
}
