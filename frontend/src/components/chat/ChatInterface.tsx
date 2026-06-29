"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Loader2,
  Bot,
  User,
  Sparkles,
  AlertCircle,
} from "lucide-react";
import { streamChat, type SSEEvent } from "@/lib/api";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

interface StepInfo {
  text: string;
  done: boolean;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [symbol, setSymbol] = useState("AAPL");
  const [isLoading, setIsLoading] = useState(false);
  const [steps, setSteps] = useState<StepInfo[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    const assistantId = (Date.now() + 1).toString();
    const assistantMsg: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput("");
    setIsLoading(true);
    setSteps([]);

    const controller = streamChat(
      {
        symbol: symbol.toUpperCase(),
        question: userMsg.content,
        include_documents: true,
      },
      (event: SSEEvent) => {
        switch (event.event) {
          case "step":
            setSteps((prev) => {
              const updated = prev.map((s) => ({ ...s, done: true }));
              return [...updated, { text: event.data, done: false }];
            });
            break;

          case "token":
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + event.data }
                  : m
              )
            );
            break;

          case "error":
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      content: m.content || `Error: ${event.data}`,
                      isStreaming: false,
                    }
                  : m
              )
            );
            setIsLoading(false);
            break;

          case "done":
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, isStreaming: false } : m
              )
            );
            setSteps((prev) => prev.map((s) => ({ ...s, done: true })));
            setIsLoading(false);
            break;
        }
      }
    );

    abortRef.current = controller;
  };

  return (
    <div className="flex h-[calc(100vh-2rem)] flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.06] px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10">
            <Sparkles className="h-4 w-4 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">
              Financial Research Chat
            </h2>
            <p className="text-xs text-slate-500">
              Powered by Gemini 2.5 Flash • RAG-enhanced
            </p>
          </div>
        </div>

        {/* Symbol Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-500">Ticker:</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="w-20 rounded-md border border-white/[0.08] bg-white/[0.03] px-2.5 py-1.5 text-xs font-mono text-white placeholder-slate-600 outline-none transition-colors focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20"
            placeholder="AAPL"
          />
        </div>
      </div>

      {/* Pipeline Steps */}
      {steps.length > 0 && (
        <div className="border-b border-white/[0.06] px-6 py-3">
          <div className="flex flex-wrap gap-2">
            {steps.map((step, i) => (
              <div
                key={i}
                className={cn(
                  "flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-medium transition-all duration-300",
                  step.done
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "bg-amber-500/10 text-amber-400 animate-pulse"
                )}
              >
                {step.done ? (
                  <span className="text-emerald-400">✓</span>
                ) : (
                  <Loader2 className="h-2.5 w-2.5 animate-spin" />
                )}
                {step.text}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10 glow-accent">
              <Bot className="h-8 w-8 text-emerald-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">
                FinSight AI Research Assistant
              </h3>
              <p className="mt-1 max-w-md text-sm text-slate-500">
                Ask any financial question about a company. I&apos;ll fetch live
                data, compute metrics, and provide institutional-grade analysis.
              </p>
            </div>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {[
                "What are AAPL's profit margins?",
                "Analyze MSFT's debt position",
                "Compare GOOGL revenue growth trends",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2 text-xs text-slate-400 transition-all hover:border-emerald-500/30 hover:bg-emerald-500/5 hover:text-slate-200"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex gap-3 animate-fade-in",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            {msg.role === "assistant" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10">
                <Bot className="h-4 w-4 text-emerald-400" />
              </div>
            )}

            <div
              className={cn(
                "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                msg.role === "user"
                  ? "bg-emerald-500/15 text-white"
                  : "glass text-slate-200"
              )}
            >
              {msg.content ? (
                <div className="w-full">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ node, ...props }) => <p className="mb-3 last:mb-0" {...props} />,
                      ul: ({ node, ...props }) => <ul className="list-disc pl-5 mb-3 space-y-1" {...props} />,
                      ol: ({ node, ...props }) => <ol className="list-decimal pl-5 mb-3 space-y-1" {...props} />,
                      li: ({ node, ...props }) => <li className="pl-1" {...props} />,
                      h1: ({ node, ...props }) => <h1 className="text-lg font-bold mb-3 text-emerald-400 mt-2" {...props} />,
                      h2: ({ node, ...props }) => <h2 className="text-base font-bold mb-3 text-emerald-400 mt-2" {...props} />,
                      h3: ({ node, ...props }) => <h3 className="text-sm font-bold mb-2 text-emerald-400 mt-2" {...props} />,
                      strong: ({ node, ...props }) => <strong className="font-semibold text-emerald-300" {...props} />,
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
              ) : msg.isStreaming ? (
                <div className="flex items-center gap-1.5 text-slate-500">
                  <span className="animate-typing">●</span>
                  <span className="animate-typing [animation-delay:0.2s]">
                    ●
                  </span>
                  <span className="animate-typing [animation-delay:0.4s]">
                    ●
                  </span>
                </div>
              ) : null}
            </div>

            {msg.role === "user" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-700/50">
                <User className="h-4 w-4 text-slate-300" />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-white/[0.06] px-6 py-4">
        <form onSubmit={handleSubmit} className="flex items-center gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about any company's financials..."
              disabled={isLoading}
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 pr-12 text-sm text-white placeholder-slate-600 outline-none transition-all focus:border-emerald-500/40 focus:ring-2 focus:ring-emerald-500/10 disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 transition-all hover:bg-emerald-400 hover:shadow-emerald-500/30 disabled:opacity-40 disabled:shadow-none"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
