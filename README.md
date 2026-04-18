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
                │   /run              │
                │   /v1/chat/completions│
                │   X-API-Key | Bearer │
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
- **🔐 Dual-header authentication**
  - `X-API-Key` header (native clients, curl, tests)
  - `Authorization: Bearer` (Roo Code, OpenAI-compatible clients)
  - Input validation and prompt injection blocking
- **🔌 Dual endpoints**
  - `/run` — native Bot Army API
  - `/v1/chat/completions` — OpenAI-compatible (Roo Code, Continue, Cursor)
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
  - 14 tests covering auth, validation, agent behavior, and OpenAI-compat
  - Structured logging across all layers
- **🔌 Roo integration ready**
  - Bot Army profile for structured tasks
  - Ollama direct profile for interactive chat

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
│   └── api.py            # FastAPI app — /run + /v1/chat/completions
├── tests/
│   ├── conftest.py       # Auto-loads .env before test collection
│   ├── test_api.py       # 11 endpoint/auth/validation tests
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
OLLAMA_BASE_URL=http://192.168.2.10:11434
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
# Set key for the session then run
$env:API_KEY="your-secret-key-here"; pytest -v

# Or rely on conftest.py auto-loading .env
pytest -v
```

## 🔐 Authentication

All `/run` and `/v1/chat/completions` requests require a valid key via either header:

```bash
# X-API-Key (native)
curl -X POST http://localhost:8000/run \
  -H "X-API-Key: your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a Python sort function"}'

# Authorization: Bearer (OpenAI-compatible clients)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"model":"bot-army","messages":[{"role":"user","content":"Write a Python sort function"}]}'
```

| Condition | Response |
|---|---|
| Missing key | 403 Forbidden |
| Wrong key | 403 Forbidden |
| Task < 3 chars | 422 Unprocessable |
| Task > 2000 chars | 422 Unprocessable |
| Injection attempt | 422 Unprocessable |
| Valid request | 200 OK |

## 🔌 Roo Code Setup

Install the **Roo Code** extension in VS Code (`ext install RooVeterinaryInc.roo-cline`).

Configure two profiles via Roo Code settings → **OpenAI Compatible**:

### Profile 1 — Bot Army (structured multi-step tasks)

```
Provider:  OpenAI Compatible
Base URL:  http://192.168.2.10:8000
API Key:   your-secret-key-here
Model ID:  bot-army
```

Roo posts to `/v1/chat/completions` using `Authorization: Bearer`. The server extracts the task from the last user message and runs the full planner/executor pipeline.

### Profile 2 — Ollama Direct (interactive chat)

```
Provider:  OpenAI Compatible
Base URL:  http://192.168.2.10:11434
API Key:   ollama
Model ID:  deepseek-r1:14b
```

Bypasses the agent pipeline. Ollama's API is natively OpenAI-compatible. Use `deepseek-coder:6.7b` for faster interactive responses.

Switch profiles via the model selector in the Roo Code top bar.

### Recommended workflow

**🧠 Bot Army — structured tasks**
```
Design a FastAPI authentication system
Implement step 1 only
Implement step 2 only
```

**💻 Ollama Direct — interactive**
```
Explain this function
What does this regex do
Fix this syntax error
```

### ⚠️ Anti-patterns

- ❌ "Build entire app" in one Bot Army prompt
- ❌ No step review between executor runs
- ❌ API key in version control or logs

## 🗂️ File Tool Sandbox

The agent's file tools (`read_file`, `write_file`, `delete_file`, `list_files`) are restricted to `AGENT_WORKSPACE`. Any path resolving outside the workspace is blocked and logged.

```
AGENT_WORKSPACE=./workspace   # set in .env
```

## 🧪 Testing

| Test | Purpose |
|---|---|
| `test_health` | Docs endpoint reachable |
| `test_run_accepts_api_key_header` | X-API-Key auth → 200 |
| `test_run_rejects_no_key` | Missing key → 403 |
| `test_run_rejects_bad_key` | Wrong key → 403 |
| `test_run_accepts_bearer_token` | Bearer auth → 200 |
| `test_run_rejects_bad_bearer` | Wrong Bearer → 403 |
| `test_run_rejects_short_task` | < 3 chars → 422 |
| `test_run_rejects_long_task` | > 2000 chars → 422 |
| `test_run_rejects_injection` | Injection phrase → 422 |
| `test_openai_compat_returns_choices` | /v1/chat/completions response structure |
| `test_openai_compat_rejects_no_key` | Unauthenticated compat request → 403 |
| `test_openai_compat_rejects_no_user_message` | No user role → 400 |
| `test_prime_task` | Agent returns valid result |
| `test_consistency` | Two runs share significant token overlap |

`tests/conftest.py` auto-loads `.env` — no manual export required.

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

> Integration tests (`test_agent`, `test_prompts`, `test_openai_compat_returns_choices`) require a live Ollama instance. In CI without Ollama, the remaining 11 auth/validation tests will pass.

## 🧠 Design Philosophy

1. **Deterministic-first** — low temperature for stable, reproducible outputs
2. **Planner/Executor separation** — prevents local model confusion on complex tasks
3. **Small-step execution** — avoids hallucinated full-code dumps
4. **GPU-aware inference** — 14B for reasoning, 6–7B for coding
5. **Async-first API** — LLM calls in thread pool, event loop never blocked
6. **Fail-fast config** — missing env vars raise at startup, not at request time
7. **Standards-compatible** — OpenAI endpoint format works with any compatible client

## ⚠️ Known Limitations

- No true multi-GPU model sharding in Ollama
- Planner may over-explain on simple tasks
- Large models (26B/32B) not recommended
- Integration tests require a live Ollama instance
- No streaming support (planned Phase 2)

## 🚀 Roadmap

### Phase 1 ✅ (complete)
- Basic agent loop
- API key authentication (X-API-Key + Bearer)
- OpenAI-compatible `/v1/chat/completions` endpoint
- Input validation + injection blocking
- Async execution
- Sandboxed file tools
- 14-test suite
- Roo Code dual-profile integration

### Phase 2
- Tool execution (git, terminal)
- Structured JSON planning output
- Streaming responses
- Per-agent rate limiting

### Phase 3
- Multi-agent system (architect / coder / reviewer)
- Roo-native IDE behavior

## 📌 Status

- ✔ API operational — dual endpoints
- ✔ Auth — X-API-Key + Bearer
- ✔ Agent functional (async)
- ✔ GPU inference active (RTX 3060 ×2)
- ✔ Tests: 14/14 passing
- ✔ File tools sandboxed
- ✔ Roo Code configured — Bot Army + Ollama Direct profiles
- ⚠ Prompt tuning ongoing
