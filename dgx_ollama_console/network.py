from __future__ import annotations

import subprocess
from typing import List


def _run(cmd: List[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception:
        return ""


def tailscale_ipv4() -> str:
    out = _run(["tailscale", "ip", "-4"])
    return (out.splitlines()[0].strip() if out else "")


def tailscale_ipv6() -> str:
    out = _run(["tailscale", "ip", "-6"])
    return (out.splitlines()[0].strip() if out else "")


def tailscale_status_short() -> str:
    return _run(["tailscale", "status", "--peers=false"])
