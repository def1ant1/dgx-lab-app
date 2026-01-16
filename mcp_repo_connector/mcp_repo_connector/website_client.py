from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from .config import Settings


def _headers(settings: Settings) -> Dict[str, str]:
    if settings.connector_bearer_token:
        return {"Authorization": f"Bearer {settings.connector_bearer_token}"}
    return {}


def get_sitemap(settings: Settings) -> Dict[str, Any]:
    r = requests.get(f"{settings.connector_api_base}/sitemap", headers=_headers(settings), timeout=30)
    r.raise_for_status()
    return r.json()


def get_page(settings: Settings, slug: str) -> Dict[str, Any]:
    r = requests.get(f"{settings.connector_api_base}/page/{slug}", headers=_headers(settings), timeout=30)
    r.raise_for_status()
    return r.json()


def search_pages(settings: Settings, query: str, limit: int = 8, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {"query": query, "limit": limit, "filters": filters}
    r = requests.post(f"{settings.connector_api_base}/search", json=payload, headers=_headers(settings), timeout=60)
    r.raise_for_status()
    return r.json()


def recommend_content(settings: Settings, goals, audience: Optional[str] = None, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {"goals": goals, "audience": audience, "constraints": constraints}
    r = requests.post(f"{settings.connector_api_base}/recommend", json=payload, headers=_headers(settings), timeout=60)
    r.raise_for_status()
    return r.json()
