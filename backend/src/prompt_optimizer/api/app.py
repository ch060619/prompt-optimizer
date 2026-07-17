from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable, Generator, Iterator
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from prompt_optimizer.core.models import (
    AnalyzeRequest,
    AuthRequest,
    AuthResponse,
    DiffResult,
    EvaluateTaskRequest,
    ExportRequest,
    OptimizeRequest,
    OptimizeResponse,
    ProjectSpace,
    PromptAnalysis,
    PromptTemplate,
    PromptVersion,
    TaskCreateResponse,
    TaskRecord,
    UserPublic,
    VersionSummary,
)
from prompt_optimizer.identity import PRODUCT_NAME
from prompt_optimizer.paths import PROJECT_ROOT
from prompt_optimizer.providers import ModelProviderError, ModelRequest, ProviderEventType
from prompt_optimizer.services import AppServices

# RC ID: RC-048. Preserve the V2 API while exposing the versioned compatibility surface.
# RC ID: RC-054. Expose Rabbit Code as the canonical API product identity.
# RC ID: RC-049. Translate Provider events into the existing SSE chunk contract.
# RC ID: RC-058. Keep the strict versioned App Server boundary beside the compatibility factory.

services = AppServices()
logger = logging.getLogger("prompt_optimizer.api")


def create_app(
    app_services: AppServices | None = None,
    *,
    include_legacy: bool = True,
    startup_token: str | None = None,
    protocol_version: str = "v1",
) -> FastAPI:
    if startup_token == "":
        raise ValueError("startup_token 不能为空。")
    current_services = app_services or services
    app = FastAPI(
        title=PRODUCT_NAME,
        version="2.0.0",
        openapi_tags=[
            {"name": "legacy", "description": "V2 兼容入口，供现有客户端继续使用。"},
            {"name": "v1", "description": "新客户端使用的版本化 API 契约。"},
        ],
    )

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

    if startup_token is not None:

        @app.middleware("http")
        async def app_server_boundary(
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            is_health = request.url.path == "/api/v1/health"
            if request.url.path.startswith("/api/v1") and not is_health:
                if request.headers.get("X-Rabbit-Code-Startup-Token") != startup_token:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "需要 App Server 启动令牌。"},
                    )
                requested_protocol = request.headers.get(
                    "X-Rabbit-Code-Protocol",
                    protocol_version,
                )
                if requested_protocol != protocol_version:
                    return JSONResponse(
                        status_code=426,
                        content={
                            "detail": "不支持的 App Server 协议版本。",
                            "supported": [protocol_version],
                        },
                    )
            response = await call_next(request)
            response.headers["X-Rabbit-Code-Protocol"] = protocol_version
            return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_router = APIRouter()

    if startup_token is not None:

        @api_router.get("/health", tags=["health"])
        def health() -> dict[str, object]:
            return {
                "status": "ok",
                "protocol_version": protocol_version,
                "startup_token_required": True,
            }

    @api_router.post("/analyze", response_model=PromptAnalysis)
    def analyze(request: AnalyzeRequest) -> PromptAnalysis:
        try:
            return current_services.analyzer.analyze(request.prompt)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api_router.post("/auth/register", response_model=AuthResponse)
    def register(request: AuthRequest) -> AuthResponse:
        try:
            return current_services.register_user(request.username, request.password)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api_router.post("/auth/login", response_model=AuthResponse)
    def login(request: AuthRequest) -> AuthResponse:
        try:
            return current_services.login_user(request.username, request.password)
        except RuntimeError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    @api_router.get("/auth/me", response_model=UserPublic)
    def me(authorization: str | None = Header(default=None)) -> UserPublic:
        return _current_user(current_services, authorization)

    @api_router.get("/projects", response_model=list[ProjectSpace])
    def projects(authorization: str | None = Header(default=None)) -> list[ProjectSpace]:
        user = _current_user(current_services, authorization)
        return current_services.versions.storage.list_project_spaces(user.id)

    @api_router.post("/optimize", response_model=OptimizeResponse)
    def optimize(
        request: OptimizeRequest,
        authorization: str | None = Header(default=None),
    ) -> OptimizeResponse:
        try:
            user = _optional_user(current_services, authorization)
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
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api_router.post("/optimize/stream", response_class=StreamingResponse)
    def optimize_stream(
        request: OptimizeRequest,
        authorization: str | None = Header(default=None),
    ) -> StreamingResponse:
        def events() -> Iterator[str]:
            try:
                user = _optional_user(current_services, authorization)
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

    @api_router.post("/tasks/optimize", response_model=TaskCreateResponse)
    def create_optimize_task(
        request: OptimizeRequest,
        background_tasks: BackgroundTasks,
        authorization: str | None = Header(default=None),
    ) -> TaskCreateResponse:
        user = _current_user(current_services, authorization)
        task = current_services.tasks.create(
            owner_id=user.id,
            kind="optimize",
            input_json=request.model_dump(mode="json"),
        )
        background_tasks.add_task(_run_optimize_task, current_services, task.id, user.id, request)
        return TaskCreateResponse(task_id=task.id, status=task.status)

    @api_router.post("/tasks/export", response_model=TaskCreateResponse)
    def create_export_task(
        request: ExportRequest,
        background_tasks: BackgroundTasks,
        authorization: str | None = Header(default=None),
    ) -> TaskCreateResponse:
        user = _current_user(current_services, authorization)
        task = current_services.tasks.create(
            owner_id=user.id,
            kind="export",
            input_json=request.model_dump(mode="json"),
        )
        background_tasks.add_task(_run_export_task, current_services, task.id, user.id, request)
        return TaskCreateResponse(task_id=task.id, status=task.status)

    @api_router.post("/tasks/evaluate", response_model=TaskCreateResponse)
    def create_evaluate_task(
        request: EvaluateTaskRequest,
        background_tasks: BackgroundTasks,
        authorization: str | None = Header(default=None),
    ) -> TaskCreateResponse:
        user = _current_user(current_services, authorization)
        task = current_services.tasks.create(
            owner_id=user.id,
            kind="evaluate",
            input_json=request.model_dump(mode="json"),
        )
        background_tasks.add_task(_run_evaluate_task, current_services, task.id, user.id, request)
        return TaskCreateResponse(task_id=task.id, status=task.status)

    @api_router.get("/tasks/{task_id}", response_model=TaskRecord)
    def get_task(task_id: str, authorization: str | None = Header(default=None)) -> TaskRecord:
        try:
            user = _current_user(current_services, authorization)
            task = current_services.tasks.get(task_id, user.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return task

    @api_router.get("/tasks/{task_id}/result")
    def get_task_result(
        task_id: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, object]:
        try:
            user = _current_user(current_services, authorization)
            task = current_services.tasks.get(task_id, user.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if task.status != "succeeded":
            raise HTTPException(status_code=409, detail="任务尚未完成。")
        return task.result_json or {}

    @api_router.get("/templates", response_model=list[PromptTemplate])
    def templates(category: str | None = None) -> list[PromptTemplate]:
        return current_services.templates.list_templates(category)

    @api_router.get("/templates/{template_id}", response_model=PromptTemplate)
    def template(template_id: str) -> PromptTemplate:
        try:
            return current_services.templates.get(template_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api_router.get("/history", response_model=list[VersionSummary])
    def history(authorization: str | None = Header(default=None)) -> list[VersionSummary]:
        user = _current_user(current_services, authorization)
        return current_services.versions.list(user.id)

    @api_router.get("/history/{version_id}", response_model=PromptVersion)
    def version(version_id: int, authorization: str | None = Header(default=None)) -> PromptVersion:
        try:
            user = _current_user(current_services, authorization)
            return current_services.versions.get(version_id, user.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api_router.get("/history/{version_id}/diff/{other_id}", response_model=DiffResult)
    def diff(
        version_id: int,
        other_id: int,
        authorization: str | None = Header(default=None),
    ) -> DiffResult:
        try:
            user = _current_user(current_services, authorization)
            return current_services.versions.diff(version_id, other_id, user.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api_router.post("/export", response_class=Response)
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
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        media_types = {
            "md": "text/markdown; charset=utf-8",
            "txt": "text/plain; charset=utf-8",
            "csv": "text/csv; charset=utf-8",
            "json": "application/json; charset=utf-8",
        }
        return Response(content=content, media_type=media_types[request.format])

    if include_legacy:
        app.include_router(api_router, prefix="/api", tags=["legacy"])
    app.include_router(api_router, prefix="/api/v1", tags=["v1"])

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            app.openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                description="新客户端使用 /api/v1；/api 保留为现有客户端兼容入口。",
                routes=app.routes,
                tags=app.openapi_tags,
            )
            app.openapi_schema["x-api-version"] = "v1"
            app.openapi_schema["x-legacy-prefix"] = "/api" if include_legacy else None
            app.openapi_schema["x-rc-reference"] = (
                "RC IDs: RC-048" if include_legacy else "RC IDs: RC-058"
            )
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    static_dir = PROJECT_ROOT / "frontend" / "dist"
    if Path(static_dir).exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="web")

    return app


def create_app_server(
    app_services: AppServices | None = None,
    *,
    startup_token: str,
    protocol_version: str = "v1",
) -> FastAPI:
    """Create the strict, versioned App Server while retaining the legacy factory."""
    if not startup_token:
        raise ValueError("startup_token 不能为空。")
    return create_app(
        app_services,
        include_legacy=False,
        startup_token=startup_token,
        protocol_version=protocol_version,
    )


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
        for event in provider.stream(ModelRequest(prompt=prompt, template=template)):
            if event.type is not ProviderEventType.DELTA or not event.text:
                continue
            chunk = event.text
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
