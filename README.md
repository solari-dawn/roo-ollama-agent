# 🚀 Roo + Ollama Local Coding Agent

A local-first AI coding agent system combining:

- Ollama (GPU inference, remote machine)
- LangChain + langchain-community (agent orchestration)
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
                ┌───────────────────────┐
                │   FastAPI Server      │  
                │   /run                │
                │   /v1/chat/completions│
                │   X-API-Key | Bearer  │
                └─────────┬─────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
 ┌────────────────────┐        ┌────────────────────┐
 │ Planner Model      │        │ Executor Model     │
 │ deepseek-r1:7b     │        │ qwen2.5-coder:7b   │
 └─────────┬──────────┘        └─────────┬──────────┘
           │                             │
           └────────────┬────────────────┘
                        ▼
               ┌─────────────────┐
               │   Ollama GPU    │  ← runs on remote
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
- **🔌 Dual endpoints**
  - `/run` — native Bot Army API
  - `/v1/chat/completions` — OpenAI-compatible with streaming + tool call interception
- **🚀 GPU optimized**
  - 2 × RTX 3060 (12GB each)
  - No cloud dependency
- **⚡ Sync execution via FastAPI threadpool**
  - LangChain LLM calls are synchronous; FastAPI runs them in a thread pool automatically
- **🧪 Built-in evaluation suite**

## 📁 Project Structure

```
roo-ollama-agent/
├── app/
│   ├── agent.py          # Planner/executor loop (sync)
│   ├── config.py         # Env config
│   ├── llm/
│   │   ├── __init__.py
│   │   └── ollama.py     # LangChain Ollama wrapper
│   └── tools/
│       └── fs.py         # File read/write tools
├── server/
│   └── api.py            # FastAPI — /run + /v1/chat/completions + /v1/models
├── tests/
│   ├── test_api.py
│   ├── test_agent.py
│   └── test_prompts.py
├── workspace/
├── .env
├── .env.example
├── .roo-config.json
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

`.env` must contain:
```
OLLAMA_BASE_URL=http://[ollama-server]]:11434
PLANNER_MODEL=deepseek-r1:7b
EXECUTOR_MODEL=qwen2.5-coder:7b
TEMPERATURE=0.1
MAX_STEPS=5
API_KEY=your-secret-key-here
AGENT_WORKSPACE=./workspace
OPENAI_BASE_URL=http://127.0.0.1:8000/v1
OPENAI_API_KEY=your-secret-key-here
```

> ⚠️ `OLLAMA_BASE_URL` must point to the remote Ollama machine IP, not localhost. FastAPI runs on PCJT; Ollama runs on the remote GPU machine.

Generate a strong API key:
```powershell
[System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

### 3. Confirm models are available on Ollama machine

```powershell
curl http://[ollama-server]:11434/api/tags
```

Required models:
- `deepseek-r1:7b` (planner)
- `qwen2.5-coder:7b` (executor)

If missing, on the Ollama machine:
```bash
ollama pull deepseek-r1:7b
ollama pull qwen2.5-coder:7b
```

### 4. Ensure Python package structure is intact

The following `__init__.py` files must exist:
```
app/__init__.py
app/llm/__init__.py
```

Create if missing:
```powershell
New-Item -Path "app/__init__.py" -ItemType File -Force
New-Item -Path "app/llm/__init__.py" -ItemType File -Force
```

### 5. Run API

```powershell
uvicorn server.api:app --port 8000
```

> Do NOT use `--reload` in production — it can cause issues with LangChain model initialisation on file change.

### 6. Run tests

```powershell
pytest -v
```

## 🔐 Authentication

All `/run` and `/v1/chat/completions` requests require a valid key:

```bash
# X-API-Key (native)
curl -X POST http://localhost:8000/run \
  -H "X-API-Key: your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a Python sort function"}'

# Authorization: Bearer (Roo / OpenAI-compatible clients)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer your-secret-key-here" \
  -H "Content-Type: application/json" \
  -d '{"model":"bot-army","messages":[{"role":"user","content":"Write a Python sort function"}],"stream":false}'
```

## 🔌 Roo Code Setup

Install Roo Code extension: `ext install RooVeterinaryInc.roo-cline`

### VS Code `settings.json`

Located at `C:\Users\<user>\AppData\Roaming\Code\User\settings.json`:

```json
"roo-cline.openaiBaseUrl": "http://127.0.0.1:8000/v1",
"roo-cline.openaiApiKey": "your-secret-key-here",
"roo-cline.model": "bot-army",
"roo-cline.requestTimeout": 120000
```

> ⚠️ Set `requestTimeout` to at least 120000 (120 seconds). The planner + executor pipeline takes 20–60 seconds per request depending on model load and GPU memory availability.

### `.roo-config.json` (project root)

```json
{
  "provider": "openai-compatible",
  "openai": {
    "baseUrl": "http://127.0.0.1:8000/v1",
    "apiKey": "your-secret-key-here"
  },
  "model": "bot-army"
}
```

### How Roo integrates

Roo sends requests to `/v1/chat/completions`. The FastAPI server:
1. Extracts the last user message as the task
2. Runs the planner (deepseek-r1:7b) to generate steps
3. Runs the executor (qwen2.5-coder:7b) on each step
4. Returns the combined result

If Roo sends tool definitions (e.g. `attempt_completion`), the server wraps the response as a tool call so Roo's protocol is satisfied.

Streaming is supported — the server detects `"stream": true` and returns SSE format.

## ⚠️ Known Issues & Fixes

### OllamaEndpointNotFoundError 404
Model not available on Ollama machine. Run `curl http://ollama-server:11434/api/tags` to check available models and update `.env` accordingly.

### `ModuleNotFoundError: No module named 'app.llm.ollama'`
Missing `__init__.py` files. See step 4 of Quick Start.

### `coroutine object is not JSON serializable`
`run_agent` was defined as `async def`. All functions in `app/agent.py` must be plain `def` — FastAPI handles threading automatically for sync functions.

### Roo error: "did not provide any assistant messages"
Caused by Roo's OpenAI provider expecting streaming SSE format. Ensure `server/api.py` handles `"stream": true` with `StreamingResponse`.

### Roo error: "did not call any of the required tools"
Roo sends tool schemas and expects tool call responses. Ensure `server/api.py` detects `attempt_completion` in the tools list and wraps the response as a tool call.

### GPU memory eviction between requests
Both models cannot stay resident simultaneously on 2×12GB with full KV cache. Ollama evicts and reloads between planner and executor calls — adds ~4 seconds per request. Expected behaviour.

## 🧪 Testing

```powershell
pytest -v
```

Integration tests require live Ollama at `ollama-server:11434` with models loaded.

## 📌 Status

- ✔ API operational — `/run` + `/v1/chat/completions` + `/v1/models`
- ✔ Auth — X-API-Key + Bearer
- ✔ Streaming — SSE format supported
- ✔ Tool call interception — `attempt_completion` wrapping
- ✔ Agent functional (sync, FastAPI threadpool)
- ✔ GPU inference active (RTX 3060 ×2, remote Ollama)
- ✔ Roo Code configured
- ⚠ Models: deepseek-r1:14b and deepseek-coder:6.7b not currently on Ollama machine — using deepseek-r1:7b + qwen2.5-coder:7b
- ⚠ Prompt tuning ongoing
