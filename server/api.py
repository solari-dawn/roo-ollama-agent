import os
import logging
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

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

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
# Auth
# ---------------------------------------------------------------------------
async def verify_key(key: str = Security(api_key_header)) -> str:
    if key != API_KEY:
        logger.warning("Rejected request — invalid API key")
        raise HTTPException(status_code=403, detail="Forbidden")
    return key

# ---------------------------------------------------------------------------
# Schema
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