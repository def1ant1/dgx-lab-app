from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class Page:
    slug: str
    url: str
    title: str | None
    description: str | None
    canonical_url: str | None
    headings: List[str]
    body_text: str
    last_fetched_at: str | None = None


def _slugify(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path.endswith("/"):
        path = path[:-1] or "/"
    slug = re.sub(r"[^a-zA-Z0-9/_-]+", "-", path).strip("-")
    slug = slug.strip("/")
    return slug or "home"


def _extract_page(url: str, html: str) -> Page:
    soup = BeautifulSoup(html, "html.parser")

    title = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    desc = None
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        desc = md.get("content").strip()

    canon = None
    cl = soup.find("link", attrs={"rel": lambda v: v and "canonical" in v})
    if cl and cl.get("href"):
        canon = cl.get("href").strip()

    headings: List[str] = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        t = tag.get_text(" ", strip=True)
        if t:
            headings.append(t)

    # Remove non-content elements
    for bad in soup(["script", "style", "noscript", "svg"]):
        bad.decompose()

    body = soup.get_text(" ", strip=True)

    return Page(
        slug=_slugify(url),
        url=url,
        title=title,
        description=desc,
        canonical_url=canon,
        headings=headings[:100],
        body_text=body,
    )


def crawl_site(base_url: str, max_pages: int = 200, max_depth: int = 3, timeout: int = 20) -> List[Page]:
    """Crawl a local-first site starting at base_url.

    Intended for localhost dev servers or a tunneled URL.
    """
    base_url = base_url.rstrip("/") + "/"
    origin = urlparse(base_url).netloc

    seen: Set[str] = set()
    q: List[Tuple[str, int]] = [(base_url, 0)]
    pages: List[Page] = []

    session = requests.Session()

    while q and len(pages) < max_pages:
        url, depth = q.pop(0)
        if url in seen or depth > max_depth:
            continue
        seen.add(url)

        try:
            r = session.get(url, timeout=timeout)
            if not r.ok or "text/html" not in (r.headers.get("content-type") or ""):
                continue
            page = _extract_page(url, r.text)
            pages.append(page)
        except Exception:
            continue

        # Discover links
        try:
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a"):
                href = a.get("href")
                if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                    continue
                nxt = urljoin(url, href)
                p = urlparse(nxt)
                if p.scheme not in {"http", "https"}:
                    continue
                if p.netloc != origin:
                    continue
                # strip fragment
                clean = nxt.split("#", 1)[0]
                if clean not in seen:
                    q.append((clean, depth + 1))
        except Exception:
            pass

    return pages


def crawl_build_folder(root: Path, max_files: int = 500) -> List[Page]:
    """Index HTML/Markdown from a build output folder."""
    root = root.expanduser().resolve()
    pages: List[Page] = []

    exts = {".html", ".htm", ".md", ".markdown"}
    for fp in sorted(root.rglob("*")):
        if len(pages) >= max_files:
            break
        if not fp.is_file() or fp.suffix.lower() not in exts:
            continue
        try:
            txt = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        url = fp.as_uri()
        if fp.suffix.lower() in {".md", ".markdown"}:
            # treat md as plain text; no HTML parsing
            title = fp.stem
            pages.append(Page(slug=str(fp.relative_to(root)).replace("/", "_"), url=url, title=title, description=None, canonical_url=None, headings=[], body_text=txt))
        else:
            pages.append(_extract_page(url, txt))

    return pages
