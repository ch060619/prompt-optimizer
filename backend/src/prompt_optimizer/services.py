from __future__ import annotations

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.storage.version_service import VersionService
from prompt_optimizer.templates.manager import TemplateManager


class AppServices:
    def __init__(self) -> None:
        self.analyzer = Analyzer()
        self.optimizer = Optimizer(self.analyzer)
        self.templates = TemplateManager()
        self.versions = VersionService()
        self.export = ExportService()

