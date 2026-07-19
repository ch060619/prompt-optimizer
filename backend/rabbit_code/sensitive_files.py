from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

# RC ID: RC-206. Gate sensitive paths and scan output before it can leave the workspace.


class SecretDetected(PermissionError):
    pass


@dataclass(frozen=True)
class SensitiveMatch:
    path: Path
    category: str
    reason: str

    @property
    def sensitive(self) -> bool:
        return self.category != "none"


@dataclass(frozen=True)
class SensitiveDecision:
    allowed: bool
    requires_approval: bool
    reason: str
    matches: tuple[SensitiveMatch, ...] = ()


@dataclass(frozen=True)
class SecretFinding:
    kind: str
    line: int
    digest: str


@dataclass(frozen=True)
class SecretScanReport:
    findings: tuple[SecretFinding, ...]

    @property
    def clean(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict[str, object]:
        return {
            "clean": self.clean,
            "findings": [
                {"kind": finding.kind, "line": finding.line, "sha256": finding.digest}
                for finding in self.findings
            ],
        }


@dataclass(frozen=True)
class _CustomFilename:
    name: str
    category: str


_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b")),
    ("cloud_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "credential_assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?[^\s'\"]{8,}"
        ),
    ),
)


class SensitiveFilePolicy:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()
        if not self.workspace_root.is_dir():
            raise ValueError("workspace root must be a directory")
        self._custom_filenames: list[_CustomFilename] = []
        self._custom_prefixes: list[tuple[Path, str]] = []

    def add_filename(self, name: str, *, category: str = "user rule") -> None:
        normalized = _required_text(name, "filename").casefold()
        self._custom_filenames.append(
            _CustomFilename(normalized, _required_text(category, "category"))
        )

    def add_path_prefix(self, path: str | Path, *, category: str = "user rule") -> None:
        candidate = Path(path).expanduser().resolve(strict=False)
        self._custom_prefixes.append((candidate, _required_text(category, "category")))

    def classify(self, path: str | Path) -> SensitiveMatch:
        candidate = Path(path).expanduser().resolve(strict=False)
        name = candidate.name.casefold()
        parts = {part.casefold() for part in candidate.parts}
        if name == ".env" or name.startswith(".env."):
            return SensitiveMatch(candidate, "environment", "dotenv file")
        if ".ssh" in parts or name.startswith("id_"):
            return SensitiveMatch(candidate, "ssh", "SSH material")
        if candidate.suffix.casefold() in {".pem", ".key", ".p12", ".pfx"}:
            return SensitiveMatch(candidate, "key material", "credential or certificate file")
        if (
            ".aws" in parts
            or ".azure" in parts
            or _under_home_config(candidate, ".aws")
            or _under_home_config(candidate, ".azure")
        ):
            return SensitiveMatch(candidate, "cloud config", "cloud credential directory")
        if (".config" in parts and "gcloud" in parts) or _under_home_config(
            candidate, ".config/gcloud"
        ):
            return SensitiveMatch(candidate, "cloud config", "cloud credential directory")
        if _looks_like_browser_data(candidate):
            return SensitiveMatch(candidate, "browser", "browser profile data")
        if _is_system_path(candidate):
            return SensitiveMatch(candidate, "system", "system directory")
        for custom in self._custom_filenames:
            if name == custom.name:
                return SensitiveMatch(candidate, custom.category, "user-defined filename rule")
        for prefix, category in self._custom_prefixes:
            if _within(candidate, prefix):
                return SensitiveMatch(candidate, category, "user-defined path rule")
        return SensitiveMatch(candidate, "none", "not classified as sensitive")

    def authorize_read(self, path: str | Path, *, approved: bool = False) -> SensitiveDecision:
        match = self.classify(path)
        if not match.sensitive:
            return SensitiveDecision(True, False, "path is not sensitive")
        if approved:
            return SensitiveDecision(True, False, "sensitive read explicitly approved", (match,))
        return SensitiveDecision(
            False,
            True,
            f"sensitive read requires approval: {match.category}",
            (match,),
        )

    def authorize_send(
        self,
        paths: Iterable[str | Path],
        *,
        target: str,
        approved: bool = False,
    ) -> SensitiveDecision:
        normalized_target = _required_text(target, "target")
        matches = tuple(
            match for match in (self.classify(path) for path in paths) if match.sensitive
        )
        if not matches:
            return SensitiveDecision(True, False, f"no sensitive files sent to {normalized_target}")
        if approved:
            return SensitiveDecision(
                True,
                False,
                f"sensitive send explicitly approved for {normalized_target}",
                matches,
            )
        return SensitiveDecision(
            False,
            True,
            f"sensitive send requires approval for {normalized_target}",
            matches,
        )


class SecretScanner:
    def __init__(self, *, max_bytes: int = 1_000_000) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.max_bytes = max_bytes

    def scan_text(self, text: str) -> SecretScanReport:
        findings: list[SecretFinding] = []
        for kind, pattern in _SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                digest = hashlib.sha256(match.group(0).encode("utf-8")).hexdigest()
                finding = SecretFinding(kind, line, digest)
                if finding not in findings:
                    findings.append(finding)
        return SecretScanReport(tuple(findings))

    def scan_file(self, path: Path) -> SecretScanReport:
        data = path.read_bytes()
        if len(data) > self.max_bytes:
            raise ValueError("file exceeds secret scanner size limit")
        return self.scan_text(data.decode("utf-8", errors="replace"))

    def assert_clean(self, text: str) -> None:
        report = self.scan_text(text)
        if not report.clean:
            kinds = ", ".join(sorted({finding.kind for finding in report.findings}))
            raise SecretDetected(f"secret scanner blocked output: {kinds}")


def _required_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty")
    return value.strip()


def _within(path: Path, prefix: Path) -> bool:
    try:
        path.relative_to(prefix)
    except ValueError:
        return False
    return True


def _under_home_config(path: Path, suffix: str) -> bool:
    home = Path.home().resolve()
    return _within(path, home / Path(suffix))


def _looks_like_browser_data(path: Path) -> bool:
    normalized = str(path).casefold().replace("\\", "/")
    return any(
        marker in normalized
        for marker in (
            "/google/chrome/user data",
            "/mozilla/firefox/profiles",
            "/microsoft/edge/user data",
            "/appdata/local/google/chrome/user data",
        )
    )


def _is_system_path(path: Path) -> bool:
    normalized = str(path).casefold().replace("\\", "/")
    if len(normalized) >= 2 and normalized[1] == ":":
        normalized = normalized[2:]
    roots = ("/etc", "/usr", "/var", "/windows", "/program files")
    return any(normalized == root or normalized.startswith(root + "/") for root in roots)
