# FinSight AI 📈

FinSight AI is an institutional-grade, AI-powered financial research assistant. It automates the extraction, analysis, and synthesis of financial data to provide actionable investment insights and structured investment memos. 

The platform leverages LangGraph for complex agentic workflows, Qdrant for vector-based semantic search, and Google's Gemini LLMs for reasoning over deep financial context.

---

## 🚀 Features

- **Automated Financial Pipeline:** Fetches raw financial statements (Income Statement, Balance Sheet, Cash Flow) and market data via `yfinance`.
- **Advanced Ratio Engine:** Automatically computes key metrics (P/E, ROE, Margins, Liquidity ratios) across multiple historical periods to detect trends.
- **RAG & Vector Search:** Uses `sentence-transformers` and `Qdrant` to embed and semantically search through financial documents and news context.
- **AI Investment Memos:** Generates structured, JSON-formatted investment memos with a clear Bull/Bear case, SWOT analysis, and final recommendation (BUY/HOLD/SELL) with confidence scores.
- **Streaming Chat Interface:** Interact dynamically with the AI via Server-Sent Events (SSE) for token-by-token financial analysis.
- **Caching Layer:** Redis-backed caching for rapid retrieval of subsequent queries and computed metrics.

## 🛠️ Architecture

FinSight AI is split into two primary components:

### 1. Backend (FastAPI + LangGraph)
- **FastAPI:** High-performance async API server.
- **LangGraph:** Orchestrates the state machine for the AI agent (Cache Check → Data Fetch → Metric Computation → Context Retrieval → Context Assembly → LLM Generation).
- **PostgreSQL / asyncpg:** Stores company metadata and audit logs for past queries.
- **Redis:** Handles caching for API responses and LLM generations to prevent redundant API calls.
- **Qdrant:** Vector database for the RAG pipeline.
- **Google GenAI (Gemini):** Core reasoning engine utilizing the `gemini-2.5-flash` model.

### 2. Frontend (Next.js) *(In Progress)*
- **Next.js (App Router):** Modern React framework for the UI.
- **Tailwind CSS:** For premium, glassmorphic styling and responsive design.
- **Recharts:** Interactive visualizations for financial trends.

---

## 🏗️ Local Development Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Docker & Docker Compose** (for PostgreSQL, Redis, and Qdrant)
- **Google Gemini API Key**

### 1. Start Infrastructure (Docker)
Ensure Docker is running, then boot the backend services:
```bash
docker-compose up -d
```
*This starts PostgreSQL on port 5432, Redis on port 6379, and Qdrant on port 6333.*

### 2. Backend Setup
Navigate to the backend directory and set up the Python environment:
```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the root of the project with the following:
```env
DATABASE_URL=postgresql+asyncpg://finsight:finsight_dev@localhost:5432/finsight_db
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_actual_gemini_api_key_here
EMBEDDING_MODEL=all-MiniLM-L6-v2
CACHE_TTL=86400
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
APP_ENV=development
LOG_LEVEL=INFO
```

Start the FastAPI development server:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup *(Coming Soon)*
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Endpoints

- `POST /api/chat`: Submit a financial query (e.g., "What are Apple's profit margins?") for a full JSON response.
- `POST /api/chat/stream`: Submit a query and receive a streamed SSE response (token-by-token).
- `POST /api/report/{symbol}`: Generate a complete structured Investment Memo for a ticker (e.g., `AAPL`).

---
*Built with Next.js, FastAPI, LangGraph, and Google Gemini.*