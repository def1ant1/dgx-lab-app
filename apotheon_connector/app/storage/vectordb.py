from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings


@dataclass
class SearchResult:
    id: str
    distance: float
    document: str
    metadata: Dict[str, Any]


class VectorDB:
    def __init__(self, persist_dir: Path, collection: str = "pages"):
        persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.col = self.client.get_or_create_collection(name=collection)

    def upsert(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        # Chroma requires aligned list lengths
        self.col.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def delete_by_prefix(self, prefix: str) -> None:
        # Chroma doesn't support prefix delete directly; fetch then delete.
        # For POC scale, it's fine.
        ids: List[str] = []
        offset = 0
        page = 500
        while True:
            resp = self.col.get(include=["metadatas"], limit=page, offset=offset)
            got = resp.get("ids", []) or []
            if not got:
                break
            for _id in got:
                if isinstance(_id, list):
                    for x in _id:
                        if x.startswith(prefix):
                            ids.append(x)
                else:
                    if str(_id).startswith(prefix):
                        ids.append(str(_id))
            offset += page
        if ids:
            self.col.delete(ids=ids)

    def query(
        self,
        embedding: List[float],
        n_results: int = 8,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        resp = self.col.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        docs = (resp.get("documents") or [[]])[0]
        metas = (resp.get("metadatas") or [[]])[0]
        dists = (resp.get("distances") or [[]])[0]
        ids = (resp.get("ids") or [[]])[0]

        out: List[SearchResult] = []
        for i in range(min(len(ids), len(docs), len(metas), len(dists))):
            out.append(SearchResult(id=str(ids[i]), distance=float(dists[i]), document=str(docs[i]), metadata=dict(metas[i] or {})))
        return out
