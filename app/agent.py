import asyncio
import logging
from functools import partial

from langchain_ollama import OllamaLLM
from app.config import OLLAMA_BASE_URL, PLANNER_MODEL, EXECUTOR_MODEL, TEMPERATURE, MAX_STEPS

logger = logging.getLogger("agent")

# ---------------------------------------------------------------------------
# Models — instantiated once at import time
# ---------------------------------------------------------------------------
planner = OllamaLLM(
    model=PLANNER_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=TEMPERATURE,
)

executor = OllamaLLM(
    model=EXECUTOR_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=TEMPERATURE,
)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
PLAN_PROMPT = """You are a senior software architect.

Return ONLY a numbered list of steps.

Rules:
- No explanations
- No markdown
- No headers
- One step per line
- Steps must be executable

Task:
{task}"""

EXEC_PROMPT = """You are a senior software engineer.

Execute this step carefully:
{step}"""

# ---------------------------------------------------------------------------
# Sync inference helpers (run inside executor thread)
# ---------------------------------------------------------------------------
def _create_plan(task: str) -> str:
    return planner.invoke(PLAN_PROMPT.format(task=task))

def _execute_step(step: str) -> str:
    return executor.invoke(EXEC_PROMPT.format(step=step))

# ---------------------------------------------------------------------------
# Public async entrypoint
# ---------------------------------------------------------------------------
async def run_agent(task: str) -> str:
    loop = asyncio.get_event_loop()

    try:
        plan: str = await loop.run_in_executor(None, partial(_create_plan, task))
        logger.info(f"Plan generated — {len(plan.splitlines())} lines")
    except Exception as e:
        logger.error(f"Planner failed: {e}")
        raise RuntimeError(f"Planner model unavailable: {e}") from e

    steps = [s.strip() for s in plan.splitlines() if s.strip()]
    results = []

    for i, step in enumerate(steps[:MAX_STEPS]):
        try:
            result: str = await loop.run_in_executor(None, partial(_execute_step, step))
            results.append(f"Step {i+1}: {step}\n{result}")
            logger.info(f"Step {i+1}/{min(len(steps), MAX_STEPS)} complete")
        except Exception as e:
            logger.error(f"Step {i+1} failed: {e}")
            results.append(f"Step {i+1}: FAILED — {e}")

    return "\n\n".join(results)
