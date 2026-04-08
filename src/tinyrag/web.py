from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import RagConfig
from .runtime import RagRuntime


ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT_DIR / "web"

load_dotenv(override=True)

app = FastAPI(title="TinyRag Web")
app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(min_length=1, max_length=120)
    debug: bool = False


class SessionResetRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=120)


def _sse_payload(data: dict) -> str:
    return "data: {0}\n\n".format(json.dumps(data, ensure_ascii=False))


_runtime_lock = Lock()
_cached_runtime = None
_cached_signature = None


def _config_signature(config: RagConfig):
    return (
        str(config.knowledge_path),
        config.embedding_model_name,
        config.embedding_device,
        config.chunk_size,
        config.chunk_overlap,
        config.retriever_k,
        config.temperature,
        config.llm_provider,
        config.ollama_model,
        config.ollama_base_url,
        config.deepseek_model,
        config.deepseek_base_url,
        config.deepseek_api_key,
    )


def get_runtime() -> RagRuntime:
    global _cached_runtime
    global _cached_signature

    load_dotenv(override=True)
    config = RagConfig.from_env()
    signature = _config_signature(config)

    with _runtime_lock:
        if _cached_runtime is None or signature != _cached_signature:
            _cached_runtime = RagRuntime(config)
            _cached_signature = signature
        return _cached_runtime


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/test-markdown")
def test_markdown() -> FileResponse:
    return FileResponse(WEB_DIR / "test-markdown.html")


@app.get("/chat")
def chat() -> FileResponse:
    return FileResponse(WEB_DIR / "chat.html")


@app.get("/api/health")
def health() -> dict:
    runtime = get_runtime()
    status = runtime.get_status()
    status["status"] = "ok"
    return status


@app.post("/api/session/reset")
def reset_session(payload: SessionResetRequest) -> dict:
    runtime = get_runtime()
    runtime.reset_session(payload.session_id.strip())
    return {"status": "ok", "session_id": payload.session_id.strip()}


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空。")

    try:
        result = get_runtime().invoke(question, session_id=payload.session_id, debug=payload.debug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="RAG 调用失败: {0}".format(exc)) from exc

    return result


@app.post("/api/chat/stream")
def chat_stream(payload: ChatRequest) -> StreamingResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空。")

    runtime = get_runtime()
    try:
        stream = runtime.stream(question, session_id=payload.session_id, debug=payload.debug)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="RAG 初始化失败: {0}".format(exc)) from exc

    def event_stream():
        for event in stream:
            yield _sse_payload(event)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
