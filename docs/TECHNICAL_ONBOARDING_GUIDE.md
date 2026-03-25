# 🏗️ Technical Onboarding Guide — GenAI Test Automation Platform

**Audience:** New engineers joining the team  
**Author:** Lead Software Architect  
**Version:** 2.0 | Last Updated: March 2026

---

## Table of Contents

1. [Welcome & Project Overview](#1-welcome--project-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Project Structure & File Map](#3-project-structure--file-map)
4. [Backend Deep Dive (FastAPI/Python)](#4-backend-deep-dive-fastapipython)
5. [Frontend Deep Dive (React/TypeScript)](#5-frontend-deep-dive-reacttypescript)
6. [The RAG Pipeline & AI Engine](#6-the-rag-pipeline--ai-engine)
7. [Script Generation → Edit → Execution Flow](#7-script-generation--edit--execution-flow)
8. [Automation Adapters & Device Management](#8-automation-adapters--device-management)
9. [Real-Time Communication (WebSockets)](#9-real-time-communication-websockets)
10. [Resilience, Timeouts & Error Handling](#10-resilience-timeouts--error-handling)
11. [Security & Code Guardrails](#11-security--code-guardrails)
12. [Local Development Setup](#12-local-development-setup)
13. [Common Debugging Scenarios](#13-common-debugging-scenarios)
14. [Contributing Guidelines](#14-contributing-guidelines)
15. [Glossary](#15-glossary)

---

## 1. Welcome & Project Overview

Welcome to the team! You're joining a project at the intersection of **AI/ML engineering** and **test automation infrastructure**.

### What This Platform Does

An **offline-first, AI-driven test automation platform** that lets QA engineers describe what they want to test *in plain English*, and the system generates executable test scripts automatically — using proprietary enterprise libraries as context.

### Key Design Principles

| Principle | Description |
|-----------|-------------|
| **Local-First** | Everything runs on the user's machine. No cloud dependencies. No data leaves the network. |
| **AI-Augmented, Not AI-Replaced** | The LLM generates scripts, but engineers review, edit, and approve before execution. |
| **Library-Aware Generation** | RAG ensures generated scripts use real enterprise APIs, not hallucinated ones. |
| **Safety by Default** | A code guardrail blocks dangerous imports and patterns before any script runs. |
| **Project Isolation** | Each project has its own library index, test cases, and execution history. |

---

## 2. High-Level Architecture

### The Three-Tier Stack

```
┌─────────────────────────────────────────────────────┐
│              React 18 / TypeScript Frontend          │
│         (Vite + shadcn/ui + Tailwind CSS)            │
│                                                      │
│  Dashboard │ Script Generator │ Executor │ History    │
├─────────────────────────────────────────────────────┤
│              FastAPI / Python Backend                 │
│                                                      │
│  REST API ─── RAG Engine ─── Ollama Client           │
│  Execution Service ─── Automation Adapters           │
│  Code Guardrails ─── Device Bridge                   │
├─────────────────────────────────────────────────────┤
│           Local Infrastructure Layer                  │
│                                                      │
│  SQLite DB · FAISS Vector Index · Ollama LLM (7B)    │
│  Playwright · Appium · ADB/USB Device Bridge         │
└─────────────────────────────────────────────────────┘
```

### Data Flow Overview

```
User (Plain English) → Frontend → FastAPI → RAG Search → Prompt Build → Ollama LLM
                                                                          │
                                                                          ▼
User ← Frontend ← FastAPI ← Code Guardrail Validation ← Generated Script
```

---

## 3. Project Structure & File Map

### Backend (`backend/`)

```
backend/
├── app/
│   ├── main.py                     # FastAPI app entry, CORS, lifespan events
│   ├── config.py                   # Pydantic Settings — env vars, paths, security rules
│   ├── api/                        # REST route handlers
│   │   ├── projects.py             #   CRUD for projects
│   │   ├── devices.py              #   Device validation & status
│   │   ├── scripts.py              #   Script generation & saving
│   │   ├── executions.py           #   Test execution triggers & history
│   │   ├── dashboard.py            #   Dashboard aggregation stats
│   │   └── system.py               #   Health checks & system status
│   ├── models/
│   │   ├── database.py             #   SQLAlchemy ORM models + SQLite init
│   │   └── schemas.py              #   Pydantic request/response schemas
│   └── services/
│       ├── rag_engine.py           #   FAISS indexing, embedding, prompt building
│       ├── script_generator.py     #   Orchestrator: RAG → Ollama → Guardrail
│       ├── ollama_client.py        #   HTTP client for local Ollama server
│       ├── execution_service.py    #   Test runner orchestration
│       ├── automation_adapters.py  #   Adapter pattern: Playwright & Appium
│       └── mtk_connect.py          #   Device bridge (ADB, browser detection)
├── examples/
│   └── enterprise_lib/             #   Sample enterprise library for RAG demo
│       ├── web.py                  #     Browser, Actions, GoogleOAuth classes
│       └── mobile.py              #     MobileDevice, TouchActions classes
├── requirements.txt                #   Python dependencies
└── .env.example                    #   Environment config template
```

### Frontend (`src/`)

```
src/
├── App.tsx                         # Root component with routing
├── pages/
│   ├── Index.tsx                   # Main page (renders current view)
│   └── NotFound.tsx                # 404 page
├── components/
│   ├── layout/                     # Shell components
│   │   ├── Header.tsx              #   Top bar with notifications & profile
│   │   ├── Sidebar.tsx             #   Navigation sidebar
│   │   ├── ConnectionStatusOverlay.tsx  #  Backend connection monitor
│   │   ├── NotificationDropdown.tsx     #  Notification panel
│   │   └── ProfileDropdown.tsx          #  User profile menu
│   ├── views/                      # Page-level views
│   │   ├── DashboardView.tsx       #   System overview & stats
│   │   ├── ExecuteView.tsx         #   Script generation + execution control
│   │   ├── HistoryView.tsx         #   Past execution results
│   │   ├── DevicesView.tsx         #   Connected device management
│   │   ├── ProjectsView.tsx        #   Project CRUD
│   │   ├── SettingsView.tsx        #   App configuration
│   │   └── ArchitectureView.tsx    #   Interactive architecture docs
│   ├── execute/                    # Script generation sub-components
│   │   ├── ConfigurationPanel.tsx  #   Project, device, platform selectors
│   │   └── DescriptionInput.tsx    #   NL input + code editor + action buttons
│   ├── dashboard/                  # Dashboard widgets
│   │   ├── StatsCard.tsx           #   Metric display card
│   │   ├── DeviceStatus.tsx        #   Device health indicator
│   │   └── RecentExecutions.tsx    #   Latest test runs list
│   ├── results/
│   │   └── ResultsViewer.tsx       #   Execution results display
│   ├── architecture/               # Docs components
│   │   ├── MermaidDiagram.tsx      #   Mermaid chart renderer
│   │   └── CodeBlock.tsx           #   Syntax-highlighted code block
│   └── ui/                         # shadcn/ui primitives (40+ components)
├── services/api/
│   ├── config.ts                   # Backend URL, timeouts, endpoint map
│   ├── client.ts                   # Typed ApiClient singleton with retries
│   ├── types.ts                    # TypeScript mirrors of Pydantic schemas
│   ├── websocket.ts                # WebSocket client for real-time updates
│   └── index.ts                    # Barrel export
├── hooks/
│   ├── useApi.ts                   # React Query wrappers for all API calls
│   ├── useExecutionWebSocket.ts    # WebSocket hook for execution streaming
│   └── use-toast.ts                # Toast notification hook
└── types/
    └── automation.ts               # Shared domain types
```

---

## 4. Backend Deep Dive (FastAPI/Python)

### 4.1 Application Startup (`main.py`)

The app uses FastAPI's `lifespan` context manager:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create directories, initialize SQLite
    ensure_directories()
    await init_database()
    yield
    # Shutdown: cleanup
```

**CORS** is configured with `allow_origins=["*"]` for development. This permits the Lovable cloud preview and local dev servers to reach the backend.

### 4.2 API Layer — Typed Endpoints & Pydantic Validation

Every request/response is validated by **Pydantic models** in `models/schemas.py`:

```python
class ScriptGenerationRequest(BaseModel):
    project_id: str
    description: str
    device_type: DeviceType    # Enum: 'web' | 'mobile'
    platform: Platform         # Enum: 'chrome' | 'firefox' | 'android' | ...
    test_type: TestType        # Enum: 'functional' | 'regression' | ...
```

**Why this matters:** The frontend mirrors these in `src/services/api/types.ts`. When you change a backend schema, update the frontend type — TypeScript catches every mismatch at compile time.

### 4.3 API Endpoints Reference

| Method | Endpoint | Handler | Purpose |
|--------|----------|---------|---------|
| `GET` | `/system/health` | `system.py` | Health check — returns OK if backend is running |
| `GET` | `/system/status` | `system.py` | Detailed status including Ollama connectivity |
| `GET/POST` | `/projects/` | `projects.py` | List / create projects |
| `POST` | `/devices/validate` | `devices.py` | Validate device connection (real checks) |
| `POST` | `/scripts/generate` | `scripts.py` | Generate script via RAG + Ollama pipeline |
| `POST` | `/scripts/save` | `scripts.py` | Save/update a test case with script code |
| `POST` | `/executions/run` | `executions.py` | Execute a saved test case |
| `GET` | `/executions/history` | `executions.py` | Retrieve past execution results |
| `GET` | `/dashboard/stats` | `dashboard.py` | Aggregated metrics for dashboard view |

### 4.4 Service Layer Architecture

```
scripts.py (API route)
    └── script_generator.py (Orchestrator)
            ├── rag_engine.py → LibraryIndexer (FAISS indexing + search)
            ├── rag_engine.py → PromptBuilder (mega-prompt construction)
            ├── ollama_client.py (LLM inference)
            └── rag_engine.py → CodeGuardrail (AST validation)

executions.py (API route)
    └── execution_service.py (Orchestrator)
            ├── automation_adapters.py → PlaywrightAdapter (web tests)
            ├── automation_adapters.py → AppiumAdapter (mobile tests)
            └── mtk_connect.py (device bridge / browser detection)
```

### 4.5 Configuration (`config.py`)

All settings are managed through **Pydantic Settings** with `.env` file support:

| Setting | Default | Purpose |
|---------|---------|---------|
| `OLLAMA_HOST` | `http://localhost:11434` | Local LLM server URL |
| `OLLAMA_MODEL` | `mistral:7b` | Model used for code generation |
| `OLLAMA_TIMEOUT` | `120` | Base timeout (extended for generation) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer for RAG embeddings |
| `FAISS_INDEX_PATH` | `./data/faiss_index` | Vector index storage directory |
| `DATABASE_PATH` | `./data/automation.db` | SQLite database file |
| `FORBIDDEN_IMPORTS` | `os, subprocess, sys...` | Blocked imports in generated code |
| `MAX_SCRIPT_SIZE` | `50KB` | Maximum allowed generated script size |

---

## 5. Frontend Deep Dive (React/TypeScript)

### 5.1 Tech Stack

| Technology | Role |
|------------|------|
| **React 18** | UI framework with hooks-based state management |
| **TypeScript** | Type safety — mirrors backend Pydantic schemas |
| **Vite** | Build tool and dev server |
| **Tailwind CSS** | Utility-first styling with design tokens |
| **shadcn/ui** | 40+ accessible UI primitives (buttons, dialogs, tabs, etc.) |
| **React Query** (`@tanstack/react-query`) | Server state management, caching, retries |
| **React Router** | Client-side navigation |
| **Recharts** | Dashboard charts and metrics visualization |
| **Mermaid** | Architecture diagram rendering |

### 5.2 API Client (`services/api/client.ts`)

A singleton `ApiClient` class handles all backend communication:

```typescript
// Typed method — mirrors Pydantic schema exactly
async generateScript(data: ScriptGenerationRequest): Promise<ScriptGenerationResponse> {
  return this.post<ScriptGenerationResponse>(
    API_ENDPOINTS.SCRIPT_GENERATE,  // → '/scripts/generate'
    data,
    API_CONFIG.LLM_TIMEOUT          // → 310,000ms
  );
}
```

**Key features:**
- Exponential backoff on retries (1s → 2s → 4s)
- Dynamic base URL (supports runtime switching via Connection Overlay)
- Two timeout tiers: 30s standard, 310s for LLM calls

### 5.3 React Hooks (`hooks/useApi.ts`)

All API calls are wrapped in **React Query mutations/queries**:

```typescript
export const useGenerateScript = () => useMutation({
  mutationFn: (data: ScriptGenerationRequest) => apiClient.generateScript(data),
});
```

This gives you: loading states, error handling, caching, automatic retries — all for free.

### 5.4 Connection Status Overlay

**The Problem:** When the frontend is served from HTTPS (e.g., cloud preview), browsers silently block HTTP requests to `localhost` (mixed-content blocking).

**The Solution** (`ConnectionStatusOverlay.tsx`):
1. Detects if `window.location.protocol === 'https:'` while backend URL starts with `http://`
2. Shows an input to enter an HTTPS tunnel URL (ngrok, Cloudflare Tunnel)
3. Persists to `localStorage` — the `ApiClient` reads it dynamically on every request

**For local development:** Run both at `http://` to avoid this entirely.

### 5.5 Design System

The UI uses **semantic design tokens** defined in `src/index.css` and `tailwind.config.ts`:

```css
:root {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --primary: 217.2 91.2% 59.8%;
  /* ... */
}
```

**Rule:** Never use raw color values in components. Always use tokens like `bg-background`, `text-primary`, `border-muted`.

---

## 6. The RAG Pipeline & AI Engine

### Why RAG Instead of Fine-Tuning?

If you tell an LLM *"Write a Selenium test to login"*, it generates generic Selenium code. But **our enterprise apps use proprietary libraries** with custom methods like `MobileDriver.tap_element()` or `WebPortal.navigate_to_module()`. The LLM has never seen these APIs during training.

**RAG** bridges this gap without the cost and complexity of fine-tuning.

### Pipeline Architecture

```
User Description ("Test login on Android")
       │
       ▼
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Embedding   │────▶│  FAISS Vector    │────▶│  Top-10 Relevant│
│  (MiniLM     │     │  Similarity      │     │  Methods        │
│   all-MiniLM │     │  Search (L2)     │     │  Retrieved      │
│   -L6-v2)    │     │                  │     │                 │
└──────────────┘     └──────────────────┘     └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  Mega-Prompt     │
                                              │  ┌─────────────┐ │
                                              │  │ Constraints  │ │
                                              │  │ + Context    │ │
                                              │  │ + User Task  │ │
                                              │  └─────────────┘ │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  Ollama LLM     │
                                              │  (Mistral 7B)   │
                                              │  temp=0.3       │
                                              └────────┬────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  Code Guardrail │
                                              │  AST Validation  │
                                              │  Import Blocking │
                                              │  Size Check      │
                                              └─────────────────┘
```

### Step-by-Step

| Step | Component | File | What Happens |
|------|-----------|------|-------------|
| **1** | LibraryIndexer | `rag_engine.py` | Parses enterprise library `.py` files using Python `ast` module. Extracts classes, methods, signatures, docstrings. |
| **2** | SentenceTransformer | `rag_engine.py` | Converts each extracted document into a **384-dimensional vector** using `all-MiniLM-L6-v2`. |
| **3** | FAISS Index | `rag_engine.py` | Stores vectors in `IndexFlatL2` for exact nearest-neighbor search. Index is saved per-project. |
| **4** | Vector Search | `rag_engine.py` | User's description is embedded → compared against index → top-K most similar methods returned. |
| **5** | PromptBuilder | `rag_engine.py` | Assembles "Mega-Prompt": system constraints + retrieved method signatures + user task description. |
| **6** | OllamaClient | `ollama_client.py` | Sends prompt to local Ollama server (Mistral 7B). Uses `temperature=0.3` for deterministic output. |
| **7** | CodeGuardrail | `rag_engine.py` | Validates output: `ast.parse()` for syntax, import scanning for forbidden modules, size limit check. |

### Keyword Fallback

If FAISS/sentence-transformers are not installed, the system gracefully falls back to **keyword matching** — scoring documents by how many query terms appear in their text. This ensures the platform works even without the ML dependencies.

---

## 7. Script Generation → Edit → Execution Flow

This is the **core user workflow**. Understanding this end-to-end flow is essential.

### Visual Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        ExecuteView.tsx                           │
│                                                                  │
│  ┌─────────────────────┐    ┌──────────────────────────────────┐│
│  │ ConfigurationPanel  │    │ DescriptionInput                 ││
│  │                     │    │                                  ││
│  │ • Select Project    │    │ • Natural language input         ││
│  │ • Device Type       │    │ • [Generate Script] button       ││
│  │ • Platform          │    │ • Editable code editor (textarea)││
│  │ • Test Type         │    │ • [Execute Test] button          ││
│  │ • [Validate Device] │    │                                  ││
│  └─────────────────────┘    └──────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Request Lifecycle

| Step | Actor | Action |
|------|-------|--------|
| **1** | User | Selects project, device type, platform, test type. Clicks "Validate Device." |
| **2** | Frontend | `POST /devices/validate` — backend checks real device/browser availability. |
| **3** | User | Writes test description in plain English. Clicks "Generate Script." |
| **4** | Frontend | `POST /scripts/generate` with 310s timeout → backend runs full RAG pipeline. |
| **5** | Backend | RAG search → Mega-Prompt → Ollama inference → Code Guardrail validation. |
| **6** | Frontend | Displays generated script in **editable textarea**. User can modify the code. |
| **7** | User | Reviews/edits script. Clicks "Execute Test." |
| **8** | Frontend | `POST /scripts/save` — saves the **current edited script** (not original). |
| **9** | Frontend | `POST /executions/run` with saved `test_case_id`. |
| **10** | Backend | ExecutionService selects adapter (Playwright/Appium), runs script, collects results. |
| **11** | Frontend | Displays results: pass/fail, step timeline, duration, AI failure analysis. |

### Critical Implementation Detail

The frontend tracks `generatedCode` in React state. When the user edits the script, `handleCodeChange` updates this state **and resets `savedTestCaseId`**. This ensures the execute button always saves the latest version:

```typescript
const handleCodeChange = (code: string) => {
  setGeneratedCode(code);
  setSavedTestCaseId(null); // Forces re-save on next execute
};
```

---

## 8. Automation Adapters & Device Management

### Adapter Pattern

The system uses an abstract `BaseAutomationAdapter` with two concrete implementations:

```
BaseAutomationAdapter (abstract)
├── PlaywrightAdapter    # Web browser testing (Chrome, Firefox, WebKit)
└── AppiumAdapter        # Mobile testing (Android, iOS)
```

### PlaywrightAdapter

- Launches a browser via Playwright
- Executes the generated Python script with step tracking
- Captures screenshots on failure and video recordings
- Handles browser lifecycle (setup → execute → teardown)

### AppiumAdapter

- Connects to Appium server for mobile device automation
- Supports Android (ADB) and iOS (XCUITest)
- Same interface as PlaywrightAdapter for consistent orchestration

### Platform Enum Coercion

The `ExecutionService` coerces raw platform strings (from API) into `Platform` enum members before passing to adapters. This prevents adapter initialization failures from type mismatches:

```python
# execution_service.py
platform_enum = PlatformEnum(platform)  # "chrome" → Platform.CHROME
adapter.setup(platform=platform_enum)
```

### Device Validation (`mtk_connect.py`)

Real device validation checks:

| Platform | What's Checked |
|----------|----------------|
| **Chrome/Firefox/WebKit** | Playwright browser binaries installed (managed cache or system) |
| **Android** | ADB available + `adb devices` shows connected device |
| **iOS** | iOS tooling available + simulator/device detected |

---

## 9. Real-Time Communication (WebSockets)

### Execution Streaming

During test execution, the backend streams status updates to the frontend via WebSocket:

```
Frontend (useExecutionWebSocket) ←── WebSocket ←── Backend (execution_service)
```

**Events streamed:**
- Step started / completed
- Screenshot captured
- Execution progress percentage
- Final result (pass/fail + metrics)

### Frontend Hook

```typescript
// hooks/useExecutionWebSocket.ts
const { status, steps, progress } = useExecutionWebSocket(executionId);
```

---

## 10. Resilience, Timeouts & Error Handling

### Timeout Strategy

| Request Type | Frontend Timeout | Backend Timeout | Rationale |
|-------------|-----------------|----------------|-----------|
| Standard API | **30s** | N/A | CRUD, health checks — should be instant |
| LLM Generation | **310s** | **300s** | 7B model on consumer hardware can take 2-5 min |
| Device Validation | **30s** | **10s** | ADB/browser checks are fast |

### Exponential Backoff (Frontend)

```
Retry 1: wait ~1 second
Retry 2: wait ~2 seconds
Retry 3: wait ~4 seconds
(then fail)
```

Configured in `src/services/api/config.ts`:
```typescript
RETRY_ATTEMPTS: 3,
RETRY_DELAY: 1000,  // Base delay in ms
```

### Error Handling Patterns

- **Backend:** Every service method returns structured error responses. The RAG pipeline returns `validation_errors` array. Execution returns `ai_analysis` with human-readable failure explanations.
- **Frontend:** React Query provides `isError`, `error` objects. Toast notifications display user-friendly messages. The Connection Overlay handles connectivity failures separately.

### AI Failure Analyst

When a test fails, the system sends the error traceback to Ollama with a specialized prompt that translates technical errors into one-sentence explanations for non-technical users:

```python
# rag_engine.py → PromptBuilder.build_failure_analysis_prompt()
"Translate this technical error into a 1-sentence explanation..."
```

---

## 11. Security & Code Guardrails

### The CodeGuardrail (`rag_engine.py`)

Every LLM-generated script passes through static analysis before saving or execution:

| Check | Implementation | Purpose |
|-------|---------------|---------|
| **Syntax validation** | `ast.parse(code)` | Reject unparseable Python |
| **Forbidden imports** | AST walk for `Import`/`ImportFrom` nodes | Block `os`, `subprocess`, `sys`, `shutil`, `pathlib`, `socket`, `requests` |
| **Dangerous patterns** | Regex scan | Block `exec()`, `eval()`, `__import__()`, `compile()`, file writes |
| **Size limit** | Byte length check | Reject scripts > 50KB |

### Why These Restrictions?

Generated scripts run on the user's machine. Blocking system-level access prevents:
- Filesystem damage (no `os.remove`, `shutil.rmtree`)
- Network exfiltration (no `requests`, `socket`)
- Code injection (no `exec`, `eval`)
- Arbitrary process spawning (no `subprocess`)

---

## 12. Local Development Setup

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.10+ | Backend runtime |
| **Node.js** | 18+ | Frontend build tooling |
| **Ollama** | Latest | Local LLM server |
| **Playwright** | via pip | Browser automation (auto-installs browsers) |

### Quick Start

```bash
# Terminal 1 — Start Ollama (download model on first run)
ollama serve
ollama pull mistral:7b

# Terminal 2 — Start Backend
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install              # Install browser binaries
cp .env.example .env            # Configure if needed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3 — Start Frontend
npm install
npm run dev
# Open http://localhost:5173
```

### Verifying Everything Works

```bash
# Check backend health
curl http://localhost:8000/system/health

# Check Ollama is reachable
curl http://localhost:11434/api/tags

# Check backend can reach Ollama
curl http://localhost:8000/system/status
```

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and adjust:

```env
DEBUG=true                           # Enable debug logging
HOST=127.0.0.1
PORT=8000
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b
DATABASE_PATH=./data/automation.db
```

---

## 13. Common Debugging Scenarios

### "Script generation hangs forever"

**Cause:** Mixed-content blocking. HTTPS frontend → HTTP backend requests are silently dropped.  
**Fix:** Run frontend locally at `http://localhost:5173`, or use the Connection Overlay to set an HTTPS tunnel URL.

### "Automation adapter initialization failed"

**Cause:** Platform string not matching enum (e.g., `"chrome"` vs `Platform.CHROME`).  
**Fix:** Already handled — `execution_service.py` coerces strings to enums. If you see this, check that the platform value exists in the `Platform` enum in `schemas.py`.

### "Playwright setup failed / NotImplementedError"

**Cause:** Browser binaries not installed.  
**Fix:** Run `playwright install` in the backend virtual environment.

### "Generated script has forbidden imports"

**Cause:** LLM occasionally ignores constraints.  
**Fix:** The CodeGuardrail catches this automatically. The response will have `is_valid: false` with specific errors. The self-correction loop retries once with error feedback.

### "Execution shows hardcoded results"

**Cause:** Frontend component using mock data instead of API response.  
**Fix:** Ensure `ResultsViewer.tsx` reads from `result.steps` (the API response), not local mock arrays.

### Backend won't start — syntax error in `main.py`

**Known issue:** Check for leading whitespace on import/include lines. Python is whitespace-sensitive — extra spaces before `from` or `app.include_router` will cause `IndentationError`.

---

## 14. Contributing Guidelines

### Before You Code

1. **Read this guide** end-to-end
2. **Run the platform locally** and generate a test script — trace the request through every layer
3. **Understand the file you're changing** — read the module docstring and related tests

### Code Standards

| Area | Standard |
|------|----------|
| **Python** | Type hints on all functions. Docstrings on all classes/public methods. Use `loguru` for logging. |
| **TypeScript** | Strict mode. No `any` types. Mirror Pydantic schemas exactly in `types.ts`. |
| **CSS** | Use Tailwind semantic tokens only. Never hardcode colors. |
| **API changes** | Update both `schemas.py` (backend) AND `types.ts` (frontend) simultaneously. |
| **New endpoints** | Add to the endpoint map in `config.ts` and create a typed method in `client.ts`. |

### Adding a New Feature — Checklist

- [ ] Backend: Add Pydantic schema in `schemas.py`
- [ ] Backend: Add API route in `api/`
- [ ] Backend: Add service logic in `services/`
- [ ] Frontend: Add TypeScript type in `types.ts`
- [ ] Frontend: Add endpoint to `config.ts`
- [ ] Frontend: Add typed method to `client.ts`
- [ ] Frontend: Add React Query hook in `useApi.ts`
- [ ] Frontend: Build UI component
- [ ] Test: Verify end-to-end flow locally

### Key Files to Understand First

If you're short on time, read these five files in order:

1. `backend/app/services/rag_engine.py` — The AI brain (indexing, search, prompt building, guardrails)
2. `backend/app/services/script_generator.py` — The orchestrator (ties RAG + Ollama + guardrail together)
3. `src/components/views/ExecuteView.tsx` — The main user workflow (generate → edit → execute)
4. `src/services/api/client.ts` — How frontend talks to backend
5. `backend/app/services/execution_service.py` — How scripts actually run

---

## 15. Glossary

| Term | Definition |
|------|-----------|
| **RAG** | Retrieval-Augmented Generation — enriching LLM prompts with retrieved context from a knowledge base |
| **FAISS** | Facebook AI Similarity Search — efficient vector similarity search library |
| **Mega-Prompt** | The assembled prompt containing constraints + library context + user task |
| **Code Guardrail** | Static analysis layer that validates LLM-generated code before execution |
| **Ollama** | Local LLM server that runs models like Mistral 7B on consumer hardware |
| **Adapter Pattern** | Design pattern where PlaywrightAdapter and AppiumAdapter share a common interface |
| **Mixed-Content Blocking** | Browser security feature that blocks HTTP requests from HTTPS pages |
| **Enterprise Library** | Proprietary test automation APIs specific to the organization |
| **Sentence Transformer** | ML model that converts text into fixed-size vector embeddings |
| **IndexFlatL2** | FAISS index type using exact L2 (Euclidean) distance — accurate but brute-force |

---

**Welcome aboard. Read the code, break things, ask questions. The best way to learn this system is to generate a script and trace the request through every layer.**

— *Your Lead Architect*
