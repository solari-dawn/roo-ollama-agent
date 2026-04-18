import time
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from app.agent import run_agent

app = FastAPI()


class TaskRequest(BaseModel):
    task: str


@app.post("/run")
def run(req: TaskRequest):
    result = run_agent(req.task)
    return {"result": result}


@app.post("/v1/chat/completions")
def openai_compat(req: dict):
    messages = req.get("messages", [])
    tools = req.get("tools", [])
    stream = req.get("stream", False)

    task = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        ""
    )

    result = run_agent(task)

    # Check if Roo sent tools - if so, wrap response as attempt_completion tool call
    tool_names = [t.get("function", {}).get("name", "") for t in tools]
    use_tool_call = "attempt_completion" in tool_names

    def make_message():
        if use_tool_call:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_botarmy",
                        "type": "function",
                        "function": {
                            "name": "attempt_completion",
                            "arguments": json.dumps({"result": result})
                        }
                    }
                ]
            }
        return {"role": "assistant", "content": result}

    if stream:
        def generate():
            msg = make_message()
            if use_tool_call:
                chunk = {
                    "id": "chatcmpl-botarmy",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": req.get("model", "bot-army"),
                    "choices": [{"index": 0, "delta": msg, "finish_reason": None}]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                done = {
                    "id": "chatcmpl-botarmy",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": req.get("model", "bot-army"),
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]
                }
            else:
                chunk = {
                    "id": "chatcmpl-botarmy",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": req.get("model", "bot-army"),
                    "choices": [{"index": 0, "delta": msg, "finish_reason": None}]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                done = {
                    "id": "chatcmpl-botarmy",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": req.get("model", "bot-army"),
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                }
            yield f"data: {json.dumps(done)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    msg = make_message()
    finish = "tool_calls" if use_tool_call else "stop"
    return JSONResponse(content={
        "id": "chatcmpl-botarmy",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.get("model", "bot-army"),
        "choices": [{"index": 0, "message": msg, "finish_reason": finish}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    })


@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "bot-army", "object": "model", "owned_by": "local"}
        ]
    }
