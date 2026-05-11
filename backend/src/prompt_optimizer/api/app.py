from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from prompt_optimizer.core.models import AnalyzeRequest, ExportRequest, OptimizeRequest
from prompt_optimizer.paths import PROJECT_ROOT
from prompt_optimizer.services import AppServices

services = AppServices()


def create_app() -> FastAPI:
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
            return services.analyzer.analyze(request.prompt)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/optimize")
    def optimize(request: OptimizeRequest) -> object:
        try:
            template = services.templates.get(request.template_id) if request.template_id else None
            prompt = request.prompt
            if request.template_id and request.variables:
                rendered = services.templates.render(request.template_id, request.variables)
                prompt = f"{rendered}\n\n用户补充：{request.prompt}"
            analysis = services.optimizer.optimize(prompt, template)
            version_id = services.versions.create(
                original_prompt=request.prompt,
                optimized_prompt=analysis.optimized_prompt or prompt,
                analysis=analysis,
            )
            return {"version_id": version_id, "analysis": analysis}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/templates")
    def templates(category: str | None = None) -> object:
        return services.templates.list_templates(category)

    @app.get("/api/templates/{template_id}")
    def template(template_id: str) -> object:
        try:
            return services.templates.get(template_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/history")
    def history() -> object:
        return services.versions.list()

    @app.get("/api/history/{version_id}")
    def version(version_id: int) -> object:
        try:
            return services.versions.get(version_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/history/{version_id}/diff/{other_id}")
    def diff(version_id: int, other_id: int) -> object:
        try:
            return services.versions.diff(version_id, other_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/export")
    def export(request: ExportRequest) -> Response:
        try:
            version = services.versions.get(request.version_id)
            content = services.export.render(version, request.format)
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


app = create_app()

