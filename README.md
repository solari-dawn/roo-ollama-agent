# 🚀 Roo + Ollama Local Coding Agent

A local-first AI coding agent system combining:

- Ollama (GPU inference)
- LangChain + langchain-ollama (agent orchestration)
- FastAPI (execution API with auth)
- pytest (evaluation layer)
- VS Code Roo Code (UI agent interface)

Designed for dual RTX 3060 (12GB + 12GB) setups.

## 🧠 Architecture

```
                ┌──────────────────────┐
                │   VS Code (Roo)      │
                │  Agent UI Layer      │
                └─────────┬────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │   FastAPI Server     │
                │   /run endpoint      │
                │   X-API-Key auth     │
                └─────────┬────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
 ┌────────────────────┐        ┌────────────────────┐
 │ Planner Model      │        │ Executor Model     │
 │ deepseek-r1:14b    │        │ deepseek-coder     │
 └─────────┬──────────┘        └─────────┬──────────┘
           │                             │
           └────────────┬────────────────┘
                        ▼
               ┌─────────────────┐
               │   Ollama GPU    │
               │ RTX 3060 x2     │
               └─────────────────┘
```

## ⚙️ Features

- **🧠 Dual-model reasoning system**
  - Planner → structured step decomposition
  - Executor → code generation per step
- **🔐 API key authentication**
  - `X-API-Key` header required on all `/run` requests
  - Input validation and prompt injection blocking
- **🚀 GPU optimized**
  - 2 × RTX 3060 (12GB each)
  - No cloud dependency
- **⚡ Async execution**
  - LLM inference runs in thread pool via `run_in_executor`
  - FastAPI event loop never blocked
- **🗂️ Sandboxed file tools**
  - All agent file I/O jailed to `AGENT_WORKSPACE`
  - Path traversal blocked at resolution time
- **🧪 Built-in evaluation suite**
  - API tests including auth negative cases
  - Agent consistency tests
  - Structured logging across all layers
- **🔌 Roo integration ready**
  - Plug directly into Roo Code

## 📁 Project Structure

```
roo-ollama-agent/
├── app/
│   ├── agent.py          # Async planner/executor loop
│   ├── config.py         # Env config with fail-fast validation
│   ├── llm/
│   │   └── ollama.py     # (deprecated — superseded by agent.py)
│   └── tools/
│       └── fs.py         # Sandboxed file read/write/delete/list
├── server/
│   └── api.py            # FastAPI app with auth, validation, logging
├── tests/
│   ├── conftest.py       # Auto-loads .env before test collection
│   ├── test_api.py       # Endpoint + auth + validation tests
│   ├── test_agent.py     # Agent response structure tests
│   └── test_prompts.py   # Consistency tests
├── workspace/            # Agent file sandbox (auto-created)
├── .env.example
├── requirements.txt
├── pytest.ini
└── README.md
```

## ⚡ Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Update `.env`:
```
OLLAMA_BASE_URL=http://127.0.0.1:11434
PLANNER_MODEL=deepseek-r1:14b
EXECUTOR_MODEL=deepseek-coder:6.7b
TEMPERATURE=0.1
MAX_STEPS=5
API_KEY=your-secret-key-here
AGENT_WORKSPACE=./workspace
```

Generate a strong API key:
```powershell
[System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

### 3. Start Ollama

```bash
ollama serve
ollama pull deepseek-r1:14b
ollama pull deepseek-coder:6.7b
```

### 4. Run API

```bash
uvicorn server.api:app --reload --port 8000
```

### 5. Run tests

```powershell
# Windows — set key for the session
$env:API_KEY="your-secret-key-here"; pytest -v

# Or rely on conftest.py auto-loading .env (recommended)
pytest -v
```

## 🔐 Authentication

All `/run` requests require an `X-API-Key` header:

```bash
curl -X POST http://localhost:8000/run \
  -H "X-API-Key: your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a Python function to sort a list"}'
```

| Condition | Response |
|---|---|
| Missing key | 401 Unauthorized |
| Wrong key | 403 Forbidden |
| Task < 3 chars | 422 Unprocessable |
| Task > 2000 chars | 422 Unprocessable |
| Injection attempt | 422 Unprocessable |
| Valid request | 200 OK |

## 🔌 Roo Workflow (IMPORTANT)

This system is designed for agent-driven development inside VS Code.

### Step 1 — Connect Roo

In Roo settings:

```json
{
  "provider": "custom",
  "endpoint": "http://127.0.0.1:8000/run",
  "headers": {
    "X-API-Key": "your-secret-key-here"
  }
}
```

### Step 2 — Recommended workflow

**🧠 1. Ask for plan only**
```
Design a FastAPI authentication system
```

**🧠 2. Review plan**

Ensure:
- Steps are clear
- No ambiguity

**💻 3. Execute step-by-step**
```
Implement step 1 only
Implement step 2 only
```

**🔁 4. Iterate**

Fix issues progressively rather than full generation.

### ⚠️ Anti-patterns (avoid)

- ❌ "Build entire app" in one prompt
- ❌ No step control
- ❌ No review loop
- ❌ Sending API key in plaintext logs or version control

## 🗂️ File Tool Sandbox

The agent's file tools (`read_file`, `write_file`, `delete_file`, `list_files`) are restricted to `AGENT_WORKSPACE`. Any path that resolves outside the workspace is blocked.

```
AGENT_WORKSPACE=./workspace   # set in .env
```

All file operations are logged with the resolved absolute path. Path traversal attempts (e.g. `../../etc/passwd`) are blocked and logged as warnings.

## 🧪 Testing Strategy

Tests cover both behavior and security boundaries.

| Test | Purpose |
|---|---|
| `test_health` | Endpoint availability |
| `test_run_endpoint` | Valid authenticated request → 200 |
| `test_run_rejects_no_key` | Missing auth → 401 |
| `test_run_rejects_bad_key` | Wrong key → 403 |
| `test_run_rejects_short_task` | Input too short → 422 |
| `test_run_rejects_injection` | Prompt injection → 422 |
| `test_prime_task` | Agent response structure |
| `test_consistency` | Output overlap across two runs |

`tests/conftest.py` auto-loads `.env` before collection — no manual export required.

## 🔄 CI Pipeline (GitHub Actions)

`.github/workflows/tests.yml`:

```yaml
name: Agent Tests

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        env:
          API_KEY: ${{ secrets.API_KEY }}
          OLLAMA_BASE_URL: http://localhost:11434
          PLANNER_MODEL: deepseek-r1:14b
          EXECUTOR_MODEL: deepseek-coder:6.7b
        run: pytest -v
```

> Note: Integration tests (`test_agent`, `test_prompts`) require a running Ollama instance. In CI without Ollama, only `test_api` auth/validation tests will pass. Use mock-based unit tests for pure CI coverage.

## 🧠 Design Philosophy

1. **Deterministic-first agent design**
   - Low temperature for stable outputs

2. **Planner/Executor separation**
   - Prevents local model confusion

3. **Small-step execution**
   - Avoids hallucinated full-code dumps

4. **GPU-aware inference**
   - 14B → reasoning
   - 6–7B → coding

5. **Async-first API**
   - LLM calls run in thread pool, event loop stays free

6. **Fail-fast config**
   - Missing env vars raise at startup, not at request time

## ⚠️ Known Limitations

- No true multi-GPU model sharding in Ollama
- Planner may still over-explain on simple tasks
- Large models (26B/32B) are not recommended
- Requires structured prompting discipline
- Integration tests require a live Ollama instance

## 🚀 Roadmap

### Phase 1 ✅ (current)
- Basic agent loop
- API key authentication
- Input validation + injection blocking
- Async execution
- Sandboxed file tools
- Test suite (auth + behavior)
- Roo integration

### Phase 2
- Tool execution (git, terminal)
- Structured JSON planning output
- Per-agent rate limiting

### Phase 3
- Multi-agent system (architect / coder / reviewer)
- Streaming responses
- Roo-native IDE behavior

## 📌 Status

- ✔ API working with auth
- ✔ Agent functional (async)
- ✔ GPU inference active
- ✔ Test suite: 8/8 passing
- ✔ File tools sandboxed
- ✔ Input validation active
- ⚠ Prompt tuning ongoing
