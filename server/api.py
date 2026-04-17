from fastapi import FastAPI
from pydantic import BaseModel
from app.agent import run_agent

app = FastAPI()

class TaskRequest(BaseModel):
    task: str

@app.post("/run")
async def run(req: TaskRequest):
    return {
        "result": run_agent(req.task)
    }