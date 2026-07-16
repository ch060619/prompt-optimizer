from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncIterator, Awaitable, Callable, Generator, Iterator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import Scope

from prompt_optimizer.core.models import (
    AnalyzeRequest,
    AuthRequest,
    EvaluateTaskRequest,
    ExportRequest,
    OptimizeRequest,
    OptimizeResponse,
    PromptTemplate,
    TaskCreateResponse,
    UserPublic,
)
from prompt_optimizer.paths import PROJECT_ROOT
from prompt_optimizer.providers import ModelProviderError, ModelRequest
from prompt_optimizer.services import AppServices

logger = logging.getLogger("prompt_optimizer.api")

try:
    APP_VERSION = version("prompt-optimizer")
except PackageNotFoundError:
    APP_VERSION = "3.0.0"


class SpaStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            normalized_path = scope["path"].lstrip("/")
            if (
                exc.status_code != 404
                or normalized_path.startswith("api/")
                or Path(normalized_path).suffix
            ):
                raise
            return await super().get_response("index.html", scope)


def create_app(
    app_services: AppServices | None = None,
    static_dir: Path | None = None,
) -> FastAPI:
    current_services = app_services or AppServices()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        current_services.providers.close()
        if current_services.remote_limiter is not None:
            current_services.remote_limiter.close()

    app = FastAPI(title="Prompt Optimizer", version=APP_VERSION, lifespan=lifespan)

    @app.middleware("http")
    async def request_logging(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", uuid4().hex)
        started = perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        latency_ms = int((perf_counter() - started) * 1000)
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "latency_ms": latency_ms,
                },
                ensure_ascii=False,
            )
        )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready() -> dict[str, str]:
        current_services.versions.storage._connect().close()
        return {"status": "ready"}

    @app.post("/api/analyze")
    def analyze(request: AnalyzeRequest) -> object:
        try:
            return current_services.analyzer.analyze(request.prompt)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/auth/register")
    def register(request: AuthRequest) -> object:
        try:
            return current_services.register_user(request.username, request.password)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/auth/login")
    def login(request: AuthRequest) -> object:
        try:
            return current_services.login_user(request.username, request.password)
        except RuntimeError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    @app.get("/api/auth/me")
    def me(authorization: str | None = Header(default=None)) -> object:
        return _current_user(current_services, authorization)

    @app.get("/api/projects")
    def projects(authorization: str | None = Header(default=None)) -> object:
        user = _current_user(current_services, authorization)
        return current_services.versions.storage.list_project_spaces(user.id)

    @app.post("/api/optimize")
    def optimize(
        request: OptimizeRequest,
        authorization: str | None = Header(default=None),
    ) -> object:
        try:
            user = _user_for_provider(current_services, authorization, request.provider)
            prompt, template = _prepare_prompt(current_services, request)
            return current_services.optimize_and_save(
                original_prompt=request.prompt,
                prompt=prompt,
                template=template,
                provider_name=request.provider,
                owner_id=user.id if user else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/optimize/stream")
    def optimize_stream(
        request: OptimizeRequest,
        authorization: str | None = Header(default=None),
    ) -> StreamingResponse:
        def events() -> Iterator[str]:
            try:
                user = _user_for_provider(current_services, authorization, request.provider)
                yield _sse("started", {"provider": request.provider})
                prompt, template = _prepare_prompt(current_services, request)
                preview = current_services.analyzer.analyze(prompt)
                yield _sse("analysis", preview.model_dump(mode="json"))
                result = yield from _stream_provider_result(
                    current_services,
                    request,
                    prompt,
                    template,
                    user.id if user else None,
                )
                if result.version_id is not None:
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

    @app.post("/api/tasks/optimize")
    def create_optimize_task(
        request: OptimizeRequest,
        background_tasks: BackgroundTasks,
        authorization: str | None = Header(default=None),
    ) -> object:
        user = _current_user(current_services, authorization)
        task = current_services.tasks.create(
            owner_id=user.id,
            kind="optimize",
            input_json=request.model_dump(mode="json"),
        )
        if os.getenv("PROMPT_OPTIMIZER_TASK_MODE", "inline") == "inline":
            background_tasks.add_task(
                _run_optimize_task, current_services, task.id, user.id, request
            )
        return TaskCreateResponse(task_id=task.id, status=task.status)

    @app.post("/api/tasks/export")
    def create_export_task(
        request: ExportRequest,
        background_tasks: BackgroundTasks,
        authorization: str | None = Header(default=None),
    ) -> object:
        user = _current_user(current_services, authorization)
        task = current_services.tasks.create(
            owner_id=user.id,
            kind="export",
            input_json=request.model_dump(mode="json"),
        )
        if os.getenv("PROMPT_OPTIMIZER_TASK_MODE", "inline") == "inline":
            background_tasks.add_task(_run_export_task, current_services, task.id, user.id, request)
        return TaskCreateResponse(task_id=task.id, status=task.status)

    @app.post("/api/tasks/evaluate")
    def create_evaluate_task(
        request: EvaluateTaskRequest,
        background_tasks: BackgroundTasks,
        authorization: str | None = Header(default=None),
    ) -> object:
        user = _current_user(current_services, authorization)
        task = current_services.tasks.create(
            owner_id=user.id,
            kind="evaluate",
            input_json=request.model_dump(mode="json"),
        )
        if os.getenv("PROMPT_OPTIMIZER_TASK_MODE", "inline") == "inline":
            background_tasks.add_task(
                _run_evaluate_task, current_services, task.id, user.id, request
            )
        return TaskCreateResponse(task_id=task.id, status=task.status)

    @app.get("/api/tasks/{task_id}")
    def get_task(task_id: str, authorization: str | None = Header(default=None)) -> object:
        try:
            user = _current_user(current_services, authorization)
            task = current_services.tasks.get(task_id, user.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return task

    @app.get("/api/tasks/{task_id}/result")
    def get_task_result(task_id: str, authorization: str | None = Header(default=None)) -> object:
        try:
            user = _current_user(current_services, authorization)
            task = current_services.tasks.get(task_id, user.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if task.status != "succeeded":
            raise HTTPException(status_code=409, detail="任务尚未完成。")
        return task.result_json or {}

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
    def history(
        limit: int = 50,
        before_id: int | None = None,
        authorization: str | None = Header(default=None),
    ) -> object:
        user = _current_user(current_services, authorization)
        return current_services.versions.list(user.id, limit=limit, before_id=before_id)

    @app.get("/api/history/{version_id}")
    def version(version_id: int, authorization: str | None = Header(default=None)) -> object:
        try:
            user = _current_user(current_services, authorization)
            return current_services.versions.get(version_id, user.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/history/{version_id}/diff/{other_id}")
    def diff(
        version_id: int,
        other_id: int,
        authorization: str | None = Header(default=None),
    ) -> object:
        try:
            user = _current_user(current_services, authorization)
            return current_services.versions.diff(version_id, other_id, user.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/export")
    def export(
        request: ExportRequest,
        authorization: str | None = Header(default=None),
    ) -> Response:
        try:
            user = _current_user(current_services, authorization)
            version = current_services.versions.get(request.version_id, user.id)
            content = current_services.export.render(version, request.format)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        media_types = {
            "md": "text/markdown; charset=utf-8",
            "txt": "text/plain; charset=utf-8",
            "csv": "text/csv; charset=utf-8",
            "json": "application/json; charset=utf-8",
        }
        return Response(content=content, media_type=media_types[request.format])

    current_static_dir = static_dir or PROJECT_ROOT / "frontend" / "dist"
    if current_static_dir.exists():
        app.mount("/", SpaStaticFiles(directory=current_static_dir, html=True), name="web")

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


def _current_user(current_services: AppServices, authorization: str | None) -> UserPublic:
    try:
        return current_services.get_user_from_token(authorization)
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _optional_user(current_services: AppServices, authorization: str | None) -> UserPublic | None:
    try:
        return current_services.get_optional_user_from_token(authorization)
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _user_for_provider(
    current_services: AppServices,
    authorization: str | None,
    provider_name: str,
) -> UserPublic | None:
    if provider_name != "offline":
        user = _current_user(current_services, authorization)
        try:
            current_services.consume_remote_quota(user.id, provider_name)
        except ValueError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        return user
    return _optional_user(current_services, authorization)


def _run_optimize_task(
    current_services: AppServices,
    task_id: str,
    owner_id: int,
    request: OptimizeRequest,
) -> None:
    def work() -> dict[str, object]:
        prompt, template = _prepare_prompt(current_services, request)
        result = current_services.optimize_and_save(
            original_prompt=request.prompt,
            prompt=prompt,
            template=template,
            provider_name=request.provider,
            owner_id=owner_id,
        )
        return result.model_dump(mode="json")

    current_services.tasks.run(task_id, owner_id, work)


def _run_export_task(
    current_services: AppServices,
    task_id: str,
    owner_id: int,
    request: ExportRequest,
) -> None:
    def work() -> dict[str, object]:
        version = current_services.versions.get(request.version_id, owner_id)
        content = current_services.export.render(version, request.format)
        return {"format": request.format, "content": content}

    current_services.tasks.run(task_id, owner_id, work)


def _run_evaluate_task(
    current_services: AppServices,
    task_id: str,
    owner_id: int,
    request: EvaluateTaskRequest,
) -> None:
    def work() -> dict[str, object]:
        items: list[dict[str, object]] = []
        for prompt in request.prompts:
            before = current_services.analyzer.analyze(prompt)
            result = current_services.optimize_and_save(
                original_prompt=prompt,
                prompt=prompt,
                template=None,
                provider_name=request.provider,
                owner_id=owner_id,
            )
            items.append(
                {
                    "prompt": prompt,
                    "before_score": before.score.total_score,
                    "after_score": result.analysis.score.total_score,
                    "score_delta": round(
                        result.analysis.score.total_score - before.score.total_score,
                        2,
                    ),
                    "version_id": result.version_id,
                    "metadata": result.metadata.model_dump(mode="json"),
                }
            )
        return {"items": items}

    current_services.tasks.run(task_id, owner_id, work)


def _stream_provider_result(
    current_services: AppServices,
    request: OptimizeRequest,
    prompt: str,
    template: PromptTemplate | None,
    owner_id: int | None,
) -> Generator[str, None, OptimizeResponse]:
    started = perf_counter()
    streamed_chunks: list[str] = []
    provider_used: str = request.provider
    fallback_used = False
    error_summary: str | None = None
    try:
        provider = current_services.providers.get(request.provider)
        provider_used = provider.name
        for chunk in provider.stream(ModelRequest(prompt=prompt, template=template)):
            streamed_chunks.append(chunk)
            yield _sse("chunk", {"text": chunk})
    except (ModelProviderError, RuntimeError, ValueError) as exc:
        if request.provider == "offline":
            raise
        fallback_used = True
        error_summary = str(exc)
        fallback_response = current_services.providers.get("offline").optimize(
            ModelRequest(prompt=prompt, template=template)
        )
        fallback = current_services.save_optimized_text(
            original_prompt=request.prompt,
            prompt=prompt,
            optimized_prompt=fallback_response.analysis.optimized_prompt or prompt,
            provider_requested=request.provider,
            provider_used=fallback_response.provider_used,
            fallback_used=fallback_used,
            latency_ms=fallback_response.latency_ms,
            error_summary=error_summary,
            owner_id=owner_id,
        )
        yield _sse("fallback", fallback.metadata.model_dump(mode="json"))
        for chunk in _chunks(fallback.analysis.optimized_prompt or ""):
            yield _sse("chunk", {"text": chunk})
        return fallback
    optimized_prompt = "".join(streamed_chunks)
    latency_ms = int((perf_counter() - started) * 1000)
    return current_services.save_optimized_text(
        original_prompt=request.prompt,
        prompt=prompt,
        optimized_prompt=optimized_prompt,
        provider_requested=request.provider,
        provider_used=provider_used,
        fallback_used=fallback_used,
        latency_ms=latency_ms,
        error_summary=error_summary,
        owner_id=owner_id,
    )


def _sse(event: str, payload: object) -> str:
    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {event}\ndata: {data}\n\n"


def _chunks(text: str, size: int = 120) -> Iterator[str]:
    if not text:
        return
    for start in range(0, len(text), size):
        yield text[start : start + size]


app = create_app()
