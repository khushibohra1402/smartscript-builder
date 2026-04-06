# 🧠 SmartScript Builder — AI-Powered Test Automation Platform

> **Generate, edit, and execute test scripts using natural language — powered by local LLMs and Retrieval-Augmented Generation (RAG).**

SmartScript Builder is a **fully offline**, AI-driven test automation platform that converts plain-English test descriptions into executable automation scripts for **Web**, **Mobile**, and **Set-Top Box (STB)** devices. It uses a local Ollama LLM combined with a FAISS-based RAG engine to produce accurate, library-aware test code — no cloud APIs required.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Folder Structure](#4-folder-structure)
5. [Setup & Installation](#5-setup--installation)
6. [How the System Works (End-to-End)](#6-how-the-system-works-end-to-end)
7. [Test Generation Guide](#7-test-generation-guide)
8. [Test Execution Guide](#8-test-execution-guide)
9. [Web Testing Guide](#9-web-testing-guide)
10. [Mobile Testing Guide](#10-mobile-testing-guide)
11. [STB Testing Guide](#11-stb-testing-guide)
12. [RAG & AI Explanation](#12-rag--ai-explanation)
13. [Code Guardrails & Validation](#13-code-guardrails--validation)
14. [Logging & Debugging](#14-logging--debugging)
15. [API Reference](#15-api-reference)
16. [How to Extend the System](#16-how-to-extend-the-system)
17. [Troubleshooting](#17-troubleshooting)
18. [Best Practices](#18-best-practices)

---

## 1. Project Overview

### What It Does

SmartScript Builder enables QA engineers and developers to **describe tests in natural language** and receive **ready-to-run automation scripts**. The platform handles the entire lifecycle:

- **Describe** → Write what you want to test in plain English
- **Generate** → AI produces executable test scripts using your project's libraries
- **Edit** → Review and modify scripts in an integrated code editor
- **Execute** → Run tests against real devices with live log streaming
- **Analyze** → Get structured results with AI-powered failure analysis

### Key Features

| Feature | Description |
|---|---|
| 🤖 AI Script Generation | Natural language → executable test code via Ollama LLM |
| 📚 RAG Engine | Retrieves project-specific library context for accurate code |
| 🌐 Web Testing | Playwright-based browser automation |
| 📱 Mobile Testing | Appium-based Android/iOS automation |
| 📺 STB Testing | Hardware automation via HDMI capture + IR control |
| 🔒 Code Guardrails | AST-based validation blocks unsafe imports and patterns |
| 📡 Real-Time Logs | WebSocket-based live execution streaming |
| 🏠 Fully Offline | Zero cloud dependencies — runs entirely on localhost |

### Problem It Solves

Writing automation scripts requires deep knowledge of testing frameworks, device APIs, and project libraries. SmartScript Builder eliminates this barrier by letting the AI learn your enterprise libraries through RAG, producing scripts that use the **correct APIs** from **your codebase** — not generic hallucinated code.

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (React 18)                    │
│                   http://localhost:8080                   │
│                                                          │
│  ┌─────────┐ ┌───────────┐ ┌──────────┐ ┌────────────┐  │
│  │Dashboard│ │Execute    │ │Projects  │ │Architecture│  │
│  │View     │ │View       │ │View      │ │View        │  │
│  └────┬────┘ └─────┬─────┘ └────┬─────┘ └────────────┘  │
│       │             │            │                        │
│       └─────────────┼────────────┘                       │
│                     │ REST + WebSocket                   │
└─────────────────────┼────────────────────────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                       │
│                  http://localhost:8000                    │
│                                                          │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────────┐  │
│  │API Layer │  │Execution  │  │Script Generator      │  │
│  │(Routers) │  │Service    │  │(2-Stage RAG Pipeline)│  │
│  └────┬─────┘  └─────┬─────┘  └──────────┬───────────┘  │
│       │               │                   │              │
│  ┌────▼─────┐  ┌──────▼──────┐  ┌────────▼──────────┐  │
│  │SQLite DB │  │Automation   │  │RAG Engine          │  │
│  │(Models)  │  │Adapters     │  │(FAISS + Embeddings)│  │
│  └──────────┘  └──────┬──────┘  └────────┬───────────┘  │
│                       │                   │              │
└───────────────────────┼───────────────────┼──────────────┘
                        │                   │
          ┌─────────────┼───────────────────┼──────┐
          │             ▼                   ▼      │
          │  ┌──────────────┐  ┌────────────────┐  │
          │  │ Playwright   │  │ Ollama LLM     │  │
          │  │ Appium       │  │ localhost:11434 │  │
          │  │ STB Hardware │  │ mistral:7b      │  │
          │  └──────────────┘  └────────────────┘  │
          │           INFRASTRUCTURE               │
          └────────────────────────────────────────┘
```

### Layer Breakdown

| Layer | Responsibility |
|---|---|
| **Frontend** | UI dashboard, test configuration, script editor, live log viewer |
| **API Layer** | FastAPI routers handling REST endpoints and WebSocket connections |
| **Script Generator** | 2-stage RAG pipeline: Intent/Plan → Code Generation |
| **RAG Engine** | FAISS vector index + sentence-transformers for context retrieval |
| **Execution Service** | Orchestrates test runs across adapters, streams logs |
| **Automation Adapters** | Playwright (Web), Appium (Mobile), STBAdapter (Hardware) |
| **Ollama** | Local LLM server running mistral:7b for code generation |
| **SQLite** | Local persistence for projects, test cases, and execution history |

---

## 3. Tech Stack

### Frontend

| Technology | Purpose |
|---|---|
| React 18 | UI framework |
| TypeScript 5 | Type safety |
| Vite 5 | Build tool and dev server |
| Tailwind CSS 3 | Utility-first styling |
| shadcn/ui | Component library (Radix primitives) |
| React Query | Server state management |
| Recharts | Dashboard charts |
| Mermaid | Architecture diagrams |
| React Router 6 | Client-side routing |

### Backend

| Technology | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| FastAPI | API framework |
| Uvicorn | ASGI server |
| SQLAlchemy 2.0 | ORM (async with aiosqlite) |
| SQLite | Local database |
| Pydantic 2.x | Schema validation |
| Loguru | Structured logging |
| WebSockets | Real-time log streaming |

### AI / ML

| Technology | Purpose |
|---|---|
| Ollama | Local LLM server |
| mistral:7b | Default language model |
| FAISS (faiss-cpu) | Vector similarity search |
| sentence-transformers | Embedding model (all-MiniLM-L6-v2) |
| Python `ast` module | Code guardrail / static analysis |

### Automation

| Technology | Purpose |
|---|---|
| Playwright | Web browser automation |
| Appium | Mobile device automation |
| OpenCV (cv2) | STB frame capture & template matching |
| Pytesseract | OCR for STB screen text extraction |
| RedRat IR Blaster | STB infrared remote control |

---

## 4. Folder Structure

```
smartscript-builder/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── config.py                 # Settings (Ollama, DB, security)
│   │   ├── api/                      # API route handlers
│   │   │   ├── dashboard.py          # GET /dashboard/stats
│   │   │   ├── devices.py            # Device validation endpoints
│   │   │   ├── executions.py         # Test execution + WebSocket
│   │   │   ├── projects.py           # Project CRUD + RAG indexing
│   │   │   ├── scripts.py            # Script generation + saving
│   │   │   └── system.py             # Health checks (/system/health)
│   │   ├── models/
│   │   │   ├── database.py           # SQLAlchemy ORM models
│   │   │   └── schemas.py            # Pydantic request/response schemas
│   │   └── services/                 # Core business logic
│   │       ├── automation_adapters.py # Playwright/Appium/STB adapters
│   │       ├── execution_service.py  # Test orchestration engine
│   │       ├── mtk_connect.py        # Device bridge + validation
│   │       ├── ollama_client.py      # LLM client (timeout: 300s)
│   │       ├── rag_engine.py         # FAISS indexing + retrieval
│   │       ├── redrat_bridge.py      # IR blaster control service
│   │       ├── script_generator.py   # 2-stage RAG generation pipeline
│   │       └── stb_vision.py         # HDMI capture + OpenCV + OCR
│   ├── libs/                         # Libraries indexed by RAG
│   │   └── stb/
│   │       ├── stb_driver.py         # High-level STB automation API
│   │       └── example_tests.py      # Few-shot examples for LLM
│   ├── examples/                     # Enterprise library examples
│   │   └── enterprise_lib/
│   │       ├── mobile.py             # Mobile automation library
│   │       └── web.py                # Web automation library
│   ├── requirements.txt              # Python dependencies
│   └── .env.example                  # Environment configuration template
│
├── src/                              # React frontend
│   ├── main.tsx                      # App entry point
│   ├── App.tsx                       # Router + layout
│   ├── pages/
│   │   ├── Index.tsx                 # Main application shell
│   │   └── NotFound.tsx              # 404 page
│   ├── components/
│   │   ├── views/                    # Page-level views
│   │   │   ├── DashboardView.tsx     # Metrics + charts
│   │   │   ├── ExecuteView.tsx       # Generate + edit + execute flow
│   │   │   ├── ProjectsView.tsx      # Project management
│   │   │   ├── DevicesView.tsx       # Device status grid
│   │   │   ├── HistoryView.tsx       # Execution history
│   │   │   ├── ArchitectureView.tsx  # Technical docs with Mermaid
│   │   │   └── SettingsView.tsx      # Configuration
│   │   ├── execute/                  # Execute view sub-components
│   │   │   ├── ConfigurationPanel.tsx # Device/platform selectors
│   │   │   ├── DescriptionInput.tsx  # Prompt input + script editor
│   │   │   └── TerminalLog.tsx       # Real-time log viewer
│   │   ├── dashboard/               # Dashboard widgets
│   │   │   ├── StatsCard.tsx
│   │   │   ├── DeviceStatus.tsx
│   │   │   └── RecentExecutions.tsx
│   │   ├── layout/                  # Shell components
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ConnectionStatusOverlay.tsx
│   │   │   ├── NotificationDropdown.tsx
│   │   │   └── ProfileDropdown.tsx
│   │   └── ui/                      # shadcn/ui primitives
│   ├── services/api/                # API communication layer
│   │   ├── client.ts                # Fetch wrapper with retry logic
│   │   ├── config.ts                # Base URL + endpoint registry
│   │   ├── types.ts                 # TypeScript API types
│   │   └── websocket.ts             # WebSocket client
│   ├── hooks/                       # Custom React hooks
│   │   ├── useApi.ts                # Health check + connectivity
│   │   └── useExecutionWebSocket.ts # Live execution streaming
│   └── types/
│       └── automation.ts            # Core domain types
│
├── docs/
│   └── TECHNICAL_ONBOARDING_GUIDE.md # Detailed onboarding document
│
├── index.html                        # Vite HTML entry
├── vite.config.ts                    # Vite configuration
├── tailwind.config.ts                # Tailwind theme
└── package.json                      # Node dependencies
```

### Key Directories Explained

| Directory | Purpose |
|---|---|
| `backend/app/api/` | FastAPI route handlers — each file maps to a resource (projects, scripts, executions, etc.) |
| `backend/app/services/` | Core business logic. This is where RAG, LLM, execution, and hardware services live |
| `backend/app/models/` | Database ORM models (`database.py`) and Pydantic schemas (`schemas.py`) for API validation |
| `backend/libs/stb/` | STB automation library that gets indexed by the RAG engine. The LLM uses these APIs in generated scripts |
| `backend/examples/` | Enterprise library examples (web/mobile) also indexed by RAG for few-shot prompting |
| `src/components/views/` | Full-page React views rendered by the router |
| `src/components/execute/` | Sub-components for the test generation and execution workflow |
| `src/services/api/` | Frontend API layer with centralized config, fetch client, and type definitions |

---

## 5. Setup & Installation

### Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| npm | 9+ | Package manager |
| Ollama | Latest | Local LLM server |
| Git | Any | Version control |

**Optional (for STB testing):**
- HDMI Capture Card (USB)
- RedRat IR Blaster (network-connected)
- Set-Top Box device

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd smartscript-builder
```

### Step 2: Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium firefox webkit

# Copy environment config
cp .env.example .env
# Edit .env if needed (defaults work for local development)

# Start the backend server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at **http://localhost:8000**. API docs at **/docs**.

### Step 3: Frontend Setup

```bash
# From project root
npm install
npm run dev
```

The frontend will be available at **http://localhost:8080**.

### Step 4: LLM Setup (Ollama)

```bash
# Install Ollama (https://ollama.ai)
# Then start the server:
ollama serve

# Pull the default model (in a separate terminal):
ollama pull mistral:7b
```

Ollama runs at **http://localhost:11434**.

### Step 5: Verify Installation

1. Open **http://localhost:8080** in your browser
2. The connection status overlay should show **Backend: Online** and **Ollama: Online**
3. Navigate to the Dashboard to see live metrics

---

## 6. How the System Works (End-to-End)

```
User types: "Test that clicking Login with valid credentials redirects to dashboard"
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  1. CONFIGURE                  │
                    │  Select: Project, Device Type, │
                    │  Platform, Test Type            │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  2. GENERATE (POST /scripts/   │
                    │     generate)                   │
                    │                                 │
                    │  Stage 1: Intent & Plan         │
                    │  → RAG retrieves library methods│
                    │  → LLM outputs structured plan  │
                    │                                 │
                    │  Stage 2: Code Generation       │
                    │  → Plan + context → LLM         │
                    │  → Executable Python script     │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  3. VALIDATE                    │
                    │  AST parsing checks:            │
                    │  ✓ Valid Python syntax           │
                    │  ✓ No forbidden imports          │
                    │  ✓ Uses correct library APIs     │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  4. EDIT (UI)                   │
                    │  User reviews and modifies      │
                    │  the script in the code editor  │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  5. EXECUTE (POST /executions)  │
                    │  Script saved → adapter init    │
                    │  → subprocess runs script       │
                    │  → Logs streamed via WebSocket  │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  6. RESULTS                     │
                    │  {status, metrics, steps,       │
                    │   artifacts, ai_analysis}       │
                    └───────────────────────────────┘
```

### Detailed Flow

1. **User configures** the test: selects project, device type (Web/Mobile/STB), platform, and test type
2. **Frontend sends** `POST /scripts/generate` with the natural language description and configuration
3. **RAG Engine** retrieves relevant library methods from the FAISS index (top-k similar chunks)
4. **Stage 1 LLM call** produces a structured intent + test plan (JSON)
5. **Stage 2 LLM call** generates executable Python code using the plan and library context
6. **Code Guardrail** validates the script via AST parsing (syntax, forbidden imports, API conformance)
7. **Script displayed** in the UI editor — user can modify before execution
8. **User clicks Execute** → script is saved, then run via the appropriate automation adapter
9. **Logs stream** in real-time over WebSocket to the terminal viewer
10. **Results returned** with pass/fail status, step-level metrics, and failure screenshots

---

## 7. Test Generation Guide

### Selecting Device Type

| Device Type | Platform Options | Use Case |
|---|---|---|
| **Web** | Chrome, Firefox, Safari | Browser-based application testing |
| **Mobile** | Android, iOS | Mobile app testing via Appium |
| **STB** | stb_linux, stb_proprietary | Set-Top Box testing via HDMI + IR |

### Writing a Good Description

The quality of the generated script depends on your prompt. Be specific:

**❌ Bad:** `"Test login"`

**✅ Good:** `"Navigate to the login page, enter username 'testuser@email.com' and password 'Test123!', click the Login button, and verify that the dashboard page loads with a welcome message"`

### Understanding the Output

The generated script will:
- Use only APIs from your project's indexed library
- Include proper setup/teardown
- Contain assertions for verification
- Include error handling and logging
- For STB: include hardware delays (`time.sleep()`) and retry loops

### Editing Before Execution

After generation, the script appears in an editable text area. You can:
- Modify assertions or expected values
- Add additional test steps
- Remove unwanted actions
- Adjust timing/delays

The **edited version** is what gets executed — not the original generated code.

---

## 8. Test Execution Guide

### How Execution Works Internally

1. **Script is saved** to the database via `POST /scripts/save`
2. **Adapter initializes** based on device type:
   - Web → Playwright launches browser
   - Mobile → Appium connects to device
   - STB → HDMI capture + RedRat IR initialized
3. **Script executes** in a subprocess (`python script.py`)
4. **Stdout/stderr captured** and streamed via WebSocket
5. **Results parsed** into structured format

### Result Schema

```json
{
  "execution_id": "uuid",
  "status": "PASS | FAIL | WARNING",
  "test_name": "Login Test",
  "project_name": "MyApp",
  "metrics": {
    "total_duration": 12.4,
    "avg_response_time": 0.3,
    "step_success_rate": 100.0
  },
  "steps": [
    {
      "action": "Navigate to login page",
      "result": true,
      "latency": 150.0,
      "error": null
    }
  ],
  "artifacts": {
    "video_path": "/artifacts/recording.webm",
    "screenshot_failure": null
  },
  "ai_analysis": "All steps passed. Login flow is functional."
}
```

### Where Reports Are Stored

| Artifact | Location |
|---|---|
| Execution records | SQLite database (`data/automation.db`) |
| Failure screenshots | `backend/reports/failure_<timestamp>.png` |
| Video recordings | `backend/artifacts/` |

---

## 9. Web Testing Guide

### How Playwright Is Used

The `PlaywrightAdapter` in `automation_adapters.py`:

1. Launches a browser instance (Chromium by default)
2. Creates a new browser context and page
3. Executes the generated Python script
4. Captures screenshots on failure
5. Cleans up resources after execution

### Supported Actions

Generated web test scripts can use:

```python
# Navigation
page.goto("https://example.com")

# Element interaction
page.click("button#submit")
page.fill("input[name='email']", "user@test.com")
page.select_option("select#country", "US")

# Assertions
assert page.title() == "Dashboard"
assert page.is_visible("text=Welcome")

# Waiting
page.wait_for_selector(".loaded")
page.wait_for_url("**/dashboard")
```

### Example Web Test Flow

```
Description: "Log in to the admin panel and verify the user list loads"
Device: Web → Chrome

Generated script:
1. Navigate to /admin/login
2. Fill email and password fields
3. Click "Sign In"
4. Wait for dashboard to load
5. Navigate to /admin/users
6. Assert user table is visible
7. Assert at least one row exists
```

---

## 10. Mobile Testing Guide

### Appium Integration

The `AppiumAdapter` connects to an Appium server to automate mobile devices.

### Requirements

| Requirement | Details |
|---|---|
| Appium Server | Running at `http://localhost:4723` |
| Android | ADB installed, device connected (`adb devices`) |
| iOS | Xcode + Simulator or physical device |

### Example Mobile Test Flow

```
Description: "Open the app, tap the search icon, type 'shoes', and verify results appear"
Device: Mobile → Android

Generated script:
1. Launch app
2. Wait for home screen
3. Tap search icon
4. Enter "shoes" in search field
5. Wait for results
6. Assert results list is not empty
```

### Device Validation

When you click **Validate Device Connection**, the backend checks:
- **Android:** `adb devices` returns a connected device
- **iOS:** Required tooling is available
- **Web:** Playwright browsers are installed

---

## 11. STB Testing Guide

### Hardware Requirements

| Component | Purpose | Connection |
|---|---|---|
| **Set-Top Box** | Device under test | HDMI output |
| **HDMI Capture Card** | Captures STB screen for vision analysis | USB to test machine |
| **RedRat IR Blaster** | Sends infrared remote commands to STB | Network (IP-based) |

### Architecture

```
┌──────────┐     HDMI      ┌────────────────┐     USB      ┌──────────────┐
│   STB    │───────────────▶│ HDMI Capture   │────────────▶│ Test Machine │
│  Device  │                │ Card           │              │ (Backend)    │
└──────────┘                └────────────────┘              └──────┬───────┘
      ▲                                                           │
      │ IR Signal                                                 │
      │                     ┌────────────────┐     HTTP/IP         │
      └─────────────────────│ RedRat IR      │◀───────────────────┘
                            │ Blaster        │
                            └────────────────┘
```

### How It Works

**Vision (STBVisionService):**
- Captures frames from HDMI input via `cv2.VideoCapture(hdmi_index)`
- Performs **template matching** (`cv2.matchTemplate`) to detect UI elements
- Uses **OCR** (`pytesseract.image_to_string`) to extract on-screen text
- Supports region-based cropping for targeted text extraction

**Control (RedRatBridge):**
- Sends IR commands over HTTP to the RedRat device
- Supports standard remote keys: `HOME`, `OK`, `UP`, `DOWN`, `LEFT`, `RIGHT`, `PLAY`, `PAUSE`, `FF`, `RW`, `BACK`, `EXIT`
- Commands have configurable delays for hardware latency

### STB Configuration in UI

When selecting **STB** as the device type, two additional fields appear:
- **RedRat IP Address** — e.g., `192.168.1.100`
- **HDMI Capture Index** — typically `0` for the first capture device

### Example STB Test Script

```python
from libs.stb.stb_driver import STBDriver
import time

driver = STBDriver(redrat_ip="192.168.1.100", hdmi_index=0)

# Navigate to home screen
driver.press_key("HOME")
time.sleep(2)

# Verify home screen loaded
assert driver.wait_for_screen("templates/home_screen.png", timeout=10)

# Navigate to content
driver.press_key("DOWN")
time.sleep(0.5)
driver.press_key("OK")
time.sleep(3)

# Verify playback started
text = driver.get_screen_text()
assert "Playing" in text or "00:" in text

print("STEP PASS: Content playback verified")
```

### Example Use Cases

| Test Case | Description |
|---|---|
| **Navigation Testing** | Verify menu navigation using directional keys and validate screen elements |
| **Playback Testing** | Start content playback and verify video is playing via frame analysis |
| **Resume Logic** | Pause content, navigate away, return, and verify resume prompt appears |
| **Channel Switching** | Switch channels and verify correct channel info displays |
| **Settings Validation** | Navigate to settings, change a value, verify it persists after reboot |

### Failure Evidence

When an STB test fails, the system:
1. Captures the current HDMI frame
2. Saves it as `backend/reports/failure_<timestamp>.png`
3. Returns the path in the execution result
4. AI analyzes the failure screenshot for root cause

---

## 12. RAG & AI Explanation

### Why RAG?

Standard LLMs don't know your proprietary APIs. RAG (Retrieval-Augmented Generation) solves this by:
1. **Indexing** your project libraries (method signatures, docstrings, examples)
2. **Retrieving** relevant context at generation time
3. **Injecting** that context into the LLM prompt

This means the LLM generates code using **your actual APIs** — not imagined ones.

### How Indexing Works

```
Project Library Files (.py)
         │
         ▼
┌─────────────────────┐
│ AST-Based Chunking  │  Parse Python files into structured chunks:
│                     │  • Class names + docstrings
│                     │  • Method signatures + parameters
│                     │  • Example usage patterns
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Sentence Transformer│  Model: all-MiniLM-L6-v2
│ (Embedding)         │  Output: 384-dimensional vectors
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ FAISS Index         │  IndexFlatL2 (Euclidean distance)
│ (Vector Store)      │  Stored at: data/faiss_index/
└─────────────────────┘
```

### How Retrieval Works

1. User's test description is embedded using the same sentence-transformer model
2. FAISS finds the **top-k most similar** library chunks (by Euclidean distance)
3. Retrieved chunks (method signatures, examples) are injected into the prompt
4. LLM generates code using only these provided APIs

### 2-Stage Generation Pipeline

**Stage 1 — Intent & Plan:**
- Input: User description + retrieved library context
- Output: Structured JSON with test intent, steps, and required methods

**Stage 2 — Code Generation:**
- Input: Stage 1 plan + library context + strict coding rules
- Output: Executable Python test script
- Context window: 16K tokens (`num_ctx: 16384`)

### Adding New Libraries to RAG

```bash
# 1. Place library files in your project directory
cp my_library.py backend/examples/my_project/

# 2. Create/select the project in the UI

# 3. Click "Index Library" on the project
# POST /projects/{id}/index

# 4. The RAG engine will:
#    - Parse all .py files via AST
#    - Generate embeddings
#    - Add to FAISS index
```

---

## 13. Code Guardrails & Validation

### What Gets Checked

Every generated script passes through the **CodeGuardrail** before saving or execution:

| Check | Description |
|---|---|
| **Syntax Validation** | Python `ast.parse()` ensures valid syntax |
| **Forbidden Imports** | Blocks: `os`, `subprocess`, `sys`, `shutil`, `pathlib`, `socket`, `requests` |
| **Import Whitelist** | Only allows imports from project libraries and standard safe modules |
| **Script Size** | Maximum 50KB per script |
| **Dangerous Patterns** | Detects `exec()`, `eval()`, `__import__()` calls |

### Why These Restrictions?

Generated code runs on your machine. The guardrails prevent the LLM from producing scripts that could:
- Access the filesystem (`os`, `pathlib`, `shutil`)
- Execute arbitrary commands (`subprocess`, `sys`)
- Make network requests (`socket`, `requests`)

### Self-Correction Loop

If validation fails, the system:
1. Collects validation errors
2. Feeds them back into the LLM prompt as correction feedback
3. Regenerates the script (1 retry attempt)
4. Validates again

---

## 14. Logging & Debugging

### Backend Logging

The backend uses **Loguru** for structured logging:

```
2024-01-15 14:23:01 | INFO     | app.services.script_generator:generate:45 - Starting script generation
2024-01-15 14:23:03 | DEBUG    | app.services.rag_engine:retrieve:89 - Retrieved 5 context chunks
2024-01-15 14:23:35 | INFO     | app.services.ollama_client:generate:112 - LLM response received (32.1s)
```

- **Console output:** Colored, formatted logs
- **File logs:** `logs/app.log` (rotated at 10MB, retained 7 days)

### Real-Time Execution Logs

During test execution, logs stream to the frontend via WebSocket:

```
[14:23:45] Starting test execution...
[14:23:46] Initializing PlaywrightAdapter (chrome)
[14:23:47] STEP PASS: Navigate to login page (latency: 150ms)
[14:23:48] STEP PASS: Fill email field (latency: 45ms)
[14:23:49] STEP FAIL: Assert dashboard loaded (error: timeout)
[14:23:49] Capturing failure screenshot...
[14:23:50] Execution complete: FAIL
```

The `TerminalLog` component in the frontend renders these with color coding:
- 🟢 Green: PASS steps
- 🔴 Red: FAIL steps / errors
- 🟡 Yellow: Warnings
- ⚪ White: Info messages

### Debugging Checklist

| Issue | Where to Look |
|---|---|
| Backend not starting | Terminal running `uvicorn` — check for import errors |
| API returning 500 | `logs/app.log` — full stack trace |
| Script generation slow | Ollama logs — check model loading status |
| Execution fails at adapter | Backend console — adapter initialization errors |
| Frontend can't connect | Browser DevTools → Network tab → check CORS and URL |

---

## 15. API Reference

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/system/health` | Health check (backend + Ollama status) |
| `GET` | `/system/status` | Detailed system status |

### Projects

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/projects` | List all projects |
| `POST` | `/projects` | Create new project |
| `GET` | `/projects/{id}` | Get project details |
| `PUT` | `/projects/{id}` | Update project |
| `DELETE` | `/projects/{id}` | Delete project |
| `POST` | `/projects/{id}/index` | Index project library for RAG |

### Scripts

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/scripts/generate` | Generate test script via RAG + LLM |
| `POST` | `/scripts/save` | Save test case with script |
| `GET` | `/scripts/test-cases/{id}` | Get saved test case |
| `POST` | `/scripts/analyze-failure` | AI failure analysis |

**Generate Request:**
```json
{
  "project_id": "uuid",
  "description": "Test login with valid credentials",
  "device_type": "web",
  "platform": "chrome",
  "test_type": "functional",
  "redrat_ip": null,
  "hdmi_capture_index": null
}
```

**Generate Response:**
```json
{
  "script_code": "from playwright.sync_api import ...",
  "is_valid": true,
  "validation_errors": [],
  "rag_context_used": ["WebDriver.click()", "WebDriver.fill()"],
  "generation_time_ms": 32100.5
}
```

### Executions

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/executions` | Execute a test case |
| `GET` | `/executions` | List execution history |
| `GET` | `/executions/{id}` | Get execution result |
| `WS` | `/ws/execution/{id}` | Real-time log streaming |

### Devices

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/devices` | List connected devices |
| `POST` | `/devices/validate` | Validate device connection |

### Dashboard

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/dashboard/stats` | Aggregated metrics |

---

## 16. How to Extend the System

### Adding a New Device Type

1. **Update schemas:** Add enum value in `backend/app/models/schemas.py` (`DeviceType`) and `src/types/automation.ts`
2. **Create adapter:** Add a new class extending `BaseAutomationAdapter` in `automation_adapters.py`
3. **Register adapter:** Update the adapter factory in `execution_service.py`
4. **Add device validation:** Extend `mtk_connect.py` with platform-specific checks
5. **Update UI:** Add the option to `ConfigurationPanel.tsx`

### Adding a New Enterprise Library

1. Place `.py` files in `backend/examples/your_library/`
2. Create a project in the UI pointing to that path
3. Click **Index Library** — the RAG engine will:
   - Parse files with AST
   - Extract class/method signatures
   - Generate embeddings
   - Store in FAISS index
4. New script generations for that project will use the library context

### Adding a New API Endpoint

1. Create router file in `backend/app/api/`
2. Define Pydantic schemas in `backend/app/models/schemas.py`
3. Register router in `backend/app/main.py`
4. Add endpoint to `src/services/api/config.ts`
5. Create API call in `src/services/api/client.ts`

### Adding a New Frontend View

1. Create component in `src/components/views/YourView.tsx`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/layout/Sidebar.tsx`

---

## 17. Troubleshooting

### Ollama Not Responding

```
Symptom: Connection overlay shows "Ollama: Offline"
```

**Fix:**
1. Verify Ollama is running: `curl http://localhost:11434/api/tags`
2. If not running: `ollama serve`
3. Check model is pulled: `ollama list` — should show `mistral:7b`
4. If model missing: `ollama pull mistral:7b`

### Script Generation Timeout

```
Symptom: "Generation failed" after 5 minutes
```

**Fix:**
1. Check Ollama logs for model loading issues
2. Ensure sufficient RAM (7B model needs ~8GB)
3. First generation after cold start is slow (model loading) — subsequent calls are faster
4. Backend timeout is 300s, frontend timeout is 310s — check `config.py` and `config.ts`

### Backend Won't Start

```
Symptom: Import errors or missing modules
```

**Fix:**
1. Ensure virtual environment is activated: `source venv/bin/activate`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (needs 3.10+)

### Frontend Shows "Backend Offline" But It's Running

```
Symptom: False-negative connection overlay
```

**Fix:**
1. Ensure backend is on `http://localhost:8000` (not `127.0.0.1:8000` — some browsers treat them differently)
2. If using the cloud preview (HTTPS), mixed content blocks HTTP calls. Use the **Connection Status Overlay** to set the backend URL
3. Check browser console for CORS errors

### Execution Fails: "Failed to Initialize Adapter"

**Fix:**
1. **Web:** Run `playwright install chromium` to install browsers
2. **Mobile:** Ensure Appium server is running at `http://localhost:4723` and device is connected
3. **STB:** Verify RedRat IP is reachable and HDMI capture device is connected

### STB: No Frame Captured

**Fix:**
1. Check HDMI capture index: `python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"`
2. Try different indices (0, 1, 2)
3. Ensure no other application is using the capture device

---

## 18. Best Practices

### Writing Effective Prompts

- **Be specific:** Include exact field names, button labels, and expected outcomes
- **Mention the flow:** Describe the user journey step by step
- **Include assertions:** State what should be verified ("verify the dashboard shows a welcome message")
- **For STB:** Mention specific menu names and expected screen elements

### Structuring Test Cases

- **One scenario per test:** Keep tests focused on a single user flow
- **Include setup/teardown:** Ensure tests start from a known state
- **Use descriptive names:** `"Login with valid credentials"` not `"Test 1"`

### Managing Libraries

- **Keep libraries updated:** Re-index after adding new methods
- **Add examples:** Place example test scripts alongside library files — the RAG engine uses them for few-shot prompting
- **Document methods:** Include docstrings with parameter descriptions — these get indexed

### Debugging Failures

1. **Read the AI analysis** in execution results — it provides root cause insights
2. **Check failure screenshots** for visual context
3. **Review step-by-step logs** to find exactly which step failed
4. **Edit and re-run** — modify the failing step in the editor and execute again

---

## License

This project is proprietary. See LICENSE file for details.

---

## Contributing

1. Create a feature branch from `main`
2. Follow existing code patterns and naming conventions
3. Add tests for new functionality
4. Update this README if adding new features or changing architecture
5. Submit a pull request with a clear description of changes

---

> **Built with ❤️ using React, FastAPI, Ollama, and FAISS — fully offline, fully yours.**
