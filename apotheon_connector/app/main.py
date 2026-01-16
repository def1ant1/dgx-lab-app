from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .core.config import Settings
from .core.auth import require_token
from .indexing.embeddings import EmbeddingClient
from .indexing.pipeline import reindex
from .storage.index_store import IndexStore
from .storage.vectordb import VectorDB


settings = Settings.from_env()

# Persistent stores
vectordb = VectorDB(persist_dir=settings.chroma_dir)
store = IndexStore(data_dir=settings.chroma_dir)
embedder = EmbeddingClient(base_url=settings.ollama_base_url, model=settings.embed_model)

app = FastAPI(title="Apotheon Website Connector", version="0.1.0")

auth_dep = require_token(settings)


class SearchReq(BaseModel):
    query: str
    limit: int = 8
    filters: Dict[str, Any] | None = None


class RecommendReq(BaseModel):
    goals: List[str]
    audience: str | None = None
    constraints: Dict[str, Any] | None = None


def _snippet(text: str, query: str, max_len: int = 220) -> str:
    q = query.lower().strip()
    if not q:
        return (text or "")[:max_len]
    low = (text or "").lower()
    idx = low.find(q)
    if idx == -1:
        return (text or "")[:max_len]
    start = max(0, idx - 60)
    end = min(len(text), idx + 160)
    return ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")


@app.get("/health")
def health():
    return {
        "ok": True,
        "target_url": settings.target_url,
        "target_dir": str(settings.target_dir) if settings.target_dir else None,
        "ollama_base_url": settings.ollama_base_url,
        "embed_model": settings.embed_model,
        "chroma_dir": str(settings.chroma_dir),
        "token_required": bool(settings.bearer_token),
    }


@app.post("/reindex")
def reindex_now(_: bool = Depends(auth_dep)):
    try:
        stats = reindex(
            target_url=settings.target_url,
            target_dir=settings.target_dir,
            vectordb=vectordb,
            store=store,
            embedder=embedder,
            max_pages=settings.max_pages,
            max_depth=settings.max_depth,
            chunk_chars=settings.chunk_chars,
            chunk_overlap=settings.chunk_overlap,
        )
        return {"ok": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sitemap")
def get_sitemap(_: bool = Depends(auth_dep)):
    return {"pages": [
        {
            "slug": e.slug,
            "url": e.url,
            "title": e.title,
            "description": e.description,
            "lastIndexedAt": e.last_indexed_at,
        }
        for e in store.list_sitemap()
    ]}


@app.get("/page/{slug}")
def get_page(slug: str, _: bool = Depends(auth_dep)):
    doc = store.get_page(slug)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")

    # Simple sections heuristic: return headings only. (You can extend later.)
    return {
        "slug": doc.slug,
        "url": doc.url,
        "title": doc.title,
        "description": doc.description,
        "headings": doc.headings,
        "content": doc.content,
        "sections": [{"heading": h, "text": ""} for h in doc.headings[:40]],
    }


@app.post("/search")
def search_pages(req: SearchReq, _: bool = Depends(auth_dep)):
    query_emb = embedder.embed(req.query)

    where = None
    if req.filters:
        # minimal support: filter by slug, url, title contains not supported by Chroma where;
        # allow exact match fields
        where = {k: v for k, v in req.filters.items() if isinstance(v, (str, int, float, bool))}

    results = vectordb.query(query_emb, n_results=max(1, min(req.limit, 50)), where=where)

    out = []
    for r in results:
        meta = r.metadata or {}
        slug = str(meta.get("slug") or "")
        title = str(meta.get("title") or "")
        headings = meta.get("headings") or []
        if not isinstance(headings, list):
            headings = []
        out.append(
            {
                "slug": slug,
                "url": meta.get("url"),
                "title": title,
                "score": float(1.0 / (1.0 + r.distance)),
                "snippet": _snippet(r.document, req.query),
                "matchedHeadings": headings,
            }
        )

    # Keyword boost pass: if a page title/headings contain query words, add/boost
    q_words = [w for w in req.query.lower().split() if len(w) >= 3]
    if q_words:
        seen = {x["slug"] for x in out if x.get("slug")}
        for e in store.list_sitemap():
            if e.slug in seen:
                continue
            hay = " ".join([e.title or "", e.description or ""]).lower()
            hit = sum(1 for w in q_words if w in hay)
            if hit >= max(1, len(q_words) // 2):
                out.append(
                    {
                        "slug": e.slug,
                        "url": e.url,
                        "title": e.title,
                        "score": 0.15 + 0.05 * hit,
                        "snippet": e.description or "",
                        "matchedHeadings": [],
                    }
                )

    out = sorted(out, key=lambda x: x.get("score", 0), reverse=True)[: req.limit]
    return {"results": out}


@app.post("/recommend")
def recommend_content(req: RecommendReq, _: bool = Depends(auth_dep)):
    recs: List[Dict[str, Any]] = []

    # 1) Gaps vs goals
    for goal in req.goals:
        sr = search_pages(SearchReq(query=goal, limit=3), True)  # auth bypass internal
        if len(sr.get("results", [])) < 1:
            slug = "-".join([w for w in goal.lower().split() if w.isalnum()])[:60] or "new-page"
            recs.append(
                {
                    "type": "new_page",
                    "title": goal,
                    "slugSuggestion": slug,
                    "rationale": "No strong matches found in the current local index for this goal/topic.",
                    "outline": [
                        "Problem statement / why it matters",
                        "Core explanation",
                        "Implementation / how it works",
                        "Examples / use cases",
                        "FAQ",
                        "CTA / next steps",
                    ],
                    "suggestedKeywords": [goal],
                    "proposedMeta": {
                        "metaTitle": goal[:60],
                        "metaDescription": f"Overview and guidance for {goal}."[:155],
                        "excerpt": f"A practical guide to {goal}."[:160],
                    },
                }
            )

    # 2) Thin pages
    for e in store.list_sitemap():
        doc = store.get_page(e.slug)
        if not doc:
            continue
        if len((doc.content or "").split()) < 250:
            recs.append(
                {
                    "type": "expand_page",
                    "title": doc.title or e.slug,
                    "slugSuggestion": e.slug,
                    "rationale": "Page appears thin (low word count) relative to typical pillar/solution pages.",
                    "outline": [
                        "Add concrete examples",
                        "Add implementation details",
                        "Add FAQs",
                        "Add internal links to related pages",
                    ],
                    "suggestedKeywords": [],
                    "proposedMeta": {},
                }
            )

    # 3) Internal linking suggestions (simple: recommend linking pages sharing tokens)
    # (Heuristic: list pairs with shared significant words in titles)
    titles = [(e.slug, (e.title or "").lower()) for e in store.list_sitemap() if e.title]
    for i in range(min(len(titles), 40)):
        slug_a, t_a = titles[i]
        toks_a = {w for w in t_a.split() if len(w) >= 5}
        if not toks_a:
            continue
        for j in range(i + 1, min(len(titles), 40)):
            slug_b, t_b = titles[j]
            toks_b = {w for w in t_b.split() if len(w) >= 5}
            inter = toks_a.intersection(toks_b)
            if len(inter) >= 2:
                recs.append(
                    {
                        "type": "internal_linking",
                        "title": f"Link {slug_a} ↔ {slug_b}",
                        "slugSuggestion": slug_a,
                        "rationale": f"Pages share topical terms: {', '.join(sorted(list(inter))[:6])}",
                        "outline": [],
                        "suggestedKeywords": [],
                        "proposedMeta": {},
                    }
                )

    # 4) Basic SEO metadata suggestions (missing descriptions)
    for e in store.list_sitemap():
        if not e.description:
            recs.append(
                {
                    "type": "seo_metadata",
                    "title": e.title or e.slug,
                    "slugSuggestion": e.slug,
                    "rationale": "Missing meta description. Add one to improve snippet quality and CTR.",
                    "outline": [],
                    "suggestedKeywords": [],
                    "proposedMeta": {
                        "metaTitle": (e.title or e.slug)[:60],
                        "metaDescription": f"Learn about {(e.title or e.slug)}."[:155],
                        "excerpt": "",
                    },
                }
            )

    # De-dupe by (type, slugSuggestion, title)
    seen = set()
    uniq = []
    for r in recs:
        k = (r.get("type"), r.get("slugSuggestion"), r.get("title"))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)

    return {"recommendations": uniq[:80]}
