from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

# RC ID: RC-080. Detect project context without executing project-provided instructions.


IGNORED_DIRECTORIES = frozenset(
    {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "dist", "node_modules"}
)
LANGUAGE_SUFFIXES = {
    ".py": "Python",
    ".pyi": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
}
BUILD_MARKERS = frozenset(
    {
        "pyproject.toml",
        "package.json",
        "tsconfig.json",
        "vite.config.ts",
        "Cargo.toml",
        "Makefile",
        "Dockerfile",
    }
)
INSTRUCTION_NAMES = frozenset({"AGENTS.md", "RABBIT.md", "CLAUDE.md"})


@dataclass(frozen=True)
class ProjectContext:
    root: Path
    git_root: Path | None
    branch: str | None
    dirty_files: tuple[str, ...]
    languages: tuple[str, ...]
    build_files: tuple[str, ...]
    instruction_files: tuple[Path, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["root"] = str(self.root)
        payload["git_root"] = str(self.git_root) if self.git_root is not None else None
        payload["instruction_files"] = [str(path) for path in self.instruction_files]
        return payload


class ProjectContextDetector:
    def __init__(self, path: Path) -> None:
        resolved = path.resolve()
        self.root = resolved if resolved.is_dir() else resolved.parent

    def detect(self) -> ProjectContext:
        git_root = self._git_root()
        return ProjectContext(
            root=self.root,
            git_root=git_root,
            branch=self._git_value("branch --show-current", git_root),
            dirty_files=self._dirty_files(git_root),
            languages=self._languages(),
            build_files=self._build_files(),
            instruction_files=self._instruction_files(),
        )

    def _git_root(self) -> Path | None:
        value = self._git_value("rev-parse --show-toplevel", self.root)
        return Path(value).resolve() if value else None

    def _git_value(self, args: str, cwd: Path | None) -> str | None:
        if cwd is None:
            return None
        try:
            result = subprocess.run(
                ["git", *args.split()],
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        value = (result.stdout or "").strip()
        return value if result.returncode == 0 and value else None

    def _dirty_files(self, git_root: Path | None) -> tuple[str, ...]:
        if git_root is None:
            return ()
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=git_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ()
        paths = []
        for line in result.stdout.splitlines():
            if len(line) < 4:
                continue
            path = line[3:]
            paths.append(path.split(" -> ")[-1])
        return tuple(sorted(set(paths)))

    def _files(self) -> list[Path]:
        return [
            path
            for path in self.root.rglob("*")
            if path.is_file()
            and not any(part in IGNORED_DIRECTORIES for part in path.relative_to(self.root).parts)
        ]

    def _languages(self) -> tuple[str, ...]:
        found = {
            language
            for path in self._files()
            if (language := LANGUAGE_SUFFIXES.get(path.suffix))
        }
        return tuple(sorted(found))

    def _build_files(self) -> tuple[str, ...]:
        return tuple(sorted({path.name for path in self._files() if path.name in BUILD_MARKERS}))

    def _instruction_files(self) -> tuple[Path, ...]:
        found = {
            path
            for path in self._files()
            if path.name in INSTRUCTION_NAMES
            or (path.name == "instructions.md" and path.parent.name == ".rabbit-code")
        }
        return tuple(sorted(found))
