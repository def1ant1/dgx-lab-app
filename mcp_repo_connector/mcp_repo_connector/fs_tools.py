from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import List, Optional

from .config import Settings
from .security import resolve_and_check, ensure_is_dir, ensure_is_file


def list_dir(settings: Settings, path: str, max_entries: int = 200) -> List[dict]:
    rp = resolve_and_check(path, settings.allowed_roots)
    ensure_is_dir(rp)

    out: List[dict] = []
    for i, entry in enumerate(sorted(rp.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))):
        if i >= max_entries:
            break
        try:
            st = entry.stat()
            out.append({
                "name": entry.name,
                "path": str(entry),
                "type": "dir" if entry.is_dir() else "file",
                "size": st.st_size if entry.is_file() else None,
                "mtime": int(st.st_mtime),
            })
        except Exception:
            out.append({"name": entry.name, "path": str(entry), "type": "unknown"})
    return out


def read_file(settings: Settings, path: str, max_bytes: Optional[int] = None) -> str:
    rp = resolve_and_check(path, settings.allowed_roots)
    ensure_is_file(rp)

    cap = max_bytes if max_bytes is not None else settings.max_read_bytes
    with rp.open("rb") as f:
        data = f.read(cap + 1)
    if len(data) > cap:
        data = data[:cap]
        suffix = b"\n\n[TRUNCATED]\n"
        return (data + suffix).decode("utf-8", errors="replace")
    return data.decode("utf-8", errors="replace")


def _iter_files(root: Path, glob: Optional[str]) -> List[Path]:
    patterns = [glob] if glob else ["*.js", "*.ts", "*.jsx", "*.tsx", "*.css", "*.scss", "*.html", "*.md", "*.json", "*.yml", "*.yaml"]

    found: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"node_modules", ".git", ".next", "dist", "build"}]
        for fn in filenames:
            fp = Path(dirpath) / fn
            for pat in patterns:
                if fnmatch.fnmatch(fn, pat):
                    found.append(fp)
                    break
    return found


def search_text(settings: Settings, query: str, path: str, glob: Optional[str] = None, max_results: Optional[int] = None) -> List[dict]:
    rp = resolve_and_check(path, settings.allowed_roots)
    ensure_is_dir(rp)

    limit = max_results if max_results is not None else settings.max_search_results
    results: List[dict] = []

    files = _iter_files(rp, glob)
    q = query.lower()

    for fp in files:
        if len(results) >= limit:
            break
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            if q in line.lower():
                results.append({"file": str(fp), "line": idx, "text": line[:400]})
                if len(results) >= limit:
                    break

    return results
