from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SitemapEntry:
    slug: str
    url: str
    title: Optional[str]
    description: Optional[str]
    last_indexed_at: str


@dataclass
class PageDoc:
    slug: str
    url: str
    title: Optional[str]
    description: Optional[str]
    headings: List[str]
    content: str
