from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    # Index targets (choose one)
    target_url: str | None
    target_dir: Path | None

    # Ollama
    ollama_base_url: str
    embed_model: str

    # Storage
    chroma_dir: Path

    # Security
    bearer_token: str | None

    # Indexing controls
    max_pages: int
    max_depth: int
    chunk_chars: int
    chunk_overlap: int

    @staticmethod
    def from_env() -> "Settings":
        target_url = os.environ.get("CONNECTOR_TARGET_URL")
        target_dir_raw = os.environ.get("CONNECTOR_TARGET_DIR")
        target_dir = Path(target_dir_raw).expanduser().resolve() if target_dir_raw else None

        return Settings(
            target_url=target_url,
            target_dir=target_dir,
            ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            embed_model=os.environ.get("CONNECTOR_EMBED_MODEL", "nomic-embed-text"),
            chroma_dir=Path(os.environ.get("CONNECTOR_CHROMA_DIR", "./.chroma")).expanduser().resolve(),
            bearer_token=os.environ.get("CONNECTOR_TOKEN"),
            max_pages=int(os.environ.get("CONNECTOR_MAX_PAGES", "200")),
            max_depth=int(os.environ.get("CONNECTOR_MAX_DEPTH", "3")),
            chunk_chars=int(os.environ.get("CONNECTOR_CHUNK_CHARS", "1200")),
            chunk_overlap=int(os.environ.get("CONNECTOR_CHUNK_OVERLAP", "200")),
        )
