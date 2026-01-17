from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

from .process import ManagedProcess
from .ollama import list_models_cli, ollama_is_healthy, generate
from .network import tailscale_ipv4, tailscale_ipv6

APP_ROOT = Path(__file__).resolve().parent
STATE_DIR = APP_ROOT / ".state"
LOG_DIR = APP_ROOT / ".logs"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

proc = ManagedProcess(
    pidfile=STATE_DIR / "ollama.pid",
    stampfile=STATE_DIR / "ollama.started_at",
    logfile=LOG_DIR / "ollama.log",
)

app = FastAPI(title="DGX Ollama Console", version="0.1.3")


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


@app.get("/health")
def health():
    # Simple health endpoint (so external checks don't spam 404s)
    return {"ok": True, "service": "dgx-ollama-console", "status": _status_payload()}


@app.get("/favicon.ico")
def favicon():
    svg_path = (APP_ROOT.parent / "ui" / "favicon.svg").resolve()
    svg = svg_path.read_text(encoding="utf-8")
    # Serve SVG with correct mime; browsers accept it as favicon.
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/", response_class=HTMLResponse)
def root():
    ui_path = (APP_ROOT.parent / "ui" / "index.html").resolve()
    return ui_path.read_text(encoding="utf-8")


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
