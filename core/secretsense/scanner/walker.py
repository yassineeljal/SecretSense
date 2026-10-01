"""Bounded traversal with nested .gitignore rules and no symlink following."""

import os
import stat
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from pathspec import GitIgnoreSpec

EXCLUDED_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".next",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
        "vendor",
    }
)


@dataclass
class WalkState:
    visited: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def walk_files(root: Path, state: WalkState, max_files: int) -> Iterator[Path]:
    """Apply ignores relative to each directory; never re-enter excluded parents."""
    if root.is_symlink():
        raise ValueError("The scan target must not be a symbolic link.")
    if root.is_file():
        state.visited = 1
        yield root
        return
    if not root.is_dir():
        raise ValueError("The scan target must be an existing regular file or directory.")

    def visit(directory: Path, inherited: list[tuple[Path, GitIgnoreSpec]]) -> Iterator[Path]:
        if len(directory.relative_to(root).parts) > 128:
            state.errors.append("Directory depth limit reached; the scan is incomplete.")
            return
        specs = inherited.copy()
        ignore = directory / ".gitignore"
        try:
            if ignore.is_file() and not ignore.is_symlink():
                # Ignore configuration is also untrusted input and must be bounded.
                with ignore.open("rb") as stream:
                    raw = stream.read(1_048_577)
                if len(raw) > 1_048_576:
                    state.errors.append("A .gitignore exceeds the 1 MiB configuration limit.")
                else:
                    specs.append(
                        (directory, GitIgnoreSpec.from_lines(raw.decode("utf-8").splitlines()))
                    )
            with os.scandir(directory) as entries:
                for entry in entries:
                    if state.visited >= max_files:
                        state.errors.append("File traversal limit reached; the scan is incomplete.")
                        return
                    state.visited += 1
                    path = Path(entry.path)
                    if entry.is_symlink():
                        state.skipped += 1
                        continue
                    is_dir = entry.is_dir(follow_symlinks=False)
                    if is_dir and entry.name in EXCLUDED_DIRS:
                        state.skipped += 1
                        continue
                    ignored = False
                    for base, spec in specs:
                        name = path.relative_to(base).as_posix() + ("/" if is_dir else "")
                        match = spec.check_file(name)
                        if match.include is not None:
                            ignored = match.include
                    if ignored:
                        state.skipped += 1
                    elif is_dir:
                        yield from visit(path, specs)
                    elif entry.is_file(follow_symlinks=False):
                        yield path
                    else:
                        state.skipped += 1
        except (OSError, UnicodeError, ValueError):
            # Avoid exception strings: filenames or malformed patterns can contain secrets.
            state.errors.append("Unable to read a directory or its .gitignore configuration.")

    yield from visit(root, [])


def read_text(path: Path, max_bytes: int) -> str | None:
    """Read at most max_bytes + 1; skip binary, non-UTF-8 and oversized input."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
            return None
        raw = stream.read(max_bytes + 1)
    if len(raw) > max_bytes or b"\x00" in raw:
        return None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None
