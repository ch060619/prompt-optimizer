from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from prompt_optimizer.core.models import (
    AnalyzeRequest,
    ExportRequest,
    OptimizeRequest,
    PromptTemplate,
)
from prompt_optimizer.paths import PROJECT_ROOT
from prompt_optimizer.services import AppServices

services = AppServices()


def create_app(app_services: AppServices | None = None) -> FastAPI:
    current_services = app_services or services
    app = FastAPI(title="Prompt Optimizer", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/api/analyze")
    def analyze(request: AnalyzeRequest) -> object:
        try:
            return current_services.analyzer.analyze(request.prompt)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/optimize")
    def optimize(request: OptimizeRequest) -> object:
        try:
            prompt, template = _prepare_prompt(current_services, request)
            return current_services.optimize_and_save(
                original_prompt=request.prompt,
                prompt=prompt,
                template=template,
                provider_name=request.provider,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/optimize/stream")
    def optimize_stream(request: OptimizeRequest) -> StreamingResponse:
        def events() -> Iterator[str]:
            try:
                yield _sse("started", {"provider": request.provider})
                prompt, template = _prepare_prompt(current_services, request)
                preview = current_services.analyzer.analyze(prompt)
                yield _sse("analysis", preview.model_dump(mode="json"))
                result = current_services.optimize_and_save(
                    original_prompt=request.prompt,
                    prompt=prompt,
                    template=template,
                    provider_name=request.provider,
                )
                if result.metadata.fallback_used:
                    yield _sse("fallback", result.metadata.model_dump(mode="json"))
                optimized = result.analysis.optimized_prompt or ""
                for chunk in _chunks(optimized):
                    yield _sse("chunk", {"text": chunk})
                yield _sse(
                    "saved",
                    {
                        "version_id": result.version_id,
                        "metadata": result.metadata.model_dump(mode="json"),
                    },
                )
                yield _sse("completed", result.model_dump(mode="json"))
            except (KeyError, ValueError) as exc:
                yield _sse("error", {"detail": str(exc)})

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.get("/api/templates")
    def templates(category: str | None = None) -> object:
        return current_services.templates.list_templates(category)

    @app.get("/api/templates/{template_id}")
    def template(template_id: str) -> object:
        try:
            return current_services.templates.get(template_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/history")
    def history() -> object:
        return current_services.versions.list()

    @app.get("/api/history/{version_id}")
    def version(version_id: int) -> object:
        try:
            return current_services.versions.get(version_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/history/{version_id}/diff/{other_id}")
    def diff(version_id: int, other_id: int) -> object:
        try:
            return current_services.versions.diff(version_id, other_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/export")
    def export(request: ExportRequest) -> Response:
        try:
            version = current_services.versions.get(request.version_id)
            content = current_services.export.render(version, request.format)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        media_types = {
            "md": "text/markdown; charset=utf-8",
            "txt": "text/plain; charset=utf-8",
            "csv": "text/csv; charset=utf-8",
            "json": "application/json; charset=utf-8",
        }
        return Response(content=content, media_type=media_types[request.format])

    static_dir = PROJECT_ROOT / "frontend" / "dist"
    if Path(static_dir).exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="web")

    return app


def _prepare_prompt(
    current_services: AppServices,
    request: OptimizeRequest,
) -> tuple[str, PromptTemplate | None]:
    template = current_services.templates.get(request.template_id) if request.template_id else None
    prompt = request.prompt
    if request.template_id and request.variables:
        rendered = current_services.templates.render(request.template_id, request.variables)
        prompt = f"{rendered}\n\n用户补充：{request.prompt}"
    return prompt, template


def _sse(event: str, payload: object) -> str:
    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {event}\ndata: {data}\n\n"


def _chunks(text: str, size: int = 120) -> Iterator[str]:
    if not text:
        return
    for start in range(0, len(text), size):
        yield text[start : start + size]


app = create_app()
