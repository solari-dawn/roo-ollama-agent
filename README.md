# 🚀 Roo + Ollama Local Coding Agent

A local-first AI coding agent system combining:

- Ollama (GPU inference)
- LangChain (agent orchestration)
- FastAPI (execution API)
- pytest (evaluation layer)
- VS Code Roo Code (UI agent interface)

Designed for dual RTX 3060 (12GB + 12GB) setups.

## 🧠 Architecture

High-level system flow:

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
  - Planner → structured decomposition
  - Executor → code generation
- **🚀 GPU optimized**
  - 2 × RTX 3060 (12GB each)
  - No cloud dependency
- **🧪 Built-in evaluation suite**
  - API tests
  - Agent consistency tests
  - Regression checks
- **🔌 Roo integration ready**
  - Plug directly into Roo Code

## 📁 Project Structure

```
roo-ollama-agent/
├── app/
│   ├── agent.py
│   ├── config.py
│   ├── llm/
│   └── tools/
├── server/
│   └── api.py
├── tests/
│   ├── test_api.py
│   ├── test_agent.py
│   └── test_prompts.py
├── .env.example
├── requirements.txt
├── requirements-tests.txt
├── pytest.ini
└── README.md
```

## ⚡ Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-tests.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Update `.env`:
```
OLLAMA_BASE_URL=http://localhost:11434
PLANNER_MODEL=deepseek-r1:14b
EXECUTOR_MODEL=deepseek-coder:6.7b
TEMPERATURE=0.1
MAX_STEPS=5
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

```bash
pytest -v
```

## 🔌 Roo Workflow (IMPORTANT)

This system is designed for agent-driven development inside VS Code.

### Step 1 — Connect Roo

In Roo settings:

```json
{
  "provider": "custom",
  "endpoint": "http://127.0.0.1:8000/run"
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

## 🧪 Testing Strategy

We test behavior, not correctness.

| Test | Purpose |
|------|---------|
| API test | endpoint stability |
| Agent test | response structure |
| Consistency test | hallucination drift |

Run:
```bash
pytest -v
```

## 🔄 CI Pipeline (GitHub Actions)

Create `.github/workflows/tests.yml`:

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
          python-version: "3.10"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-tests.txt

      - name: Run tests
        run: pytest -v
```

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

## ⚠️ Known limitations

- No true multi-GPU model sharding in Ollama
- Planner may still over-explain
- Large models (26B/32B) are not recommended
- Requires structured prompting discipline

## 🚀 Roadmap

### Phase 1 (current)
- Basic agent loop
- Test suite
- Roo integration

### Phase 2
- Tool execution (files, git, terminal)
- Structured JSON planning

### Phase 3
- Multi-agent system (architect / coder / reviewer)
- Streaming responses
- Roo-native IDE behavior

## 🧠 Why this works

This system turns local LLMs into:
- A controllable, testable, GPU-accelerated coding agent

Instead of:
- Chat-only systems
- Uncontrolled generation loops
- Cloud dependency agents

## 📌 Status

- ✔ API working
- ✔ Agent functional
- ✔ GPU inference active
- ✔ Test suite integrated
- ⚠ Prompt tuning ongoing
