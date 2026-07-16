from __future__ import annotations

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
from prompt_optimizer.storage.version_service import VersionService
from prompt_optimizer.tasks import TaskService
from prompt_optimizer.templates.manager import TemplateManager


class AppServices:
    def __init__(self) -> None:
        self.analyzer = Analyzer()
        self.optimizer = Optimizer(self.analyzer)
        self.templates = TemplateManager()
        self.versions = VersionService()
        self.export = ExportService()
        self.providers = ProviderRegistry(self.optimizer)
        self.auth = AuthService()
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
        return self.versions.storage.get_user(self.auth.read_token(token_value))

    def optimize_and_save(
        self,
        *,
        original_prompt: str,
        prompt: str,
        template: PromptTemplate | None,
        provider_name: str = "offline",
        owner_id: int = 1,
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
        owner_id: int = 1,
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
