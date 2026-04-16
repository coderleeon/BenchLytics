# Benchlytics

> **Benchlytics** is a production-grade LLM benchmarking and evaluation platform. It leverages an autonomous LLM-as-judge architecture to evaluate models across variations, tracking cost, latency, hallucination rates, and confidence scores across a live Next.js metrics dashboard.

---

```text
┌──────────────────────────────────────────────────────────────────┐
│                      Next.js 14 Frontend (:3000)                 │
│  • Leaderboard Dashboard (Recharts Trend Graphs)                 │
│  • Run Benchmark Interface (Prompt Variations & Multi-runs)      │
│  • Results View (Radar Charts, Hallucination Flags, Cost)        │
└──────────────────────────────┬───────────────────────────────────┘
                               │  POST /benchmark
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Layer (:8000)                          │
│  • Concurrent execution handling                                 │
│  • Asynchronous Background Tasks                                 │
│  • Pydantic validation & Model Abstractions                      │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Evaluation Engine                              │
│  • Distributes prompts across selected LLMs concurrently         │
│  • Triggers LLM-as-judge scoring pipeline                        │
│  • Tracks latency payload and absolute exact token counts        │
│  • Writes deterministic JSON run logs directly to SQLite         │
└──┬──────────────┬────────────────────────────────────────────────┘
   │              │              
   ▼              ▼              
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Gemini  │   │ OpenAI  │   │  Local  │   │  Judge  │
│ Models  │──▶│ Models  │──▶│ Models  │──▶│ Agent   │
│         │   │         │   │         │   │ (Rates) │
└─────────┘   └─────────┘   └─────────┘   └────┬────┘
                                               │
                                               ▼
                                     ┌──────────────────┐
                                     │  Metrics Output  │
                                     │  (Cost, Score,   │
                                     │   Hallucination) │
                                     └──────────────────┘
```

## Architecture
---

## The LLM-as-Judge
Instead of relying on fragile string comparisons, Benchlytics utilizes an elite LLM (e.g., Google Gemini 1.5 Pro) to judge the exact generations of its sub-models. The judge is strictly typed to output verifiable JSON matching the following schema mapping:

| Metric | Output Range | Description |
|---|---|---|
| **Correctness** | `0.0 - 10.0` | Assesses factual accuracy and strict instruction following. |
| **Clarity** | `0.0 - 10.0` | Evaluates formatting, cognitive readability, and conciseness. |
| **Reasoning** | `0.0 - 10.0` | Verifies logical progression, and step-by-step coherence. |
| **Confidence** | `0.0 - 10.0` | The Judge's absolute embedded confidence score for its own internal assessment. |
| **Hallucination** | `[0, 1]` | Boolean flagging ungrounded references or hallucinated statements. |

---

```text
Benchlytics/
├── benchlytics-backend/       ← FastAPI API & Processing Layer
│   ├── main.py                ← FastAPI entry point + endpoints
│   ├── config.yaml            ← Model configurations and API pricing mapping
│   ├── .env                   ← Secrets (OPENAI_API_KEY, GEMINI_API_KEY)
│   │
│   ├── api/routes.py          ← Core endpoint logic (POST /benchmark, GET /leaderboard)
│   ├── database/              ← SQLAlchemy Engine
│   │   ├── session.py         ← DB Connector
│   │   └── models.py          ← SQLite Schema (Tasks, ExperimentRuns, BenchmarkResults)
│   ├── evaluation/            
│   │   └── judge.py           ← The LLM-as-judge structured generator
│   └── models/
│       └── llm_manager.py     ← Vendor SDKs (google-genai, openai) + metadata extractors
│
├── benchlytics-frontend/      ← Next.js 14 + Tailwind v4 UI Layer
│   ├── src/app/
│   │   ├── layout.tsx         ← Navbar and Global configurations
│   │   ├── globals.css        ← Tailwind variables and Glassmorphism utilities
│   │   ├── page.tsx           ← Leaderboard & Timeline Analytics Dashboard
│   │   ├── run/page.tsx       ← Configurable A/B Testing form
│   │   └── results/[id]/      ← Dynamic comparison grids (Radar plots, Latency tracking)
│   │
│   ├── tailwind.config.ts     ← Tailwind compilation
│   └── package.json           ← Dependencies (recharts, lucide-react)
```

---

## 🚀 Getting Started

### 1. Start the FastAPI Backend
```bash
cd benchlytics-backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

**Configure Credentials**
```bash
# Update the keys in benchlytics-backend/.env
GEMINI_API_KEY="AIzaSy..."
OPENAI_API_KEY="sk-..."
```

**Run Server**
```bash
uvicorn main:app --reload
```
(*API runs on `http://localhost:8000`. SQLite DB is created automatically.*)

### 2. Start the Next.js Frontend
```bash
cd benchlytics-frontend

npm install
npm run dev
```
(*Dashboard runs on `http://localhost:3000`.*)

---

## System Capabilities

### ⚡ Automatic Token & Cost Mapping
Benchlytics extracts `total_token_count` metrics on execution and actively measures latency. The `config.yaml` dictates exact `cost_per_1k_tokens` algorithms, meaning your experiment dashboard live updates the exact USD spend mapping for comparisons.

### 🧪 Configuration Runs
- **Prompt Variations**: Execute Zero-Shot against Chain-of-Thought paths simultaneously within one execution instance.
- **Multi-Runs**: Automatically triggers iteration boundaries to verify standard-deviation outputs instead of relying on one-off testing bias.

### 📊 Dashboard Visualizations
Integration of `recharts` maps visual radar comparisons bridging correctness, clarity, and reasoning. Any hallucination detection overrides the UI warning layers to alert engineers immediately of failure conditions.

## Why This Platform Matters

- **Agnostic & Scalable** — Swap provider layers locally without rebuilding execution protocols.
- **Truth Oriented** — Employs judge grading patterns avoiding exact-string matches. 
- **Automated Logging** — All payload details are structured internally inside the local SQLite database seamlessly tracking historical performance regression across tasks.
