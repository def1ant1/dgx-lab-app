from __future__ import annotations

from pathlib import Path
from typing import Iterable


class PathDenied(Exception):
    pass


def resolve_and_check(path: str, allowed_roots: Iterable[Path]) -> Path:
    p = Path(path).expanduser()
    try:
        rp = p.resolve(strict=False)
    except Exception:
        rp = p.absolute()

    roots = [r.resolve() for r in allowed_roots]
    for root in roots:
        if rp == root or str(rp).startswith(str(root) + "/"):
            return rp

    raise PathDenied(f"Path is outside allowed roots: {rp}")


def ensure_is_dir(p: Path) -> None:
    if not p.exists() or not p.is_dir():
        raise FileNotFoundError(f"Directory not found: {p}")


def ensure_is_file(p: Path) -> None:
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"File not found: {p}")
