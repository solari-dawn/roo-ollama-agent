import os
import time
import uuid
import logging
from typing import Optional, List, Any

from fastapi import FastAPI, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.agent import run_agent

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY not set")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# ---------------------------------------------------------------------
# App
# ---------------------------------------------------------------------
app = FastAPI()

# ---------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------
async def verify_key(request: Request, key: Optional[str] = Security(api_key_header)):
    resolved = key

    if not resolved:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            resolved = auth.replace("Bearer ", "").strip()

    if resolved != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    return resolved

# ---------------------------------------------------------------------
# Models (VERY relaxed for Roo)
# ---------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str
    content: Optional[Any] = None
    model_config = ConfigDict(extra="allow")

class ChatRequest(BaseModel):
    model: Optional[str] = "bot-army"
    messages: List[ChatMessage] = []
    model_config = ConfigDict(extra="allow")

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        return "\n".join(parts)

    return ""

# ---------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# ---------------------------------------------------------------------
# OpenAI-compatible endpoint (STRICT + SAFE)
# ---------------------------------------------------------------------
@app.post("/v1/chat/completions")
async def chat(req: ChatRequest, _: str = Security(verify_key)):

    # Extract task
    user_msgs = [m for m in req.messages if m.role == "user"]

    if user_msgs:
        task = extract_text(user_msgs[-1].content).strip()
    else:
        task = "\n".join(extract_text(m.content) for m in req.messages).strip()

    if not task:
        task = "Hello"

    logger.info(f"Task: {task[:80]}")

    # Run agent
    try:
        result = await run_agent(task)
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        result = "Error running agent."

    # 🚨 HARD GUARANTEE STRING
    if not isinstance(result, str):
        result = str(result)

    result = result.strip()

    if not result:
        result = "Hello."

    # 🚨 FORCE EXACT JSON RESPONSE (this is the critical part)
    response = {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model or "bot-army",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result
                },
                "finish_reason": "stop"
            }
        ]
    }

    return JSONResponse(content=response)