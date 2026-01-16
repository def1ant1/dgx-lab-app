from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProcStatus:
    running: bool
    pid: Optional[int]
    started_at: Optional[float]
    cmd: Optional[str]


class ManagedProcess:
    """Minimal supervisor for `ollama serve` (subprocess-managed)."""

    def __init__(self, pidfile: Path, stampfile: Path, logfile: Path, workdir: Optional[Path] = None):
        self.pidfile = pidfile
        self.stampfile = stampfile
        self.logfile = logfile
        self.workdir = workdir
        self.pidfile.parent.mkdir(parents=True, exist_ok=True)
        self.logfile.parent.mkdir(parents=True, exist_ok=True)

    def _read_pid(self) -> Optional[int]:
        try:
            raw = self.pidfile.read_text().strip()
            return int(raw) if raw else None
        except Exception:
            return None

    def _is_pid_running(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def status(self) -> ProcStatus:
        pid = self._read_pid()
        if pid and self._is_pid_running(pid):
            started_at = None
            try:
                started_at = float(self.stampfile.read_text().strip())
            except Exception:
                pass
            return ProcStatus(True, pid, started_at, "ollama serve")
        return ProcStatus(False, None, None, None)

    def start(self, env: Optional[dict] = None) -> ProcStatus:
        st = self.status()
        if st.running:
            return st

        log_f = open(self.logfile, "a", buffering=1)
        p = subprocess.Popen(
            ["ollama", "serve"],
            stdout=log_f,
            stderr=log_f,
            cwd=str(self.workdir) if self.workdir else None,
            env={**os.environ, **(env or {})},
            preexec_fn=os.setsid,
        )
        self.pidfile.write_text(str(p.pid))
        self.stampfile.write_text(str(time.time()))
        return self.status()

    def stop(self, timeout_sec: float = 8.0) -> ProcStatus:
        st = self.status()
        if not st.running or not st.pid:
            self._cleanup_files()
            return self.status()

        pid = st.pid
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            self._cleanup_files()
            return self.status()

        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            if not self._is_pid_running(pid):
                self._cleanup_files()
                return self.status()
            time.sleep(0.15)

        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

        time.sleep(0.2)
        self._cleanup_files()
        return self.status()

    def restart(self) -> ProcStatus:
        self.stop()
        return self.start()

    def tail_log(self, lines: int = 200) -> str:
        try:
            content = self.logfile.read_text(errors="ignore").splitlines()
            return "\n".join(content[-lines:])
        except FileNotFoundError:
            return ""
        except Exception as e:
            return f"[log read error] {e}"

    def _cleanup_files(self) -> None:
        for p in [self.pidfile, self.stampfile]:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass
