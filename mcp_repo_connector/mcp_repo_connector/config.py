from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


def _split_roots(raw: str) -> List[str]:
    parts = [p.strip() for p in raw.replace(";", ":").split(":")]
    return [p for p in parts if p]


@dataclass(frozen=True)
class Settings:
    allowed_roots: List[Path]
    max_read_bytes: int
    max_diff_bytes: int
    max_search_results: int

    # Website connector
    connector_api_base: str
    connector_bearer_token: str | None

    @staticmethod
    def from_env() -> "Settings":
        roots_raw = os.environ.get("MCP_ALLOWED_ROOTS", "")
        if not roots_raw:
            roots = [Path.cwd().resolve()]
        else:
            roots = [Path(p).expanduser().resolve() for p in _split_roots(roots_raw)]

        return Settings(
            allowed_roots=roots,
            max_read_bytes=int(os.environ.get("MCP_MAX_READ_BYTES", "200000")),
            max_diff_bytes=int(os.environ.get("MCP_MAX_DIFF_BYTES", "300000")),
            max_search_results=int(os.environ.get("MCP_MAX_SEARCH_RESULTS", "50")),
            connector_api_base=os.environ.get("CONNECTOR_API_BASE", "http://127.0.0.1:8090").rstrip("/"),
            connector_bearer_token=os.environ.get("CONNECTOR_TOKEN"),
        )
