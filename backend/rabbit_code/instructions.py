from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# RC ID: RC-081. Load layered project instructions without executing them.


INSTRUCTION_FILES = ("AGENTS.md", "RABBIT.md")


@dataclass(frozen=True)
class InstructionDocument:
    path: Path
    scope: str
    content: str


@dataclass(frozen=True)
class InstructionSet:
    documents: tuple[InstructionDocument, ...]
    combined_text: str


class InstructionLoader:
    def __init__(
        self,
        project_root: Path,
        working_directory: Path,
        *,
        global_file: Path | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.working_directory = working_directory.resolve()
        self.global_file = global_file.resolve() if global_file is not None else None

    def load(self) -> InstructionSet:
        if not self.project_root.is_dir():
            raise ValueError("project root must be a directory")
        try:
            relative_working = self.working_directory.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError("working directory must be within project root") from exc
        documents: list[InstructionDocument] = []
        seen: set[Path] = set()
        if self.global_file is not None:
            self._append_file(documents, seen, self.global_file, "global", allow_outside=True)
        directories = [self.project_root]
        current = self.project_root
        for part in relative_working.parts:
            current = current / part
            directories.append(current)
        for directory in directories:
            for name in INSTRUCTION_FILES:
                self._append_file(documents, seen, directory / name, "project")
            self._append_file(
                documents,
                seen,
                directory / ".rabbit-code" / "instructions.md",
                "project",
            )
        return InstructionSet(
            tuple(documents),
            "\n".join(document.content for document in documents),
        )

    def _append_file(
        self,
        documents: list[InstructionDocument],
        seen: set[Path],
        path: Path,
        scope: str,
        *,
        allow_outside: bool = False,
    ) -> None:
        resolved = path.resolve()
        if not allow_outside:
            try:
                resolved.relative_to(self.project_root)
            except ValueError:
                return
        if resolved in seen or not resolved.is_file():
            return
        seen.add(resolved)
        documents.append(
            InstructionDocument(resolved, scope, resolved.read_text(encoding="utf-8"))
        )
