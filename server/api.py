import os
import time
import uuid
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from app.agent import run_agent

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("api")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise EnvironmentError("Missing required environment variable: API_KEY")

# auto_error=False — disables FastAPI's automatic 401 rejection so verify_key
# can inspect both X-API-Key and Authorization: Bearer before deciding
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Bot Army Agent API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

# ---------------------------------------------------------------------------
# Auth — accepts X-API-Key header OR Authorization: Bearer
# ---------------------------------------------------------------------------
async def verify_key(
    request: Request,
    key: Optional[str] = Security(api_key_header),
) -> str:
    # Priority 1: X-API-Key header (native clients, curl, tests)
    resolved = key

    # Priority 2: Authorization: Bearer (Roo Code, OpenAI-compatible clients)
    if not resolved:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            resolved = auth.removeprefix("Bearer ").strip()

    if not resolved or resolved != API_KEY:
        logger.warning("Rejected request — invalid API key")
        raise HTTPException(status_code=403, detail="Forbidden")

    return resolved

# ---------------------------------------------------------------------------
# Schemas — native endpoint
# ---------------------------------------------------------------------------
_BLOCKED_PHRASES = [
    "ignore all",
    "ignore previous",
    "system prompt",
    "jailbreak",
    "disregard",
    "forget your instructions",
]

class TaskRequest(BaseModel):
    task: str

    @field_validator("task")
    @classmethod
    def validate_task(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Task too short (min 3 chars)")
        if len(v) > 2000:
            raise ValueError("Task exceeds 2000 character limit")
        lower = v.lower()
        for phrase in _BLOCKED_PHRASES:
            if phrase in lower:
                raise ValueError(f"Blocked content detected: '{phrase}'")
        return v

class TaskResponse(BaseModel):
    result: str

# ---------------------------------------------------------------------------
# Schemas — OpenAI-compatible endpoint
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: Optional[str] = "bot-army"
    messages: list[ChatMessage]

# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok"}


@app.post("/run", response_model=TaskResponse, tags=["agent"])
async def run(req: TaskRequest, _: str = Security(verify_key)):
    logger.info(f"Task received ({len(req.task)} chars): {req.task[:80]}...")
    try:
        result = await run_agent(req.task)
    except RuntimeError as e:
        logger.error(f"Agent runtime error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    logger.info("Task complete")
    return TaskResponse(result=result)


@app.post("/v1/chat/completions", tags=["openai-compat"])
async def chat_completions(req: ChatRequest, _: str = Security(verify_key)):
    user_messages = [m for m in req.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")

    task = user_messages[-1].content.strip()
    logger.info(f"[openai-compat] Task received ({len(task)} chars): {task[:80]}...")

    if len(task) < 3:
        raise HTTPException(status_code=422, detail="Task too short (min 3 chars)")
    if len(task) > 2000:
        raise HTTPException(status_code=422, detail="Task exceeds 2000 character limit")
    for phrase in _BLOCKED_PHRASES:
        if phrase in task.lower():
            raise HTTPException(status_code=422, detail="Blocked content detected")

    try:
        result = await run_agent(task)
    except RuntimeError as e:
        logger.error(f"[openai-compat] Agent runtime error: {e}")
        raise HTTPException(status_code=503, detail=str(e))

    logger.info("[openai-compat] Task complete")

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": result
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(task.split()),
            "completion_tokens": len(result.split()),
            "total_tokens": len(task.split()) + len(result.split())
        }
    }
