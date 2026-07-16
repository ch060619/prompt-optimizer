from __future__ import annotations

import os

from prompt_optimizer.auth.service import AuthError, AuthService
from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.models import (
    AuthResponse,
    OptimizeMetadata,
    OptimizeResponse,
    PromptAnalysis,
    PromptTemplate,
    UserPublic,
)
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.providers import ModelProviderError, ModelRequest, ProviderRegistry
from prompt_optimizer.providers.limiter import DistributedRateLimiter
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService
from prompt_optimizer.tasks import TaskService
from prompt_optimizer.templates.manager import TemplateManager


class AppServices:
    def __init__(self, *, cli_mode: bool = False) -> None:
        self.analyzer = Analyzer()
        self.optimizer = Optimizer(self.analyzer)
        self.templates = TemplateManager()
        self.auth = AuthService()
        storage = StorageService(
            create_demo_user=os.getenv("PROMPT_OPTIMIZER_ENV") == "development"
        )
        self.cli_owner_id: int | None = None
        if cli_mode:
            username = "__local_cli__"
            found = storage.get_user_by_username(username)
            user = (
                found[0]
                if found
                else storage.create_user(username, self.auth.hash_password(os.urandom(32).hex()))
            )
            self.cli_owner_id = user.id
        self.versions = VersionService(storage)
        self.export = ExportService()
        self.providers = ProviderRegistry(self.optimizer)
        redis_url = os.getenv("PROMPT_OPTIMIZER_REDIS_URL")
        self.remote_limiter = DistributedRateLimiter(redis_url) if redis_url else None
        self.tasks = TaskService(self.versions.storage)

    def register_user(self, username: str, password: str) -> AuthResponse:
        user = self.versions.storage.create_user(username, self.auth.hash_password(password))
        return AuthResponse(access_token=self.auth.create_token(user), user=user)

    def login_user(self, username: str, password: str) -> AuthResponse:
        found = self.versions.storage.get_user_by_username(username)
        if found is None:
            raise AuthError("用户名或密码错误。")
        user, password_hash = found
        if not self.auth.verify_password(password, password_hash):
            raise AuthError("用户名或密码错误。")
        if self.auth.needs_password_rehash(password_hash):
            self.versions.storage.update_password_hash(user.id, self.auth.hash_password(password))
        return AuthResponse(access_token=self.auth.create_token(user), user=user)

    def get_user_from_token(self, token: str | None) -> UserPublic:
        user = self.get_optional_user_from_token(token)
        if user is None:
            raise AuthError("需要登录。")
        return user

    def get_optional_user_from_token(self, token: str | None) -> UserPublic | None:
        if not token:
            return None
        if not token.startswith("Bearer "):
            raise AuthError("无效 token。")
        token_value = token.removeprefix("Bearer ").strip()
        try:
            return self.versions.storage.get_user(self.auth.read_token(token_value))
        except KeyError as exc:
            raise AuthError("用户不存在。") from exc

    def consume_remote_quota(self, user_id: int, provider_name: str) -> None:
        if os.getenv("PROMPT_OPTIMIZER_ENV") == "production" and self.remote_limiter is None:
            raise ValueError("生产环境远程 Provider 必须配置 PROMPT_OPTIMIZER_REDIS_URL。")
        if self.remote_limiter is not None:
            limit = int(os.getenv("PROMPT_OPTIMIZER_REMOTE_RATE_PER_MINUTE", "30"))
            key = f"prompt-optimizer:provider:{provider_name}:user:{user_id}"
            if not self.remote_limiter.allow(key, limit):
                raise ValueError("远程 Provider 请求过于频繁，请稍后重试。")
        self.versions.storage.consume_provider_quota(user_id, provider_name)

    def optimize_and_save(
        self,
        *,
        original_prompt: str,
        prompt: str,
        template: PromptTemplate | None,
        provider_name: str = "offline",
        owner_id: int | None = 1,
        project_id: int | None = None,
    ) -> OptimizeResponse:
        request = ModelRequest(prompt=prompt, template=template)
        fallback_used = False
        error_summary: str | None = None
        try:
            provider_response = self.providers.get(provider_name).optimize(request)
        except (ModelProviderError, RuntimeError, ValueError) as exc:
            if provider_name == "offline":
                raise
            fallback_used = True
            error_summary = str(exc)
            provider_response = self.providers.get("offline").optimize(request)
        analysis = provider_response.analysis
        version_id = None
        if owner_id is not None:
            version_id = self.versions.create(
                original_prompt=original_prompt,
                optimized_prompt=analysis.optimized_prompt or prompt,
                analysis=analysis,
                owner_id=owner_id,
                project_id=project_id,
            )
        metadata = OptimizeMetadata(
            provider_requested=provider_name,
            provider_used=provider_response.provider_used,
            fallback_used=fallback_used,
            latency_ms=provider_response.latency_ms,
            error_summary=error_summary,
        )
        return OptimizeResponse(version_id=version_id, analysis=analysis, metadata=metadata)

    def save_optimized_text(
        self,
        *,
        original_prompt: str,
        prompt: str,
        optimized_prompt: str,
        provider_requested: str,
        provider_used: str,
        fallback_used: bool,
        latency_ms: int,
        error_summary: str | None,
        owner_id: int | None = 1,
        project_id: int | None = None,
    ) -> OptimizeResponse:
        analysis: PromptAnalysis = self.analyzer.analyze(optimized_prompt)
        analysis.optimized_prompt = optimized_prompt
        version_id = None
        if owner_id is not None:
            version_id = self.versions.create(
                original_prompt=original_prompt,
                optimized_prompt=optimized_prompt or prompt,
                analysis=analysis,
                owner_id=owner_id,
                project_id=project_id,
            )
        metadata = OptimizeMetadata(
            provider_requested=provider_requested,
            provider_used=provider_used,
            fallback_used=fallback_used,
            latency_ms=latency_ms,
            error_summary=error_summary,
        )
        return OptimizeResponse(version_id=version_id, analysis=analysis, metadata=metadata)
