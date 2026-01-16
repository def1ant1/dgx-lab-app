from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

from .config import Settings
from .security import resolve_and_check, ensure_is_dir


def _run_git(root: Path, args: List[str]) -> str:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if p.returncode != 0:
        stderr = (p.stderr or "").strip()
        stdout = (p.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr or stdout}")
    return p.stdout


def git_status(settings: Settings, root: str) -> str:
    rp = resolve_and_check(root, settings.allowed_roots)
    ensure_is_dir(rp)
    return _run_git(rp, ["status", "--porcelain=v1", "--branch"])


def git_diff(settings: Settings, root: str, staged: bool = False, path: Optional[str] = None, max_bytes: Optional[int] = None) -> str:
    rp = resolve_and_check(root, settings.allowed_roots)
    ensure_is_dir(rp)

    args = ["diff"]
    if staged:
        args.append("--staged")
    if path:
        args += ["--", path]

    out = _run_git(rp, args)
    cap = max_bytes if max_bytes is not None else settings.max_diff_bytes
    if len(out.encode("utf-8")) > cap:
        return out[:cap] + "\n\n[TRUNCATED]\n"
    return out


def git_log(settings: Settings, root: str, max_count: int = 20) -> str:
    rp = resolve_and_check(root, settings.allowed_roots)
    ensure_is_dir(rp)
    return _run_git(rp, ["log", f"-n{max_count}", "--oneline", "--decorate"])


def git_grep(settings: Settings, root: str, pattern: str, max_results: int = 50) -> str:
    rp = resolve_and_check(root, settings.allowed_roots)
    ensure_is_dir(rp)
    out = _run_git(rp, ["grep", "-n", "--no-color", pattern])
    lines = out.splitlines()
    if len(lines) > max_results:
        lines = lines[:max_results] + ["[TRUNCATED]"]
    return "\n".join(lines)
