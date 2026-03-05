# 🏗️ Technical Onboarding Guide — GenAI Test Automation Platform

**Audience:** New engineers joining the team  
**Author:** Lead Software Architect  
**Version:** 1.1 | Last Updated: March 2026

---

## 1. The Vision & High-Level Architecture

Welcome to the team! You're joining a project that sits at the intersection of **AI/ML engineering** and **test automation infrastructure**. Here's the big picture.

### What We Built

An **offline-first, AI-driven test automation platform** that lets QA engineers describe what they want to test *in plain English*, and the system generates executable test scripts automatically — using our own proprietary libraries as context.

### The Three-Tier Stack

```
┌─────────────────────────────────────────────────────┐
│              React 18 / TypeScript Frontend          │
│         (Vite + shadcn/ui + Tailwind CSS)            │
├─────────────────────────────────────────────────────┤
│              FastAPI / Python Backend                 │
│    (RAG Engine + Ollama Client + Code Guardrails)     │
├─────────────────────────────────────────────────────┤
│           Local Infrastructure Layer                  │
│   (SQLite · FAISS Vector DB · Ollama LLM · ADB/USB)  │
└─────────────────────────────────────────────────────┘
```

- **Frontend (React/TypeScript):** A single-page application providing the dashboard, script generation UI, execution history, device management, and real-time WebSocket updates. It communicates with the backend exclusively through typed HTTP endpoints.

- **Backend (FastAPI/Python):** The orchestration brain. It hosts the REST API, manages projects and test cases in SQLite, runs the RAG pipeline for context retrieval, interfaces with Ollama for LLM inference, and enforces code safety through static analysis guardrails.

- **Ollama LLM with RAG:** This is what makes the platform *intelligent*. Instead of sending a bare prompt to the LLM, we first **retrieve relevant method signatures and docstrings** from our indexed enterprise libraries (using FAISS vector search), then inject that context into a carefully constructed "Mega-Prompt." This ensures the generated scripts actually use our real APIs — not hallucinated ones.

> **Key Design Principle:** Everything runs locally. No cloud dependencies. No data leaves the machine. This is critical for enterprise environments with strict data governance.

---

## 2. The Backend Engine (FastAPI)

The backend lives in `backend/app/` and is organized as follows:

```
backend/app/
├── main.py                  # FastAPI app, CORS, lifespan events
├── config.py                # Pydantic Settings (env vars, paths, security)
├── api/                     # Route handlers (projects, devices, scripts, executions, dashboard)
├── models/
│   ├── database.py          # SQLAlchemy models + SQLite connection
│   └── schemas.py           # Pydantic request/response schemas
└── services/
    ├── rag_engine.py         # FAISS indexing, embedding, prompt building, code guardrail
    ├── ollama_client.py      # HTTP client for local Ollama server
    ├── script_generator.py   # Orchestrator: RAG → Ollama → Guardrail
    ├── execution_service.py  # Test runner (Playwright/Appium)
    ├── automation_adapters.py# Adapter pattern for web vs. mobile
    └── mtk_connect.py        # Device bridge (ADB)
```

### 2.1 The API Client Layer — Typed Endpoints & Pydantic Validation

Every request and response flowing through FastAPI is validated by **Pydantic models** defined in `backend/app/models/schemas.py`.

- **Request validation:** When a `POST /scripts/generate` request arrives, FastAPI automatically deserializes the JSON body into a `ScriptGenerationRequest` Pydantic model. If any field is missing or has the wrong type, FastAPI returns a `422 Unprocessable Entity` *before our code even runs*. Zero manual validation needed.

- **Response serialization:** Return values are typed as `ScriptGenerationResponse`, ensuring the frontend always receives a predictable shape. This creates a **contract** between frontend and backend.

- **Enums for safety:** Fields like `device_type`, `platform`, and `test_type` use Python `Enum` classes, so invalid values (e.g., `"blackberry"`) are rejected at the schema level.

```python
# Example: The request model guarantees these fields exist and are valid
class ScriptGenerationRequest(BaseModel):
    project_id: str
    description: str
    device_type: DeviceType    # Enum: 'web' | 'mobile'
    platform: Platform         # Enum: 'chrome' | 'firefox' | 'android' | ...
    test_type: TestType        # Enum: 'functional' | 'regression' | ...
```

> **Why this matters:** The frontend mirrors these types in `src/services/api/types.ts`. When you change a backend schema, you update the frontend type — and TypeScript catches every mismatched call site at compile time.

### 2.2 Resilience Logic — Exponential Backoff & Retries

The system is designed to handle the reality that local services (Ollama, ADB devices) are not always immediately responsive.

- **Frontend retry config** (`src/services/api/config.ts`):
  ```typescript
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,  // Base delay in ms
  ```

- **Connection Status Overlay** uses exponential backoff when polling health endpoints:
  - First retry: ~1 second
  - Second retry: ~2 seconds
  - Third retry: ~4 seconds
  - This prevents flooding a struggling service with requests while still recovering quickly once it's back.

- **Backend-side:** The Ollama client (`ollama_client.py`) wraps `httpx` with explicit timeout handling. If Ollama is loading a model into VRAM, the first request may take 30+ seconds — the client accounts for this gracefully rather than failing immediately.

### 2.3 Timeouts — The 30s vs. 310s Split

This is a deliberate architectural decision, not an accident:

| Request Type | Timeout | Rationale |
|---|---|---|
| Standard API calls | **30 seconds** | Health checks, CRUD operations, device validation — these should be near-instant. If they take 30s, something is genuinely broken. |
| LLM inference (`/scripts/generate`) | **310 seconds** | Ollama running a 7B-parameter model on consumer hardware can legitimately take 2–5 minutes. The backend allows 300s; the frontend allows 310s to account for network overhead. |

```typescript
// src/services/api/config.ts
TIMEOUT: 30000,        // 30s — standard requests
LLM_TIMEOUT: 310000,   // 310s — LLM generation only
```

```python
# backend/app/config.py
OLLAMA_TIMEOUT: int = 120  # Base timeout, extended per-request for generation
```

> **Mental model:** Think of it like a restaurant. Ordering takes 30 seconds. But if you order a slow-cooked dish, you wait longer — and you don't cancel the order after 30 seconds just because the food isn't ready yet.

---

## 3. The Frontend & Bridge (React/TypeScript)

The frontend lives in `src/` and follows a clean component architecture:

```
src/
├── services/api/
│   ├── config.ts        # Dynamic backend URL, timeouts, endpoint map
│   ├── client.ts        # Typed ApiClient class (singleton)
│   ├── types.ts         # TypeScript mirrors of Pydantic schemas
│   └── websocket.ts     # Real-time execution updates
├── components/
│   ├── layout/          # Sidebar, Header, ConnectionStatusOverlay
│   ├── views/           # Page-level components (Dashboard, Execute, History...)
│   ├── execute/         # Script generation UI (ConfigPanel, DescriptionInput)
│   └── ui/              # shadcn/ui primitives
├── hooks/
│   ├── useApi.ts        # React Query wrappers for API calls
│   └── useExecutionWebSocket.ts
└── types/automation.ts  # Shared domain types
```

### 3.1 Connection Status Overlay — Mixed Content Detection

This is one of our more elegant pieces of infrastructure. Here's the problem it solves:

**The Problem:** When the frontend is served from an HTTPS domain (e.g., Lovable's cloud preview at `https://*.lovable.app`), browsers **silently block** all requests to `http://localhost:8000`. No error. No log. The request just hangs as "Pending" forever. This is called **mixed-content blocking**.

**Our Solution** (`src/components/layout/ConnectionStatusOverlay.tsx`):

1. **Detection:** On mount, the overlay calls `isMixedContentBlocked()` which checks:
   ```typescript
   const isHttps = window.location.protocol === 'https:';
   const backendIsHttp = getBackendUrl().startsWith('http://');
   return isHttps && backendIsHttp;
   ```

2. **Runtime URL switching:** If mixed content is detected, the overlay presents an input field where users can enter an HTTPS tunnel URL (e.g., from `ngrok` or Cloudflare Tunnel). This URL is persisted to `localStorage` and takes effect immediately — no page reload required.

3. **Dynamic base URL:** The `ApiClient` reads the backend URL through a getter, not a constructor value:
   ```typescript
   private get baseUrl(): string {
     return API_CONFIG.BASE_URL;  // Reads from localStorage every time
   }
   ```

> **For local development:** Just run the frontend at `http://localhost:5173` and the backend at `http://localhost:8000`. Same protocol = no mixed-content issues.

### 3.2 Frontend → Backend Communication for Script Generation

When a user clicks **"Generate Script"**, here's the exact code path:

1. **`ExecuteView.tsx`** collects the form state (`TestConfiguration`) and calls the API hook.

2. **`useApi.ts`** wraps `apiClient.generateScript()` with React Query for caching, loading states, and error handling.

3. **`client.ts`** sends a typed `POST` request:
   ```typescript
   async generateScript(data: ScriptGenerationRequest): Promise<ScriptGenerationResponse> {
     return this.post<ScriptGenerationResponse>(
       API_ENDPOINTS.SCRIPT_GENERATE,  // → '/scripts/generate'
       data,
       API_CONFIG.LLM_TIMEOUT          // → 310,000ms
     );
   }
   ```

4. **FastAPI** receives the request, validates via Pydantic, and hands it to `ScriptGenerator.generate()`.

5. The response flows back as a typed `ScriptGenerationResponse` with the generated code, validation status, RAG context used, and generation time.

---

## 4. Data Science & Advanced Logic — Why RAG?

### The Problem with Naive Prompting

If you just tell an LLM: *"Write a Selenium test to login to the app"*, it will generate generic Selenium code. But **our enterprise apps use proprietary wrapper libraries** with custom methods like `MobileDriver.tap_element()` or `WebPortal.navigate_to_module()`. The LLM has never seen these APIs during training.

### How RAG Solves This

**RAG (Retrieval-Augmented Generation)** bridges the gap between the LLM's general knowledge and our specific codebase:

```
User Description
       │
       ▼
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Embedding   │────▶│  FAISS Vector    │────▶│  Top-K Relevant │
│  (MiniLM)    │     │  Similarity      │     │  Methods        │
│              │     │  Search          │     │  Retrieved      │
└──────────────┘     └──────────────────┘     └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  Mega-Prompt     │
                                              │  Construction    │
                                              │  (Constraints +  │
                                              │   Context +      │
                                              │   User Task)     │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  Ollama LLM     │
                                              │  (Mistral 7B)   │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  Code Guardrail │
                                              │  (AST Validation │
                                              │   + Import Block)│
                                              └─────────────────┘
```

### The Pipeline in Detail

1. **Indexing (one-time per project):** `LibraryIndexer` uses Python's `ast` module to parse enterprise library source files. It extracts class names, method signatures, docstrings, and parameter types — creating structured "documents."

2. **Embedding:** Each document is converted to a **384-dimensional vector** using `sentence-transformers/all-MiniLM-L6-v2`. These vectors are stored in a FAISS `IndexFlatL2` (flat index with L2/Euclidean distance).

3. **Retrieval:** When a user submits a description like *"test the login flow on Android"*, that description is embedded into the same vector space, and FAISS returns the **top-K most similar** method signatures (default K=10).

4. **Prompt Construction:** `PromptBuilder` assembles a "Mega-Prompt" with three sections:
   - **Constraints:** "Only use methods from the provided library. Do not import os, subprocess, sys..."
   - **Context:** The retrieved method signatures with their docstrings
   - **Task:** The user's natural language description

5. **Generation:** The assembled prompt is sent to Ollama (Mistral 7B) with `temperature=0.3` for deterministic, focused output.

6. **Guardrail Validation:** `CodeGuardrail` runs the generated code through:
   - `ast.parse()` — catches syntax errors
   - Import scanning — blocks forbidden modules (`os`, `subprocess`, `sys`, `shutil`, etc.)
   - Size limits — rejects scripts exceeding 50KB

> **Why FAISS `IndexFlatL2`?** For our scale (hundreds to low thousands of methods per library), a flat index gives exact nearest-neighbor search with sub-millisecond latency. No need for approximate methods like HNSW or IVF.

---

## 5. The "How to Run It" Mental Model

Here's the complete request lifecycle when a user clicks **"Generate Script"**:

```
┌─────────┐    POST /scripts/generate     ┌──────────┐
│ Browser  │ ──────────────────────────▶  │ FastAPI   │
│ (React)  │   {project_id, description,  │ Backend   │
│          │    device_type, platform,     │          │
│          │    test_type}                 │          │
└─────────┘                               └─────┬────┘
                                                │
                               ┌────────────────┼────────────────┐
                               ▼                ▼                ▼
                        ┌───────────┐   ┌────────────┐   ┌──────────┐
                        │ 1. Index  │   │ 2. Search  │   │ 3. Build │
                        │ Library   │   │ FAISS for  │   │ Mega-    │
                        │ (if new)  │   │ top-10     │   │ Prompt   │
                        │           │   │ methods    │   │          │
                        └───────────┘   └────────────┘   └─────┬────┘
                                                               │
                                                               ▼
                                                        ┌──────────┐
                                                        │ 4. Ollama│
                                                        │ Generate │
                                                        │ (≤300s)  │
                                                        └─────┬────┘
                                                               │
                                                               ▼
                                                        ┌──────────┐
                                                        │ 5. AST   │
                                                        │ Guardrail│
                                                        │ Validate │
                                                        └─────┬────┘
                                                               │
┌─────────┐    ScriptGenerationResponse    ┌──────────┐        │
│ Browser  │ ◀──────────────────────────── │ FastAPI   │◀───────┘
│ (React)  │   {script_code, is_valid,     │ Backend   │
│          │    validation_errors,          │          │
│          │    rag_context_used,           │          │
│          │    generation_time_ms}         │          │
└─────────┘                               └──────────┘
```

### Step-by-Step

| Step | Component | What Happens |
|------|-----------|-------------|
| **1** | **React UI** | User fills in project, device type, platform, test type, and a natural language description. Clicks "Generate Script." |
| **2** | **ApiClient** | `generateScript()` sends a `POST` to `/scripts/generate` with a **310-second timeout**. A loading spinner appears. |
| **3** | **FastAPI Router** | `scripts.py` receives the request. Pydantic validates the payload. Calls `script_generator.generate()`. |
| **4** | **ScriptGenerator** | Orchestrates the pipeline: index → search → prompt → generate → validate. |
| **5** | **LibraryIndexer** | If the project's library hasn't been indexed yet, it parses the Python source files via AST and builds a FAISS index. |
| **6** | **FAISS Search** | The user's description is embedded and compared against the indexed methods. Top 10 most relevant methods are returned. |
| **7** | **PromptBuilder** | Constructs the Mega-Prompt: constraints + retrieved context + user task. |
| **8** | **OllamaClient** | Sends the prompt to the local Ollama server running Mistral 7B. Waits up to 300 seconds. |
| **9** | **CodeGuardrail** | Parses the generated code with `ast.parse()`. Checks for forbidden imports. Validates size. |
| **10** | **Response** | Returns `ScriptGenerationResponse` with the code, validation status, which RAG documents were used, and timing. |
| **11** | **React UI** | Displays the generated script in a code editor. Shows validation status and RAG context as metadata. |

---

## 🚀 Getting Started

```bash
# Terminal 1 — Start Ollama
ollama serve
ollama pull mistral:7b

# Terminal 2 — Start Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3 — Start Frontend
npm install
npm run dev
# Open http://localhost:5173
```

---

**Welcome aboard. Read the code, break things, ask questions. The best way to learn this system is to generate a script and trace the request through every layer.**

— *Your Lead Architect*
