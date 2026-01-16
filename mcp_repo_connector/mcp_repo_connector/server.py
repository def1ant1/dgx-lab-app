from __future__ import annotations

import os
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from .config import Settings
from .fs_tools import list_dir as _list_dir, read_file as _read_file, search_text as _search_text
from .git_tools import git_status as _git_status, git_diff as _git_diff, git_log as _git_log, git_grep as _git_grep
from .website_client import get_sitemap as _get_sitemap, get_page as _get_page, search_pages as _search_pages, recommend_content as _recommend_content

settings = Settings.from_env()

mcp = FastMCP("Apotheon Repo + Website Connector", json_response=True)

# ---- Repo / folder tools ----

@mcp.tool()
def list_dir(path: str, max_entries: int = 200):
    """List a directory (sandboxed to MCP_ALLOWED_ROOTS)."""
    return _list_dir(settings, path, max_entries=max_entries)

@mcp.tool()
def read_file(path: str, max_bytes: Optional[int] = None):
    """Read a file (sandboxed to MCP_ALLOWED_ROOTS)."""
    return _read_file(settings, path, max_bytes=max_bytes)

@mcp.tool()
def search_text(query: str, path: str, glob: Optional[str] = None, max_results: Optional[int] = None):
    """Search for text within a folder tree (skips node_modules/.git)."""
    return _search_text(settings, query, path, glob=glob, max_results=max_results)

@mcp.tool()
def git_status(root: str):
    """git status --porcelain (sandboxed root)."""
    return _git_status(settings, root)

@mcp.tool()
def git_diff(root: str, staged: bool = False, path: Optional[str] = None, max_bytes: Optional[int] = None):
    """git diff (optionally staged) with truncation."""
    return _git_diff(settings, root, staged=staged, path=path, max_bytes=max_bytes)

@mcp.tool()
def git_log(root: str, max_count: int = 20):
    """git log --oneline."""
    return _git_log(settings, root, max_count=max_count)

@mcp.tool()
def git_grep(root: str, pattern: str, max_results: int = 50):
    """git grep pattern (line numbers)."""
    return _git_grep(settings, root, pattern=pattern, max_results=max_results)

# ---- Website connector tools (thin wrapper over Retrieval API) ----

@mcp.tool()
def get_sitemap():
    """List indexed pages and metadata (calls GET /sitemap)."""
    return _get_sitemap(settings)

@mcp.tool()
def get_page(slug: str):
    """Fetch a page's structured content (calls GET /page/{slug})."""
    return _get_page(settings, slug)

@mcp.tool()
def search_pages(query: str, limit: int = 8, filters: Optional[Dict[str, Any]] = None):
    """Semantic search across indexed pages (calls POST /search)."""
    return _search_pages(settings, query=query, limit=limit, filters=filters)

@mcp.tool()
def recommend_content(goals, audience: Optional[str] = None, constraints: Optional[Dict[str, Any]] = None):
    """Recommend new pages, improvements, and internal links (calls POST /recommend)."""
    return _recommend_content(settings, goals=goals, audience=audience, constraints=constraints)


def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport not in {"stdio", "streamable-http"}:
        transport = "stdio"
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
