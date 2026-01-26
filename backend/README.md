# GenAI Automation Framework - Python Backend

Local-first automation framework with RAG-powered script generation.

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Ollama installed and running locally
- ADB (for Android testing) or libimobiledevice (for iOS testing)

### 2. Installation

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium firefox webkit
```

### 3. Configure Ollama

```bash
# Start Ollama (in a separate terminal)
ollama serve

# Pull a model (7B recommended for local use)
ollama pull mistral:7b
# or
ollama pull llama3:8b
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Run the Server

```bash
# Development mode with hot reload
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Production mode
python -m app.main
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── main.py             # FastAPI application
│   ├── api/                # API routers
│   │   ├── devices.py      # Device validation (MTK Connect)
│   │   ├── executions.py   # Test execution & history
│   │   ├── projects.py     # Project CRUD
│   │   ├── scripts.py      # Script generation (RAG + Ollama)
│   │   └── system.py       # Health checks
│   ├── models/             # Database & Pydantic models
│   │   ├── database.py     # SQLAlchemy models
│   │   └── schemas.py      # API schemas (SRS Section 7)
│   └── services/           # Business logic
│       ├── automation_adapters.py  # Playwright/Appium
│       ├── execution_service.py    # Execution orchestration
│       ├── mtk_connect.py          # Device bridge
│       ├── ollama_client.py        # LLM client
│       ├── rag_engine.py           # RAG + Code Guardrail
│       └── script_generator.py     # Generation orchestration
├── data/                   # SQLite DB & FAISS indexes
├── projects/               # Project artifacts
├── requirements.txt
└── .env.example
```

## API Endpoints

### Projects
- `GET /projects/` - List all projects
- `POST /projects/` - Create project
- `GET /projects/{id}` - Get project
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project
- `POST /projects/{id}/index` - Index library for RAG

### Devices
- `POST /devices/validate` - Validate device connection
- `GET /devices/` - List connected devices

### Script Generation
- `POST /scripts/generate` - Generate test script with RAG
- `POST /scripts/save` - Save test case
- `GET /scripts/test-cases/{id}` - Get test case
- `POST /scripts/analyze-failure` - AI failure analysis

### Executions
- `POST /executions/` - Execute test case
- `GET /executions/` - List execution history
- `GET /executions/{id}` - Get execution result
- `GET /executions/active/list` - List running executions
- `WS /executions/ws/{id}` - Real-time execution updates

### System
- `GET /system/health` - Health check
- `GET /system/status` - Detailed system status
- `GET /system/config` - Non-sensitive config

## Execution Result Schema (SRS Section 7)

```json
{
  "execution_id": "uuid",
  "status": "PASS | FAIL | WARNING",
  "test_name": "string",
  "project_name": "string",
  "metrics": {
    "total_duration": 12.4,
    "avg_response_time": 0.3,
    "step_success_rate": 100
  },
  "steps": [
    {"action": "string", "result": true, "latency": 150, "error": null}
  ],
  "artifacts": {
    "video_path": "string",
    "screenshot_failure": null
  },
  "ai_analysis": "string",
  "created_at": "datetime"
}
```

## Security Features

- **Code Guardrail**: All generated scripts are validated with AST parsing
- **Forbidden Imports**: `os`, `subprocess`, `sys`, `shutil`, `socket`, `requests`
- **No External API Calls**: 0.0.0.0/0 restricted (local-first)
- **Project Isolation**: RBAC at folder level

## Development

```bash
# Run tests
pytest

# Type checking
mypy app/

# Format code
black app/
```
