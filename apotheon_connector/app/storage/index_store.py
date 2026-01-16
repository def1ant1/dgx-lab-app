from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from .models import PageDoc, SitemapEntry


class IndexStore:
    """Stores lightweight per-page metadata outside the vector DB."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._pages_path = self.data_dir / "pages.json"
        self._sitemap_path = self.data_dir / "sitemap.json"

        self.pages: Dict[str, PageDoc] = {}
        self.sitemap: Dict[str, SitemapEntry] = {}
        self._load()

    def _load(self) -> None:
        if self._pages_path.exists():
            try:
                raw = json.loads(self._pages_path.read_text(encoding="utf-8"))
                for slug, obj in (raw or {}).items():
                    self.pages[slug] = PageDoc(**obj)
            except Exception:
                self.pages = {}

        if self._sitemap_path.exists():
            try:
                raw = json.loads(self._sitemap_path.read_text(encoding="utf-8"))
                for slug, obj in (raw or {}).items():
                    self.sitemap[slug] = SitemapEntry(**obj)
            except Exception:
                self.sitemap = {}

    def save(self) -> None:
        self._pages_path.write_text(json.dumps({k: asdict(v) for k, v in self.pages.items()}, indent=2), encoding="utf-8")
        self._sitemap_path.write_text(json.dumps({k: asdict(v) for k, v in self.sitemap.items()}, indent=2), encoding="utf-8")

    def upsert_page(self, doc: PageDoc, entry: SitemapEntry) -> None:
        self.pages[doc.slug] = doc
        self.sitemap[entry.slug] = entry

    def get_page(self, slug: str) -> Optional[PageDoc]:
        return self.pages.get(slug)

    def list_sitemap(self) -> List[SitemapEntry]:
        return sorted(self.sitemap.values(), key=lambda e: e.slug)
