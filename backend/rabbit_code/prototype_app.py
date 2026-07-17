from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from prompt_optimizer.providers.base import ModelProvider, ModelRequest
from prompt_optimizer.providers.offline import OfflineRuleProvider

from .agent import AgentCore, AgentEvent

# RC ID: RC-057. Expose the candidate Agent Core through an isolated prototype App Server.


class AgentStreamRequest(BaseModel):
    prompt: str


def create_app(provider: ModelProvider | None = None) -> FastAPI:
    app = FastAPI(title="Rabbit Code Agent Prototype", version="0.1.0")
    core = AgentCore(provider or OfflineRuleProvider())

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/agent/stream", response_class=StreamingResponse)
    def stream(request: AgentStreamRequest) -> StreamingResponse:
        def events() -> Iterator[str]:
            for event in core.stream(ModelRequest(prompt=request.prompt)):
                yield _sse(event)

        return StreamingResponse(events(), media_type="text/event-stream")

    return app


def _sse(event: AgentEvent) -> str:
    payload = {"type": event.type.value}
    if event.text is not None:
        payload["text"] = event.text
    return f"event: {event.type.value}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


app = create_app()
