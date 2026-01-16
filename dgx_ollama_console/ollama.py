from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class OllamaModel:
    name: str
    size: Optional[str] = None
    modified: Optional[str] = None


def ollama_is_healthy(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=1.0)
        return r.status_code == 200
    except Exception:
        return False


def list_models_cli() -> List[OllamaModel]:
    """Use `ollama list` so model listing works even when server is stopped."""
    try:
        out = subprocess.check_output(["ollama", "list"], text=True, stderr=subprocess.STDOUT)
    except Exception:
        return []

    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    if not lines:
        return []

    header = lines[0].lower()
    data_lines = lines[1:] if "name" in header and "size" in header else lines

    models: List[OllamaModel] = []
    for ln in data_lines:
        parts = ln.split()
        if not parts:
            continue

        name = parts[0]
        size = None
        modified = None

        for i in range(1, len(parts) - 1):
            if _looks_number(parts[i]) and parts[i + 1].upper() in {"KB", "MB", "GB", "TB"}:
                size = f"{parts[i]} {parts[i+1]}"
                if i + 2 < len(parts):
                    modified = " ".join(parts[i + 2 :])
                break

        models.append(OllamaModel(name=name, size=size, modified=modified))

    return models


def _looks_number(s: str) -> bool:
    try:
        float(s)
        return True
    except Exception:
        return False


def generate(base_url: str, model: str, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
    payload: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
    if options:
        payload["options"] = options

    r = requests.post(f"{base_url}/api/generate", json=payload, timeout=300)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "")
