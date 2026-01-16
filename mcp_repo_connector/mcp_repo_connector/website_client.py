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


def get_changes(settings: Settings, since: Optional[str] = None) -> Dict[str, Any]:
    params = {"since": since} if since else None
    r = requests.get(f"{settings.connector_api_base}/changes", params=params, headers=_headers(settings), timeout=30)
    r.raise_for_status()
    return r.json()


def lint_site(settings: Settings, thin_word_threshold: int = 250, scope_slugs: Optional[list[str]] = None) -> Dict[str, Any]:
    payload = {"thinWordThreshold": thin_word_threshold, "scopeSlugs": scope_slugs}
    r = requests.post(f"{settings.connector_api_base}/lint", json=payload, headers=_headers(settings), timeout=60)
    r.raise_for_status()
    return r.json()


def cluster_topics(settings: Settings, max_pages: int = 300, similarity_threshold: float = 0.35) -> Dict[str, Any]:
    payload = {"maxPages": max_pages, "similarityThreshold": similarity_threshold}
    r = requests.post(f"{settings.connector_api_base}/clusters", json=payload, headers=_headers(settings), timeout=60)
    r.raise_for_status()
    return r.json()


def export_page(settings: Settings, title: str, slug_suggestion: str, outline: list[str], proposed_meta: Dict[str, Any], write: bool = False) -> Dict[str, Any]:
    payload = {"title": title, "slugSuggestion": slug_suggestion, "outline": outline, "proposedMeta": proposed_meta, "write": write}
    r = requests.post(f"{settings.connector_api_base}/export", json=payload, headers=_headers(settings), timeout=60)
    r.raise_for_status()
    return r.json()


def daily_brief(settings: Settings, goals: Optional[list[str]] = None, audience: Optional[str] = None) -> Dict[str, Any]:
    payload = {"goals": goals, "audience": audience}
    r = requests.post(f"{settings.connector_api_base}/daily-brief", json=payload, headers=_headers(settings), timeout=60)
    r.raise_for_status()
    return r.json()
