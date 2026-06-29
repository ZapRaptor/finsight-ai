/**
 * FinSight AI — Backend API client.
 *
 * All communication with the FastAPI backend (port 8000) happens here.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ── Types ────────────────────────────────────────────────── */

export interface ChatRequest {
  symbol: string;
  question: string;
  include_documents?: boolean;
}

export interface ChatResponse {
  symbol: string;
  question: string;
  response: string;
  sources: string[];
  step_log: string[];
  errors: string[];
}

export interface InvestmentMemo {
  summary: string;
  bull_case: string[];
  bear_case: string[];
  swot: {
    strengths: string[];
    weaknesses: string[];
    opportunities: string[];
    threats: string[];
  };
  guidance: string;
  recommendation: "BUY" | "HOLD" | "SELL";
  confidence: number;
}

export interface ReportResponse {
  symbol: string;
  memo: InvestmentMemo;
  step_log: string[];
  errors: string[];
}

export interface MetricPeriod {
  period: string;
  pe_ratio: number | null;
  pb_ratio: number | null;
  roe: number | null;
  roa: number | null;
  current_ratio: number | null;
  debt_to_equity: number | null;
  gross_margin: number | null;
  operating_margin: number | null;
  net_margin: number | null;
  revenue_growth: number | null;
  revenue: number | null;
  net_income: number | null;
  operating_income: number | null;
}

export interface HealthResponse {
  status: string;
  environment: string;
  services: Record<string, string>;
}

/* ── SSE Event Types ──────────────────────────────────────── */

export interface SSEEvent {
  event: "step" | "token" | "sources" | "error" | "done";
  data: string;
}

/* ── API Functions ────────────────────────────────────────── */

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchMetrics(symbol: string): Promise<MetricPeriod[]> {
  const res = await fetch(`${API_BASE}/api/metrics/${symbol.toUpperCase()}`);
  if (!res.ok) throw new Error(`Failed to fetch metrics: ${res.status}`);
  const data = await res.json();
  return data.metrics || [];
}

export async function fetchReport(symbol: string): Promise<ReportResponse> {
  const res = await fetch(`${API_BASE}/api/report/${symbol.toUpperCase()}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Failed to fetch report: ${res.status}`);
  return res.json();
}

export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}

/**
 * Stream chat via SSE. Calls `onEvent` for each SSE event received.
 * Returns an AbortController so the caller can cancel.
 */
export function streamChat(
  req: ChatRequest,
  onEvent: (event: SSEEvent) => void,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        onEvent({ event: "error", data: `HTTP ${res.status}` });
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ") && currentEvent) {
            onEvent({
              event: currentEvent as SSEEvent["event"],
              data: line.slice(6),
            });
            currentEvent = "";
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") {
        onEvent({ event: "error", data: err.message });
      }
    }
  })();

  return controller;
}
