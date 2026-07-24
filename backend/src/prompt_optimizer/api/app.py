from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    FastAPI,
    Header,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from prompt_optimizer.cleanup import CleanupError
from prompt_optimizer.core.models import (
    AnalyzeRequest,
    AuthRequest,
    AuthResponse,
    CleanupRequest,
    DiffResult,
    EvaluateTaskRequest,
    ExecutionDestination,
    ExecutionDestinationRequest,
    ExportRequest,
    LocalModelEventRequest,
    ModelCleanupRequest,
    ModelDirectoryCheckRequest,
    ModelDirectoryMigrateRequest,
    ModelRepairRequest,
    ModelRollbackRequest,
    ModelVersionInstallRequest,
    OptimizeMetadata,
    OptimizeRequest,
    OptimizeResponse,
    PerformanceMetricsSnapshot,
    ProjectSpace,
    PromptAnalysis,
    PromptTemplate,
    PromptVersion,
    ProviderPrivacyNotice,
    RunnerGenerateRequest,
    RunnerResourceConfigRequest,
    TaskCreateResponse,
    TaskRecord,
    UserPublic,
    VersionSummary,
)
from prompt_optimizer.hardware import HardwareDetector
from prompt_optimizer.identity import PRODUCT_NAME
from prompt_optimizer.local_model_state import (
    LocalModelState,
    LocalModelStateError,
    LocalModelStateMachine,
    recover_install_state,
    recover_state,
)
from prompt_optimizer.model_lifecycle import ModelDirectoryError, ModelDirectoryService
from prompt_optimizer.paths import PROJECT_ROOT, app_data_dir
from prompt_optimizer.providers import PRESETS, ModelProviderError, ModelRequest
from prompt_optimizer.public import provider_error_presentation
from prompt_optimizer.retention import RetentionError
from prompt_optimizer.runner_gateway import LocalRunnerGateway, RunnerGatewayError
from prompt_optimizer.runner_resources import RunnerResourceConfig
from prompt_optimizer.services import AppServices
from prompt_optimizer.streaming import (
    OptimizationStreamCursor,
    OptimizationStreamCursorExpired,
    OptimizationStreamEvent,
    OptimizationStreamEventType,
    OptimizationStreamLog,
    encode_optimization_sse,
)
from prompt_optimizer.structured_logging import StructuredLogEmitter

# RC ID: RC-048. Preserve the V2 API while exposing the versioned compatibility surface.
# RC ID: RC-054. Expose Rabbit Code as the canonical API product identity.
# RC IDs: RC-154, RC-155, RC-184. Expose optimization targets, composition, and cleanup boundaries
# through every API entry point.
# RC IDs: RC-049, RC-181. Translate Provider events and expose safe configuration state.
# RC ID: RC-058. Keep the strict versioned App Server boundary beside the compatibility factory.

services = AppServices()
logger = logging.getLogger("prompt_optimizer.api")


def create_app(
    app_services: AppServices | None = None,
    *,
    runner_gateway: LocalRunnerGateway | None = None,
    include_legacy: bool = True,
    startup_token: str | None = None,
    protocol_version: str = "v1",
    strict_boundary: bool = False,
    max_body_bytes: int = 2_000_000,
) -> FastAPI:
    if startup_token == "":
        raise ValueError("startup_token 不能为空。")
    if max_body_bytes <= 0:
        raise ValueError("max_body_bytes must be positive")
    if strict_boundary and startup_token is None:
        raise ValueError("strict boundary requires a startup token")
    current_services = app_services or services
    local_runner_gateway = runner_gateway or LocalRunnerGateway(metrics=current_services.metrics)
    model_directory = ModelDirectoryService(
        app_data_dir() / "model-registry.json",
        app_data_dir() / "local-models",
    )
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.recovered_tasks = current_services.tasks.recover_incomplete()
        yield

    app = FastAPI(
        title=PRODUCT_NAME,
        version="2.0.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "legacy", "description": "V2 兼容入口，供现有客户端继续使用。"},
            {"name": "v1", "description": "新客户端使用的版本化 API 契约。"},
        ],
    )
    app.state.startup_token = startup_token
    app.state.strict_boundary = strict_boundary
    app.state.max_body_bytes = max_body_bytes
    app.state.recovered_tasks = 0

    structured_logger = StructuredLogEmitter(lambda line: logger.info(line))

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
        structured_logger.emit(
            "http.request",
            request_id=request_id,
            status=str(response.status_code),
            fields={
                "component": "api",
                "status": response.status_code,
                "latency_ms": latency_ms,
            },
        )
        return response

    if startup_token is not None:

        @app.middleware("http")
        async def app_server_boundary(
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            if strict_boundary:
                boundary_error = _strict_request_error(request, max_body_bytes)
                if boundary_error is not None:
                    return boundary_error
                stream_error = await _strict_stream_request_error(request, max_body_bytes)
                if stream_error is not None:
                    return stream_error
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
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://[::1]:5173",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Last-Event-ID",
            "X-Request-ID",
            "X-Rabbit-Code-Protocol",
            "X-Rabbit-Code-Startup-Token",
        ],
    )

    api_router = APIRouter()
    stream_log = OptimizationStreamLog(max_events=512)

    if startup_token is not None:

        @api_router.get("/health", tags=["health"])
        def health() -> dict[str, object]:
            return {
                "status": "ok",
                "protocol_version": protocol_version,
                "startup_token_required": True,
            }

    @api_router.get("/config", tags=["config"])
    def config() -> dict[str, dict[str, object]]:
        return current_services.config.resolve().display()

    @api_router.get("/metrics", response_model=PerformanceMetricsSnapshot, tags=["metrics"])
    def metrics() -> PerformanceMetricsSnapshot:
        report = HardwareDetector(network_probe=lambda: False).detect()
        ram = report.fields.get("ram")
        gpu = report.fields.get("gpu")
        ram_bytes = _hardware_int(ram.value, "total_bytes") if ram is not None else None
        gpu_bytes = _gpu_memory_bytes(gpu.value) if gpu is not None else None
        current_services.metrics.record_resources(
            cpu_percent=_cpu_load_percent(),
            ram_bytes=ram_bytes,
            gpu_memory_bytes=gpu_bytes,
        )
        return current_services.metrics.snapshot()

    @api_router.get(
        "/provider-privacy",
        response_model=list[ProviderPrivacyNotice],
        tags=["providers"],
    )
    def provider_privacy() -> list[ProviderPrivacyNotice]:
        return [
            ProviderPrivacyNotice(
                id=preset.id,
                display_name=preset.display_name,
                version=preset.privacy.version,
                execution_location=preset.privacy.execution_location,
                request_fields=list(preset.privacy.request_fields),
                service_region=preset.privacy.service_region,
                privacy_policy_url=preset.privacy.privacy_policy_url,
                retention_risk=preset.privacy.retention_risk,
            )
            for preset in PRESETS.values()
            if preset.privacy is not None
        ]

    @api_router.get("/local-models/{model_id}/state", tags=["local-models"])
    def local_model_state(model_id: str) -> dict[str, object]:
        state = _load_local_model_state(model_id)
        return _local_model_event(
            event="recovered",
            message="local model state recovered",
            state=state,
        )

    @api_router.post("/local-models/{model_id}/events", tags=["local-models"])
    def local_model_event(
        model_id: str,
        request: LocalModelEventRequest,
    ) -> dict[str, object]:
        state = _load_local_model_state(model_id)
        machine = LocalModelStateMachine(state)
        try:
            event = machine.apply(
                request.event,
                message=request.message,
                progress=request.progress,
                error=request.error,
            )
        except LocalModelStateError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        _save_local_model_state(model_id, event.state)
        return event.to_dict()

    @api_router.get("/local-models/directory", tags=["local-models"])
    def local_model_directory() -> dict[str, object]:
        return {
            "root": str(model_directory.root),
            "registry": model_directory.snapshot(),
        }

    @api_router.post("/local-models/directory/check", tags=["local-models"])
    def check_local_model_directory(request: ModelDirectoryCheckRequest) -> dict[str, object]:
        try:
            return model_directory.check_directory(
                Path(request.path), required_bytes=request.required_bytes
            ).to_dict()
        except ModelDirectoryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api_router.post("/local-models/directory/migrate", tags=["local-models"])
    def migrate_local_model_directory(
        request: ModelDirectoryMigrateRequest,
    ) -> dict[str, object]:
        try:
            return model_directory.migrate_directory(Path(request.destination)).to_dict()
        except ModelDirectoryError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api_router.post("/local-models/{model_id}/versions", tags=["local-models"])
    def install_local_model_version(
        model_id: str,
        request: ModelVersionInstallRequest,
    ) -> dict[str, object]:
        try:
            return model_directory.install_version(
                model_id=model_id,
                source=Path(request.source),
                version=request.version,
                checksum=request.checksum,
            ).to_dict()
        except ModelDirectoryError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api_router.post("/local-models/{model_id}/rollback", tags=["local-models"])
    def rollback_local_model(model_id: str, request: ModelRollbackRequest) -> dict[str, object]:
        try:
            return model_directory.rollback(model_id, request.version).to_dict()
        except ModelDirectoryError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api_router.post("/local-models/{model_id}/repair", tags=["local-models"])
    def repair_local_model(model_id: str, request: ModelRepairRequest) -> dict[str, object]:
        try:
            source = Path(request.source) if request.source else None
            return model_directory.repair(model_id, source=source).to_dict()
        except ModelDirectoryError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api_router.post("/local-models/cleanup", tags=["local-models"])
    def cleanup_local_models(request: ModelCleanupRequest) -> dict[str, object]:
        try:
            return model_directory.cleanup(request.model_id).to_dict()
        except ModelDirectoryError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api_router.delete("/local-models/{model_id}/registered", tags=["local-models"])
    def uninstall_registered_local_model(model_id: str) -> dict[str, object]:
        try:
            return model_directory.uninstall(model_id).to_dict()
        except ModelDirectoryError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api_router.get("/local-runners/{runner}/models", tags=["local-runners"])
    def local_runner_models(runner: str) -> dict[str, object]:
        try:
            models = local_runner_gateway.list(runner)
            return {
                "runner": runner,
                "models": [
                    {"model_id": model.model_id, "loaded": model.loaded} for model in models
                ],
            }
        except RunnerGatewayError as exc:
            raise _runner_http_exception(exc) from exc

    @api_router.get("/local-runners/{runner}/capabilities", tags=["local-runners"])
    def local_runner_capabilities(runner: str) -> dict[str, object]:
        try:
            return local_runner_gateway.capabilities(runner).to_dict()
        except RunnerGatewayError as exc:
            raise _runner_http_exception(exc) from exc

    @api_router.get("/local-runners/{runner}/health", tags=["local-runners"])
    def local_runner_health(runner: str) -> dict[str, object]:
        try:
            health = local_runner_gateway.health(runner)
            return {
                "runner": runner,
                "ready": health.ready,
                "model_id": health.model_id,
                "detail": health.detail,
                "status": health.status,
                "temperature_celsius": health.temperature_celsius,
            }
        except RunnerGatewayError as exc:
            raise _runner_http_exception(exc) from exc

    @api_router.get("/local-runners/{runner}/queue", tags=["local-runners"])
    def local_runner_queue(runner: str) -> dict[str, object]:
        return {"runner": runner, **local_runner_gateway.queue_status().to_dict()}

    @api_router.get("/local-runners/{runner}/resources", tags=["local-runners"])
    def local_runner_resources(runner: str) -> dict[str, object]:
        return {
            "runner": runner,
            "config": local_runner_gateway.resource_config.to_dict(),
            "signal": local_runner_gateway.resource_signal(runner),
        }

    @api_router.post("/local-runners/{runner}/resources", tags=["local-runners"])
    def configure_local_runner_resources(
        runner: str,
        request: RunnerResourceConfigRequest,
    ) -> dict[str, object]:
        current = local_runner_gateway.resource_config
        config = RunnerResourceConfig(
            threads=request.threads if request.threads is not None else current.threads,
            gpu_layers=(
                request.gpu_layers if request.gpu_layers is not None else current.gpu_layers
            ),
            context_length=(
                request.context_length
                if request.context_length is not None
                else current.context_length
            ),
            concurrency=(
                request.concurrency if request.concurrency is not None else current.concurrency
            ),
            idle_timeout_seconds=(
                request.idle_timeout_seconds
                if request.idle_timeout_seconds is not None
                else current.idle_timeout_seconds
            ),
            temperature_limit_celsius=(
                request.temperature_limit_celsius
                if request.temperature_limit_celsius is not None
                else current.temperature_limit_celsius
            ),
        )
        try:
            return {
                "runner": runner,
                "config": local_runner_gateway.configure_resources(config).to_dict(),
            }
        except RunnerGatewayError as exc:
            raise _runner_http_exception(exc) from exc

    @api_router.post("/local-runners/{runner}/models/{model_id}/load", tags=["local-runners"])
    def load_local_runner_model(runner: str, model_id: str) -> dict[str, str]:
        try:
            return local_runner_gateway.load(runner, model_id).to_dict()
        except RunnerGatewayError as exc:
            raise _runner_http_exception(exc) from exc

    @api_router.post("/local-runners/{runner}/models/{model_id}/unload", tags=["local-runners"])
    def unload_local_runner_model(runner: str, model_id: str) -> dict[str, str]:
        try:
            return local_runner_gateway.unload(runner, model_id).to_dict()
        except RunnerGatewayError as exc:
            raise _runner_http_exception(exc) from exc

    @api_router.post("/local-runners/{runner}/generate", tags=["local-runners"])
    def generate_local_runner(
        runner: str,
        request: RunnerGenerateRequest,
    ) -> dict[str, object]:
        try:
            result = local_runner_gateway.generate(
                runner,
                ModelRequest(prompt=request.prompt, request_id=request.request_id),
                model_id=request.model_id,
            )
            return result.to_dict()
        except RunnerGatewayError as exc:
            raise _runner_http_exception(exc) from exc

    @api_router.post("/local-runners/{runner}/stream", tags=["local-runners"])
    def stream_local_runner(
        runner: str,
        request: RunnerGenerateRequest,
    ) -> StreamingResponse:
        def events() -> Iterator[str]:
            try:
                for event in local_runner_gateway.stream(
                    runner,
                    ModelRequest(prompt=request.prompt, request_id=request.request_id),
                    model_id=request.model_id,
                ):
                    yield _sse(event.event, event.to_dict())
            except RunnerGatewayError as exc:
                yield _sse("error", exc.to_dict())

        return StreamingResponse(events(), media_type="text/event-stream")

    @api_router.post("/local-runners/{runner}/requests/{request_id}/cancel", tags=["local-runners"])
    def cancel_local_runner(runner: str, request_id: str) -> dict[str, object]:
        try:
            return {
                "runner": runner,
                "request_id": request_id,
                "cancelled": local_runner_gateway.cancel(runner, request_id),
            }
        except RunnerGatewayError as exc:
            raise _runner_http_exception(exc) from exc

    @api_router.get("/data/cleanup/preview", tags=["data"])
    def cleanup_preview() -> dict[str, object]:
        return current_services.cleanup.preview().display()

    @api_router.post("/data/cleanup", tags=["data"])
    def cleanup(request: CleanupRequest) -> dict[str, object]:
        try:
            return current_services.cleanup.clear_all(confirm=request.confirm).display()
        except CleanupError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api_router.get("/data/retention/preview", tags=["data"])
    def retention_preview() -> dict[str, object]:
        return current_services.retention.preview().display()

    @api_router.post("/data/retention", tags=["data"])
    def retention(request: CleanupRequest) -> dict[str, object]:
        try:
            return current_services.retention.apply(confirm=request.confirm).display()
        except RetentionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

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
        request_id_header: str | None = Header(default=None, alias="X-Request-ID"),
        authorization: str | None = Header(default=None),
    ) -> OptimizeResponse:
        _validate_optimization_targets(request)
        try:
            user = _optional_user(current_services, authorization)
            prompt, template = _prepare_prompt(current_services, request)
            return current_services.optimization.optimize(
                original_prompt=request.prompt,
                prompt=prompt,
                template=template,
                targets=request.targets,
                strategy=request.strategy,
                provider_name=request.provider,
                model=request.model,
                optimizer_provider=request.optimizer_provider,
                optimizer_model=request.optimizer_model,
                owner_id=user.id if user else None,
                save_prompt_history=request.save_prompt_history,
                max_tokens=request.max_tokens,
                max_cost=request.max_cost,
                request_id=request_id_header,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ModelProviderError as exc:
            raise _provider_http_exception(exc) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api_router.post("/execution-destination", response_model=ExecutionDestination)
    def execution_destination_preview(
        request: ExecutionDestinationRequest,
    ) -> ExecutionDestination:
        return current_services.optimization.execution_destination(
            provider_name=request.provider,
            model=request.model,
            optimizer_provider=request.optimizer_provider,
            optimizer_model=request.optimizer_model,
            strategy=request.strategy,
        )

    @api_router.post("/optimize/stream", response_class=StreamingResponse)
    def optimize_stream(
        request: OptimizeRequest,
        http_request: Request,
        authorization: str | None = Header(default=None),
        request_id_header: str | None = Header(default=None, alias="X-Request-ID"),
        last_event_id: int | None = Header(default=None, alias="Last-Event-ID"),
    ) -> StreamingResponse:
        _validate_optimization_targets(request)

        def events() -> Iterator[str]:
            request_id = request_id_header or uuid4().hex
            legacy = http_request.url.path == "/api/optimize/stream"
            try:
                user = _optional_user(current_services, authorization)
                latest_seq = stream_log.latest_seq(request_id)
                if latest_seq >= 0:
                    cursor = OptimizationStreamCursor(
                        request_id=request_id,
                        after_seq=last_event_id if last_event_id is not None else -1,
                    )
                    for stored in stream_log.replay(cursor):
                        yield _stream_output(stored, legacy=legacy)
                    return

                started = stream_log.append(
                    request_id,
                    OptimizationStreamEventType.STARTED,
                    {"provider": request.provider},
                    event_key="started",
                )
                yield _stream_output(started, legacy=legacy)
                prompt, template = _prepare_prompt(current_services, request)
                for event in current_services.optimization.stream(
                    original_prompt=request.prompt,
                    prompt=prompt,
                    template=template,
                    targets=request.targets,
                    strategy=request.strategy,
                    provider_name=request.provider,
                    model=request.model,
                    optimizer_provider=request.optimizer_provider,
                    optimizer_model=request.optimizer_model,
                    owner_id=user.id if user else None,
                    save_prompt_history=request.save_prompt_history,
                    request_id=request_id,
                    max_tokens=request.max_tokens,
                    max_cost=request.max_cost,
                ):
                    if event.event == "analysis":
                        if not isinstance(event.data, PromptAnalysis):
                            raise RuntimeError("优化服务返回了无效分析。")
                        stored = stream_log.append(
                            request_id,
                            OptimizationStreamEventType.ANALYSIS,
                            event.data.model_dump(mode="json"),
                            event_key="analysis",
                        )
                        yield _stream_output(stored, legacy=legacy)
                    elif event.event == "chunk":
                        stored = stream_log.append(
                            request_id,
                            OptimizationStreamEventType.DELTA,
                            {"text": event.data},
                        )
                        yield _stream_output(stored, legacy=legacy)
                    elif event.event == "fallback":
                        if not isinstance(event.data, OptimizeMetadata):
                            raise RuntimeError("优化服务返回了无效降级信息。")
                        stored = stream_log.append(
                            request_id,
                            OptimizationStreamEventType.FALLBACK,
                            event.data.model_dump(mode="json"),
                        )
                        yield _stream_output(stored, legacy=legacy)
                    elif event.event == "completed":
                        result = event.data
                        if not isinstance(result, OptimizeResponse):
                            raise RuntimeError("优化服务返回了无效结果。")
                        if result.version_id is not None:
                            saved = stream_log.append(
                                request_id,
                                OptimizationStreamEventType.SAVED,
                                {
                                    "version_id": result.version_id,
                                    "metadata": result.metadata.model_dump(mode="json"),
                                },
                                event_key="saved",
                            )
                            yield _stream_output(saved, legacy=legacy)
                        completed = stream_log.append(
                            request_id,
                            OptimizationStreamEventType.COMPLETED,
                            result.model_dump(mode="json"),
                            event_key="completed",
                        )
                        yield _stream_output(completed, legacy=legacy)
            except OptimizationStreamCursorExpired as exc:
                yield _sse("error", {"detail": str(exc)})
            except Exception as exc:
                if stream_log.is_cancelled(request_id):
                    return
                presentation = provider_error_presentation(exc)
                error = stream_log.append(
                    request_id,
                    OptimizationStreamEventType.ERROR,
                    {
                        "code": presentation.code,
                        "category": presentation.category,
                        "detail": presentation.message,
                        "retryable": presentation.retryable,
                        "recovery_action": presentation.recovery_action,
                        "exit_code": presentation.exit_code,
                        "provider_request_id": presentation.request_id,
                    },
                    event_key="error",
                )
                yield _stream_output(error, legacy=legacy)

        return StreamingResponse(events(), media_type="text/event-stream")

    @api_router.websocket("/optimize/ws")
    async def optimize_websocket(websocket: WebSocket) -> None:
        startup_header = websocket.headers.get("x-rabbit-code-startup-token")
        if startup_token is not None and startup_header != startup_token:
            await websocket.close(code=4401)
            return
        if strict_boundary and websocket.headers.get("origin") not in {
            None,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://[::1]:5173",
        }:
            await websocket.close(code=4403)
            return

        await websocket.accept()
        request_id = websocket.headers.get("x-request-id") or uuid4().hex
        try:
            request = OptimizeRequest.model_validate(await websocket.receive_json())
            _validate_optimization_targets(request)
            user = _optional_user(
                current_services,
                websocket.headers.get("authorization"),
            )
            prompt, template = _prepare_prompt(current_services, request)
            await websocket.send_json(
                {"event": "started", "data": {"provider": request.provider}}
            )
            for event in current_services.optimization.stream(
                original_prompt=request.prompt,
                prompt=prompt,
                template=template,
                targets=request.targets,
                strategy=request.strategy,
                provider_name=request.provider,
                model=request.model,
                optimizer_provider=request.optimizer_provider,
                optimizer_model=request.optimizer_model,
                owner_id=user.id if user else None,
                save_prompt_history=request.save_prompt_history,
                request_id=request_id,
                max_tokens=request.max_tokens,
                max_cost=request.max_cost,
            ):
                if event.event == "analysis" and isinstance(event.data, PromptAnalysis):
                    await websocket.send_json(
                        {"event": "analysis", "data": event.data.model_dump(mode="json")}
                    )
                elif event.event == "chunk":
                    await websocket.send_json({"event": "chunk", "data": {"text": event.data}})
                elif event.event == "fallback" and isinstance(event.data, OptimizeMetadata):
                    await websocket.send_json(
                        {"event": "fallback", "data": event.data.model_dump(mode="json")}
                    )
                elif event.event == "completed" and isinstance(event.data, OptimizeResponse):
                    await websocket.send_json(
                        {"event": "completed", "data": event.data.model_dump(mode="json")}
                    )
                    await websocket.close(code=1000)
                    return
        except WebSocketDisconnect:
            return
        except Exception as exc:
            presentation = provider_error_presentation(exc)
            await websocket.send_json(
                {
                    "event": "error",
                    "data": {
                        "code": presentation.code,
                        "category": presentation.category,
                        "detail": presentation.message,
                        "retryable": presentation.retryable,
                        "recovery_action": presentation.recovery_action,
                    },
                }
            )
            await websocket.close(code=1011)

    @api_router.post("/optimize/stream/{request_id}/cancel")
    def cancel_optimize_stream(request_id: str) -> dict[str, object]:
        existing = stream_log.replay(
            OptimizationStreamCursor(request_id=request_id, after_seq=-1)
        )
        if any(
            item.type
            in {
                OptimizationStreamEventType.COMPLETED,
                OptimizationStreamEventType.ERROR,
                OptimizationStreamEventType.CANCELLED,
            }
            for item in existing
        ):
            return {
                "request_id": request_id,
                "cancelled": False,
                "seq": stream_log.latest_seq(request_id),
            }
        cancelled = current_services.optimization.cancel(request_id)
        event = stream_log.cancel(request_id)
        return {"request_id": request_id, "cancelled": cancelled, "seq": event.seq}

    @api_router.post("/optimize/{request_id}/cancel")
    def cancel_optimize(request_id: str) -> dict[str, object]:
        return {
            "request_id": request_id,
            "cancelled": current_services.optimization.cancel(request_id),
        }

    @api_router.post("/tasks/optimize", response_model=TaskCreateResponse)
    def create_optimize_task(
        request: OptimizeRequest,
        background_tasks: BackgroundTasks,
        authorization: str | None = Header(default=None),
    ) -> TaskCreateResponse:
        _validate_optimization_targets(request)
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

    @api_router.post("/history/{version_id}/accept", response_model=PromptVersion)
    def accept_version(
        version_id: int,
        authorization: str | None = Header(default=None),
    ) -> PromptVersion:
        try:
            user = _current_user(current_services, authorization)
            return current_services.versions.mark_accepted(version_id, user.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api_router.delete("/history/{version_id}", status_code=204)
    def delete_version(
        version_id: int,
        authorization: str | None = Header(default=None),
    ) -> Response:
        try:
            user = _current_user(current_services, authorization)
            current_services.versions.delete(version_id, user.id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return Response(status_code=204)

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
    runner_gateway: LocalRunnerGateway | None = None,
    startup_token: str,
    protocol_version: str = "v1",
    strict_boundary: bool = False,
    max_body_bytes: int = 2_000_000,
) -> FastAPI:
    """Create the strict, versioned App Server while retaining the legacy factory."""
    if not startup_token:
        raise ValueError("startup_token 不能为空。")
    return create_app(
        app_services,
        runner_gateway=runner_gateway,
        include_legacy=False,
        startup_token=startup_token,
        protocol_version=protocol_version,
        strict_boundary=strict_boundary,
        max_body_bytes=max_body_bytes,
    )


def _strict_request_error(request: Request, max_body_bytes: int) -> JSONResponse | None:
    client_host = request.client.host if request.client is not None else None
    if client_host not in {"127.0.0.1", "::1"}:
        return JSONResponse(status_code=400, content={"detail": "仅允许 Loopback 客户端。"})
    raw_host = request.headers.get("host", "")
    host = (
        raw_host.partition("]")[0].lstrip("[")
        if raw_host.startswith("[")
        else raw_host.split(":", 1)[0]
    ).lower()
    if host not in {"127.0.0.1", "localhost", "::1"}:
        return JSONResponse(status_code=400, content={"detail": "Host 不在 Loopback allowlist。"})
    origin = request.headers.get("origin")
    if origin not in {
        None,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
    }:
        return JSONResponse(status_code=403, content={"detail": "Origin 不在 allowlist。"})
    raw_length = request.headers.get("content-length")
    if raw_length is not None:
        try:
            content_length = int(raw_length)
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Content-Length 无效。"})
        if content_length > max_body_bytes:
            return JSONResponse(status_code=413, content={"detail": "请求体超过上限。"})
    return None


async def _strict_stream_request_error(
    request: Request,
    max_body_bytes: int,
) -> JSONResponse | None:
    if request.headers.get("content-length") is not None:
        return None
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > max_body_bytes:
            return JSONResponse(status_code=413, content={"detail": "请求体超过上限。"})
    request._body = bytes(body)  # type: ignore[attr-defined]
    return None


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


def _validate_optimization_targets(request: OptimizeRequest) -> None:
    if request.targets is not None and not request.targets.has_enabled_target():
        raise HTTPException(status_code=400, detail="至少选择一项优化目标。")


def _hardware_int(value: object, key: str) -> int | None:
    if isinstance(value, dict):
        candidate = value.get(key)
        if isinstance(candidate, int) and candidate >= 0:
            return candidate
    return None


def _gpu_memory_bytes(value: object) -> int | None:
    if not isinstance(value, dict):
        return None
    devices = value.get("devices")
    if not isinstance(devices, list):
        return None
    memories = [
        int(device["memory_mb"]) * 1024 * 1024
        for device in devices
        if isinstance(device, dict)
        and isinstance(device.get("memory_mb"), int)
        and device["memory_mb"] >= 0
    ]
    return sum(memories) if memories else None


def _cpu_load_percent() -> float | None:
    load_average = getattr(os, "getloadavg", None)
    if not callable(load_average):
        return None
    try:
        load = load_average()[0]
        cores = max(1, os.cpu_count() or 1)
    except (AttributeError, OSError):
        return None
    return round(min(100.0, max(0.0, load / cores * 100)), 2)


def _provider_http_exception(error: ModelProviderError) -> HTTPException:
    presentation = provider_error_presentation(error)
    return HTTPException(
        status_code=presentation.http_status,
        detail={
            "code": presentation.code,
            "category": presentation.category,
            "message": presentation.message,
            "retryable": presentation.retryable,
            "recovery_action": presentation.recovery_action,
            "exit_code": presentation.exit_code,
            "provider_request_id": presentation.request_id,
        },
    )


def _runner_http_exception(error: RunnerGatewayError) -> HTTPException:
    status = 409 if error.code in {"runner_busy", "model_not_ready", "local_not_ready"} else 400
    return HTTPException(status_code=status, detail=error.to_dict())


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
        result = current_services.optimization.optimize(
            original_prompt=request.prompt,
            prompt=prompt,
            template=template,
            targets=request.targets,
            strategy=request.strategy,
            provider_name=request.provider,
            model=request.model,
            optimizer_provider=request.optimizer_provider,
            optimizer_model=request.optimizer_model,
            owner_id=owner_id,
            save_prompt_history=request.save_prompt_history,
            max_tokens=request.max_tokens,
            max_cost=request.max_cost,
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
            result = current_services.optimization.optimize(
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


def _sse(event: str, payload: object) -> str:
    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {event}\ndata: {data}\n\n"


def _stream_output(event: OptimizationStreamEvent, *, legacy: bool) -> str:
    if not legacy:
        return encode_optimization_sse(event)
    event_name = "chunk" if event.type is OptimizationStreamEventType.DELTA else event.type.value
    return _sse(event_name, event.payload)


_LOCAL_MODEL_STATUSES = {
    "not_installed",
    "downloading",
    "paused",
    "verifying",
    "loading",
    "ready",
    "busy",
    "stopping",
    "unloaded",
    "corrupt",
    "update",
    "failed",
    "disabled",
}


def _local_model_root(model_id: str) -> Path:
    if not model_id or model_id in {".", ".."} or Path(model_id).name != model_id:
        raise HTTPException(status_code=400, detail="本地模型 ID 无效。")
    return app_data_dir() / "local-models" / model_id


def _load_local_model_state(model_id: str) -> LocalModelState:
    root = _local_model_root(model_id)
    lifecycle_path = root / "lifecycle-state.json"
    if lifecycle_path.is_file():
        try:
            payload = json.loads(lifecycle_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("invalid lifecycle state")
            status = payload.get("status")
            if status not in _LOCAL_MODEL_STATUSES:
                raise ValueError("invalid lifecycle status")
            state = LocalModelState(
                model_id=model_id,
                runner=str(payload.get("runner") or "ollama"),
                status=status,
                progress=int(payload.get("progress") or 0),
                installed_path=(
                    payload["installed_path"]
                    if isinstance(payload.get("installed_path"), str)
                    else None
                ),
                version=payload.get("version") if isinstance(payload.get("version"), str) else None,
                error=payload.get("error") if isinstance(payload.get("error"), str) else None,
                last_event=str(payload.get("last_event") or "recovered"),
            )
            installed_path = Path(state.installed_path) if state.installed_path else None
            if state.status in {"busy", "stopping", "loading"} and installed_path is not None:
                return recover_state(state, installed_path=installed_path)
            return state
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return LocalModelState(
                model_id=model_id,
                runner="ollama",
                status="corrupt",
                error=f"invalid lifecycle state: {exc}",
            )
    install_state_path = root / "install-state.json"
    if install_state_path.is_file():
        try:
            return recover_install_state(install_state_path)
        except LocalModelStateError as exc:
            return LocalModelState(
                model_id=model_id,
                runner="ollama",
                status="corrupt",
                error=str(exc),
            )
    installed_path = root / model_id
    return LocalModelState(
        model_id=model_id,
        runner="ollama",
        status="ready" if installed_path.is_file() else "not_installed",
        progress=100 if installed_path.is_file() else 0,
        installed_path=str(installed_path) if installed_path.is_file() else None,
    )


def _save_local_model_state(model_id: str, state: LocalModelState) -> None:
    root = _local_model_root(model_id)
    root.mkdir(parents=True, exist_ok=True)
    target = root / "lifecycle-state.json"
    temporary = root / ".lifecycle-state.json.tmp"
    temporary.write_text(
        json.dumps(state.to_dict(), ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def _local_model_event(
    *,
    event: str,
    message: str,
    state: LocalModelState,
) -> dict[str, object]:
    return {
        "event": event,
        "message": message,
        "lifecycle_event": state.last_event,
        "lifecycle_status": state.status,
        "recovery_actions": list(state.recovery_actions),
        "state": state.to_dict(),
    }


app = create_app()
