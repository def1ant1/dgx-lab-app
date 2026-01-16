from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .crawler import Page, crawl_build_folder, crawl_site
from .chunking import chunk_text
from .embeddings import EmbeddingClient
from ..storage.index_store import IndexStore
from ..storage.models import PageDoc, SitemapEntry
from ..storage.vectordb import VectorDB


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _chunk_id(slug: str, idx: int) -> str:
    return f"{slug}::chunk::{idx}"


def reindex(
    *,
    target_url: str | None,
    target_dir,
    vectordb: VectorDB,
    store: IndexStore,
    embedder: EmbeddingClient,
    max_pages: int,
    max_depth: int,
    chunk_chars: int,
    chunk_overlap: int,
) -> Dict[str, int]:
    """(Re)build the index from a URL or build folder."""

    if not target_url and not target_dir:
        raise ValueError("Set CONNECTOR_TARGET_URL or CONNECTOR_TARGET_DIR")

    pages: List[Page]
    if target_url:
        pages = crawl_site(target_url, max_pages=max_pages, max_depth=max_depth)
    else:
        pages = crawl_build_folder(target_dir)

    # Clear existing vectors for slugs that are being reindexed
    # (Simple approach: delete by prefix per slug.)
    for p in pages:
        vectordb.delete_by_prefix(f"{p.slug}::")

    total_chunks = 0

    for p in pages:
        content = p.body_text or ""
        doc = PageDoc(
            slug=p.slug,
            url=p.url,
            title=p.title,
            description=p.description,
            headings=p.headings,
            content=content,
        )
        entry = SitemapEntry(
            slug=p.slug,
            url=p.url,
            title=p.title,
            description=p.description,
            last_indexed_at=now_iso(),
        )
        store.upsert_page(doc, entry)

        chunks = chunk_text(content, max_chars=chunk_chars, overlap=chunk_overlap)
        if not chunks:
            continue

        ids = []
        docs = []
        metas = []
        for c in chunks:
            ids.append(_chunk_id(p.slug, c.index))
            docs.append(c.text)
            metas.append(
                {
                    "slug": p.slug,
                    "url": p.url,
                    "title": p.title or "",
                    "description": p.description or "",
                    "headings": p.headings[:10],
                    "chunk_index": c.index,
                }
            )

        embs = embedder.embed_many(docs)
        vectordb.upsert(ids=ids, documents=docs, embeddings=embs, metadatas=metas)
        total_chunks += len(ids)

    store.save()

    return {"pages": len(pages), "chunks": total_chunks}
