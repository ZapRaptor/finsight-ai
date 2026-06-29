<div align="center">

# 📈 FinSight AI

**AI-Powered Institutional-Grade Financial Research Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Railway](https://img.shields.io/badge/Railway-Deployed-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Deployment](#-deployment) • [Tech Stack](#-tech-stack)

</div>

---

## 🎯 Overview

FinSight AI is a full-stack financial research platform that automates investment analysis using agentic AI workflows. It fetches live market data, computes institutional-grade financial ratios, retrieves relevant context via RAG, and generates structured investment memos — all orchestrated through a LangGraph state machine powered by **Gemini 2.5 Flash**.

> **Ask it anything:** *"What are Apple's profit margins and how have they trended?"* — and get a real-time, data-backed analysis streamed token-by-token.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **Agentic Pipeline** | 6-node LangGraph state machine: Cache → Fetch → Compute → Retrieve → Assemble → Generate |
| 📊 **Financial Ratio Engine** | Auto-computes P/E, ROE, margins, liquidity ratios across multiple periods |
| 🔍 **RAG Pipeline** | Sentence-transformers + Qdrant vector search for semantic context retrieval |
| 📝 **Investment Memos** | JSON-structured memos with Bull/Bear case, SWOT, and BUY/HOLD/SELL recommendations |
| ⚡ **SSE Streaming** | Real-time token-by-token financial analysis via Server-Sent Events |
| 🗄️ **Smart Caching** | Redis-backed caching layer — sub-100ms responses on repeated queries |
| 🐳 **Containerized** | Full Docker Compose stack: PostgreSQL, Redis, Qdrant |
| 🎨 **Interactive Dashboard** | Next.js 16 frontend with dark-mode glassmorphic UI, Recharts visualizations, and markdown-rendered AI chat |
| 🚀 **Cloud Deployed** | Backend on Railway, frontend on Vercel, vector DB on Qdrant Cloud |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 16)                      │
│         Tailwind CSS · Recharts · ReactMarkdown · SSE        │
│                    Deployed on Vercel                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend (Railway)                    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              LangGraph State Machine                 │    │
│  │                                                      │    │
│  │  check_cache ──► fetch_data ──► compute_metrics     │    │
│  │       │                              │               │    │
│  │   use_cache     retrieve_context ◄───┘               │    │
│  │                      │                               │    │
│  │              assemble_context                        │    │
│  │                      │                               │    │
│  │             generate_response ──► cache_result       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Services:  LLM (Gemini) · Embedder · Fetcher · Ratios      │
└──────┬──────────┬──────────┬──────────┬─────────────────────┘
       │          │          │          │
  ┌────▼───┐ ┌───▼───┐ ┌───▼────┐ ┌───▼──────┐
  │Postgres│ │ Redis │ │ Qdrant │ │ yfinance │
  │Railway │ │Railway│ │ Cloud  │ │  (API)   │
  └────────┘ └───────┘ └────────┘ └──────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **[Gemini API Key](https://aistudio.google.com/apikey)** (free tier works)

### 1. Clone the Repository

```bash
git clone https://github.com/ZapRaptor/finsight-ai.git
cd finsight-ai
```

### 2. Start Infrastructure

```bash
docker-compose up -d
```

This boots **PostgreSQL** (`:5432`), **Redis** (`:6379`), and **Qdrant** (`:6333`).

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 4. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 📡 API Reference

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Non-streaming financial Q&A |
| `POST` | `/api/chat/stream` | SSE streaming response (token-by-token) |

**Request Body:**
```json
{
  "symbol": "AAPL",
  "question": "What are Apple's profit margins?",
  "include_documents": true
}
```

### Investment Memo

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/report/{symbol}` | Generate structured investment memo |

**Response:**
```json
{
  "memo": {
    "summary": "Apple demonstrates robust profitability...",
    "recommendation": "BUY",
    "confidence": 0.75,
    "bull_case": ["Revenue growth rebounded to 6.43%...", "..."],
    "bear_case": ["PE ratio of 37.21 is elevated...", "..."],
    "swot": {
      "strengths": ["..."],
      "weaknesses": ["..."],
      "opportunities": ["..."],
      "threats": ["..."]
    }
  }
}
```

### Health & Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Server health check |
| `GET` | `/api/financials/{symbol}` | Raw financial statements |
| `GET` | `/api/metrics/{symbol}` | Computed financial ratios |
| `GET` | `/api/company/{symbol}` | Company metadata |

---

## ☁️ Deployment

### Backend → Railway

1. Create a new project on [Railway](https://railway.app)
2. Add **PostgreSQL** and **Redis** plugins from the dashboard
3. Connect your GitHub repo and set root directory to `/backend`
4. Set environment variables:
   - `GEMINI_API_KEY` — your Gemini API key
   - `QDRANT_URL` — your Qdrant Cloud cluster URL
   - `QDRANT_API_KEY` — your Qdrant Cloud API key
   - `APP_ENV=production`
   - `CORS_ORIGINS=["https://your-app.vercel.app"]`
   - `DATABASE_URL` and `REDIS_URL` are auto-set by Railway plugins

### Vector DB → Qdrant Cloud

1. Sign up at [Qdrant Cloud](https://cloud.qdrant.io) (free 1 GB tier)
2. Create a cluster and get the URL + API key
3. Set `QDRANT_URL` and `QDRANT_API_KEY` on Railway

### Frontend → Vercel

1. Import the repo on [Vercel](https://vercel.com)
2. Set root directory to `frontend`
3. Set env var: `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`
4. Deploy

---

## 🛠 Tech Stack

<table>
<tr>
<td><b>Category</b></td>
<td><b>Technology</b></td>
</tr>
<tr>
<td>Backend Framework</td>
<td>FastAPI, Uvicorn</td>
</tr>
<tr>
<td>Agent Orchestration</td>
<td>LangGraph (6-node state machine)</td>
</tr>
<tr>
<td>LLM</td>
<td>Google Gemini 2.5 Flash</td>
</tr>
<tr>
<td>Embeddings</td>
<td>sentence-transformers (all-MiniLM-L6-v2)</td>
</tr>
<tr>
<td>Vector Database</td>
<td>Qdrant (Cloud)</td>
</tr>
<tr>
<td>Relational Database</td>
<td>PostgreSQL 16 + asyncpg</td>
</tr>
<tr>
<td>Cache</td>
<td>Redis 7</td>
</tr>
<tr>
<td>Data Source</td>
<td>yfinance</td>
</tr>
<tr>
<td>Frontend</td>
<td>Next.js 16, Tailwind CSS, Recharts, ReactMarkdown</td>
</tr>
<tr>
<td>Containerization</td>
<td>Docker Compose</td>
</tr>
<tr>
<td>Deployment</td>
<td>Railway (backend), Vercel (frontend), Qdrant Cloud (vectors)</td>
</tr>
</table>

---

## 📁 Project Structure

```
finsight-ai/
├── .env.example                  # Environment configuration template
├── docker-compose.yml            # PostgreSQL + Redis + Qdrant (local dev)
├── README.md
├── LICENSE
├── backend/
│   ├── Procfile                  # Railway deployment entrypoint
│   ├── railway.toml              # Railway build/deploy config
│   ├── runtime.txt               # Python version pin
│   ├── requirements.txt
│   └── app/
│       ├── main.py               # FastAPI application entry point
│       ├── config.py             # Pydantic settings
│       ├── agents/
│       │   ├── state.py          # LangGraph state definition
│       │   ├── nodes.py          # Pipeline node logic
│       │   └── graph.py          # State machine wiring
│       ├── api/routes/
│       │   ├── chat.py           # Chat endpoints (+ SSE stream)
│       │   ├── report.py         # Investment memo generation
│       │   └── ticker.py         # Financial data & metrics
│       ├── db/
│       │   ├── engine.py         # Async SQLAlchemy engine
│       │   ├── models.py         # ORM models
│       │   └── crud.py           # Database operations
│       └── services/
│           ├── llm.py            # Gemini 2.5 Flash client
│           ├── embedder.py       # Qdrant + sentence-transformers
│           ├── fetcher.py        # yfinance data fetcher
│           ├── ratios.py         # Financial ratio engine
│           └── cache.py          # Redis caching layer
└── frontend/
    ├── vercel.json               # Vercel deployment config
    ├── package.json
    └── src/
        ├── app/
        │   ├── page.tsx          # Dashboard (ticker search)
        │   ├── chat/page.tsx     # AI Chat (SSE streaming)
        │   └── report/[ticker]/  # Investment memo & charts
        ├── components/
        │   ├── layout/Sidebar.tsx
        │   ├── chat/ChatInterface.tsx
        │   ├── charts/FinancialCharts.tsx
        │   └── report/MemoCard.tsx
        └── lib/
            ├── api.ts            # Backend API client
            └── utils.ts          # Formatting helpers
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
<sub>Built with ❤️ using FastAPI · LangGraph · Gemini 2.5 Flash · Next.js</sub>
</div>