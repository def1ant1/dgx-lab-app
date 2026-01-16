from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Literal

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

from .process import ManagedProcess
from .ollama import list_models_cli, ollama_is_healthy, generate
from .network import tailscale_ipv4, tailscale_ipv6

APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parent
STATE_DIR = PROJECT_ROOT / ".state"
LOG_DIR = PROJECT_ROOT / ".logs"

# Used by the console for health checks and /api/infer.
# Claude Code will use ANTHROPIC_BASE_URL (see /api/claude-code/env).
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

proc = ManagedProcess(
    pidfile=STATE_DIR / "ollama.pid",
    stampfile=STATE_DIR / "ollama.started_at",
    logfile=LOG_DIR / "ollama.log",
)

app = FastAPI(title="DGX Ollama Console", version="0.2.0")


class InferReq(BaseModel):
    model: str
    prompt: str
    options: Optional[Dict[str, Any]] = None


def _status_payload() -> dict:
    st = proc.status()
    healthy = ollama_is_healthy(OLLAMA_BASE_URL)
    uptime_sec = None
    if st.running and st.started_at:
        uptime_sec = max(0, int(time.time() - st.started_at))

    ts4 = tailscale_ipv4()
    ts6 = tailscale_ipv6()

    return {
        "ollama": {
            "running": st.running,
            "pid": st.pid,
            "healthy": healthy,
            "base_url": OLLAMA_BASE_URL,
            "uptime_sec": uptime_sec,
        },
        "tailscale": {
            "ipv4": ts4,
            "ipv6": ts6,
            "hint": (f"http://{ts4}:8080" if ts4 else None),
        },
    }


def _claude_code_exports(base_url: str) -> str:
    # Claude Code uses Anthropic-compatible env vars.
    # For Ollama, API key/token values are ignored but required to be set.
    return "\n".join(
        [
            f'export ANTHROPIC_BASE_URL="{base_url}"',
            'export ANTHROPIC_API_KEY="ollama"',
            'export ANTHROPIC_AUTH_TOKEN="ollama"',
        ]
    )


def _safe_read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def _fallback_index_html() -> str:
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>DGX Ollama Console</title>
  <style>
    body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial; margin:24px;}
    code,pre{background:#f6f6f6; padding:2px 6px; border-radius:6px;}
    pre{padding:12px; overflow:auto;}
    .row{margin:10px 0;}
  </style>
</head>
<body>
  <h1>DGX Ollama Console</h1>
  <div class=\"row\">UI assets not found. API is available.</div>
  <ul>
    <li><code>GET /api/status</code></li>
    <li><code>POST /api/start</code>, <code>/api/stop</code>, <code>/api/restart</code></li>
    <li><code>GET /api/models</code></li>
    <li><code>POST /api/infer</code></li>
    <li><code>GET /api/claude-code/env?mode=local</code></li>
    <li><code>GET /api/claude-code/env?mode=tailscale</code></li>
  </ul>
</body>
</html>"""


@app.get("/health")
def health():
    return {"ok": True, "service": "dgx-ollama-console", "status": _status_payload()}


@app.get("/favicon.ico")
def favicon():
    svg_path = (PROJECT_ROOT / "ui" / "favicon.svg").resolve()
    svg = _safe_read_text(svg_path)
    if not svg:
        # minimal inline svg
        svg = """<svg xmlns='http://www.w3.org/2000/svg' width='64' height='64'>
<rect width='64' height='64' rx='12' fill='#111'/>
<text x='32' y='40' font-size='28' text-anchor='middle' fill='#fff'>O</text>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/", response_class=HTMLResponse)
def root():
    ui_path = (PROJECT_ROOT / "ui" / "index.html").resolve()
    html = _safe_read_text(ui_path)
    return html or _fallback_index_html()


@app.get("/api/status")
def status():
    return _status_payload()


@app.post("/api/start")
def start():
    proc.start()
    return {"ok": True, "status": _status_payload()}


@app.post("/api/stop")
def stop():
    proc.stop()
    return {"ok": True, "status": _status_payload()}


@app.post("/api/restart")
def restart():
    proc.restart()
    return {"ok": True, "status": _status_payload()}


@app.get("/api/models")
def models():
    items = list_models_cli()
    return {"models": [m.__dict__ for m in items]}


@app.get("/api/logs")
def logs(lines: int = 200):
    txt = proc.tail_log(lines=lines)
    return JSONResponse({"lines": txt.splitlines()})


@app.post("/api/infer")
def infer(req: InferReq):
    if not ollama_is_healthy(OLLAMA_BASE_URL):
        return JSONResponse(
            {"ok": False, "error": f"Ollama is not responding at {OLLAMA_BASE_URL}. Start it first."},
            status_code=409,
        )
    try:
        resp = generate(OLLAMA_BASE_URL, model=req.model, prompt=req.prompt, options=req.options)
        return {"ok": True, "response": resp}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.get("/api/claude-code/env")
def claude_code_env(
    mode: Literal["local", "tailscale"] = Query(default="local"),
    port: int = Query(default=11434, ge=1, le=65535),
):
    """Return copy/paste exports for running Claude Code against Ollama.

    - local: use http://127.0.0.1:<port> (Claude Code running on DGX)
    - tailscale: use http://<tailscale-ipv4>:<port> (Claude Code running off-box)

    Note: Ollama ignores API key/token values, but Claude Code expects them set.
    """
    if mode == "local":
        base = f"http://127.0.0.1:{port}"
        return {"mode": mode, "exports": _claude_code_exports(base)}

    ts4 = tailscale_ipv4()
    if not ts4:
        return JSONResponse({"ok": False, "error": "No Tailscale IPv4 detected. Is tailscale up?"}, status_code=409)

    base = f"http://{ts4}:{port}"
    return {"mode": mode, "exports": _claude_code_exports(base)}
