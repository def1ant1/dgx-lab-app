from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    text: str
    index: int


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 200) -> List[Chunk]:
    clean = "\n".join([ln.strip() for ln in text.splitlines() if ln.strip()])
    if not clean:
        return []

    chunks: List[Chunk] = []
    start = 0
    idx = 0
    n = len(clean)

    while start < n:
        end = min(n, start + max_chars)
        part = clean[start:end]
        chunks.append(Chunk(text=part, index=idx))
        idx += 1
        if end >= n:
            break
        start = max(0, end - overlap)

    return chunks
