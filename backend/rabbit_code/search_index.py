from __future__ import annotations

import fnmatch
import hashlib
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from queue import Full, Queue
from threading import Event, Lock, Thread
from typing import Literal

# RC ID: RC-083. Build a bounded, cancellable, incremental workspace search index.


class SearchCancelled(RuntimeError):
    pass


@dataclass(frozen=True)
class SearchEntry:
    path: Path
    size_bytes: int
    sha256: str
    binary: bool = False


ScanStatus = Literal["queued", "running", "completed", "cancelled", "failed"]


@dataclass
class _BackgroundScanState:
    status: ScanStatus = "queued"
    entries: tuple[SearchEntry, ...] = ()
    error: BaseException | None = None


class BackgroundScan:
    def __init__(self, cancellation: Event, state: _BackgroundScanState, done: Event) -> None:
        self._cancellation = cancellation
        self._state = state
        self._done = done

    @property
    def status(self) -> ScanStatus:
        return self._state.status

    @property
    def entries(self) -> tuple[SearchEntry, ...]:
        return self._state.entries

    def cancel(self) -> None:
        self._cancellation.set()

    def wait(self, timeout: float | None = None) -> tuple[SearchEntry, ...]:
        if not self._done.wait(timeout):
            raise TimeoutError("background search scan did not finish before timeout")
        if self._state.error is not None:
            raise self._state.error
        return self._state.entries


class SafeSearchIndexer:
    def __init__(
        self,
        workspace_root: Path,
        *,
        user_exclusions: Sequence[str] = (),
        max_file_bytes: int = 1_000_000,
        max_queue_size: int = 128,
    ) -> None:
        if max_file_bytes <= 0:
            raise ValueError("max_file_bytes must be positive")
        if max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive")
        self.workspace_root = workspace_root.resolve()
        self.user_exclusions = tuple(user_exclusions)
        self.max_file_bytes = max_file_bytes
        self.max_queue_size = max_queue_size
        self._cache: dict[Path, tuple[int, int, SearchEntry]] = {}
        self._contents: dict[Path, str] = {}
        self._entries: tuple[SearchEntry, ...] = ()
        self._rejections: dict[Path, str] = {}
        self._state_lock = Lock()
        self.read_count = 0

    @property
    def entries(self) -> tuple[SearchEntry, ...]:
        return self._entries

    @property
    def rejections(self) -> dict[Path, str]:
        return dict(self._rejections)

    def scan(self, *, cancellation: Event | None = None) -> tuple[SearchEntry, ...]:
        return self._scan_paths(self.workspace_root.rglob("*"), cancellation=cancellation)

    def start_background_scan(self, *, cancellation: Event | None = None) -> BackgroundScan:
        stop = cancellation or Event()
        state = _BackgroundScanState()
        done = Event()
        handle = BackgroundScan(stop, state, done)

        def run() -> None:
            if stop.is_set():
                state.status = "cancelled"
                state.error = SearchCancelled("background search scan was cancelled")
                done.set()
                return
            state.status = "running"
            path_queue: Queue[Path | None] = Queue(maxsize=self.max_queue_size)

            def produce() -> None:
                try:
                    for path in self.workspace_root.rglob("*"):
                        if stop.is_set():
                            return
                        while True:
                            try:
                                path_queue.put(path, timeout=0.05)
                                break
                            except Full:
                                if stop.is_set():
                                    return
                finally:
                    while not stop.is_set():
                        try:
                            path_queue.put(None, timeout=0.05)
                            break
                        except Full:
                            continue

            producer = Thread(target=produce, name="rabbit-search-producer", daemon=True)
            producer.start()
            try:
                state.entries = self._scan_paths(_queued_paths(path_queue), cancellation=stop)
                state.status = "cancelled" if stop.is_set() else "completed"
            except SearchCancelled as exc:
                state.status = "cancelled"
                state.error = exc
            except BaseException as exc:
                state.status = "failed"
                state.error = exc
            finally:
                if state.status in {"cancelled", "failed"}:
                    stop.set()
                producer.join(timeout=1)
                done.set()

        Thread(target=run, name="rabbit-search-consumer", daemon=True).start()
        return handle

    def _scan_paths(
        self,
        paths: Iterable[Path],
        *,
        cancellation: Event | None = None,
    ) -> tuple[SearchEntry, ...]:
        patterns = self._patterns()
        entries: list[SearchEntry] = []
        contents: dict[Path, str] = {}
        rejections: dict[Path, str] = {}
        for path in paths:
            if cancellation is not None and cancellation.is_set():
                raise SearchCancelled("search scan cancelled")
            if not path.is_file():
                continue
            if path.is_symlink():
                rejections[path] = "symlink"
                continue
            relative = path.relative_to(self.workspace_root).as_posix()
            if (
                path.name in {".gitignore", ".rabbitignore"}
                or self._is_sensitive(path)
                or self._matches(relative, patterns)
            ):
                rejections[path] = "ignored"
                continue
            stat = path.stat()
            if stat.st_size > self.max_file_bytes:
                rejections[path] = "large"
                continue
            cached = self._cache.get(path)
            if cached is not None and cached[:2] == (stat.st_mtime_ns, stat.st_size):
                entry = cached[2]
                entries.append(entry)
                contents[path] = self._contents[path]
                continue
            data = path.read_bytes()
            self.read_count += 1
            if b"\x00" in data:
                rejections[path] = "binary"
                continue
            digest = hashlib.sha256(data).hexdigest()
            entry = SearchEntry(path, stat.st_size, digest)
            entries.append(entry)
            contents[path] = data.decode("utf-8", errors="replace")
            self._cache[path] = (stat.st_mtime_ns, stat.st_size, entry)
        with self._state_lock:
            self._entries = tuple(sorted(entries, key=lambda entry: entry.path))
            self._contents = contents
            self._rejections = rejections
            return self._entries

    def search(self, query: str) -> tuple[Path, ...]:
        if not query:
            return ()
        needle = query.casefold()
        return tuple(
            path for path in self._entries_paths() if needle in self._contents[path].casefold()
        )

    def _entries_paths(self) -> tuple[Path, ...]:
        return tuple(entry.path for entry in self._entries)

    def _patterns(self) -> tuple[str, ...]:
        patterns = list(self.user_exclusions)
        for filename in (".gitignore", ".rabbitignore"):
            path = self.workspace_root / filename
            if not path.is_file():
                continue
            patterns.extend(
                line.strip()
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            )
        return tuple(patterns)

    @staticmethod
    def _matches(relative: str, patterns: Iterable[str]) -> bool:
        for pattern in patterns:
            normalized = pattern.removeprefix("/")
            if normalized.endswith("/"):
                normalized = normalized.rstrip("/")
                if relative == normalized or relative.startswith(normalized + "/"):
                    return True
            elif fnmatch.fnmatch(relative, normalized) or fnmatch.fnmatch(
                Path(relative).name, normalized
            ):
                return True
        return False

    @staticmethod
    def _is_sensitive(path: Path) -> bool:
        sensitive_names = {".env", "credentials.json", "id_rsa", "id_ed25519"}
        return path.name in sensitive_names or path.name.startswith(".env.") or ".ssh" in path.parts


def _queued_paths(path_queue: Queue[Path | None]) -> Iterator[Path]:
    while True:
        path = path_queue.get()
        if path is None:
            return
        yield path
