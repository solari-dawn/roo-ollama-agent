from app.llm.ollama import get_llm
from app.config import PLANNER_MODEL, EXECUTOR_MODEL, MAX_STEPS

planner = get_llm(PLANNER_MODEL)
executor = get_llm(EXECUTOR_MODEL)

def create_plan(task: str) -> str:
    prompt = f"""
You are a senior software architect.

Return ONLY a numbered list of steps.

Rules:
- No explanations
- No markdown
- No headers
- One step per line
- Steps must be executable

Task:
{task}
"""
    return planner.invoke(prompt)

def execute_step(step: str) -> str:
    prompt = f"""
You are a senior software engineer.

Execute this step carefully:
{step}
"""
    return executor.invoke(prompt)

def run_agent(task: str) -> str:
    plan = create_plan(task)
    steps = [s for s in plan.split("\n") if s.strip()]
    results = []
    for i, step in enumerate(steps[:MAX_STEPS]):
        result = execute_step(step)
        results.append(f"Step {i+1}: {step}\n{result}")
    return "\n\n".join(results)
