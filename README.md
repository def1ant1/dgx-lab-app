# DGX Local AI Dev Bundle (Ollama + Console + Website Connector + MCP)

This bundle packages:

1) **DGX Ollama Console** (FastAPI) – start/stop Ollama, inspect models/logs, and generate Claude Code env snippets.
2) **Apotheon Website Connector** (FastAPI) – local-first crawler/indexer + semantic search/recommend endpoints for your in-progress website.
3) **MCP Repo + Website Connector** – an MCP server that exposes repo/folder tools + website search/get/recommend tools to MCP clients.
4) **Tailscale helper scripts** – quick on/off for exposing the console over Tailnet.

---

## Quick start

### 0) Prereqs
- Ollama running on the DGX (`ollama serve`), with an embedding model pulled (default: `nomic-embed-text`).
- Python 3.10+.

Note on ports: This project avoids common dev ports used by websites (3000, 8000).
It binds to 8080 (console) and 8090 (connector) by default.

### 1) Start the DGX Ollama Console

```bash
make run-console
```

Console:
- UI: http://127.0.0.1:8080
- API: http://127.0.0.1:8080/api/status

Manual (without Makefile):
```
uvicorn dgx_ollama_console.main:app --app-dir . --host 127.0.0.1 --port 8080
```
Entrypoint: `dgx_ollama_console/main.py:1`

### 2) Generate Claude Code env exports (Ollama-backed)

Local (Claude Code running on DGX):
```bash
make claude-env-local
```

Tailscale (Claude Code running off-box):
```bash
make claude-env-tailscale
```

### 3) Start the Website Connector (crawler + index + retrieval API)

By default it crawls a local dev server at `http://127.0.0.1:5173`.

```bash
export CONNECTOR_TARGET_URL="http://127.0.0.1:5173"   # set your website base URL
make run-connector
```

Manual (without Makefile):
```
uvicorn apotheon_connector.app.main:app --app-dir . --host 127.0.0.1 --port 8090
```
Entrypoint: `apotheon_connector/app/main.py:1`

Connector API:
- http://127.0.0.1:8090/health
- POST http://127.0.0.1:8090/reindex (admin)
- POST http://127.0.0.1:8090/search
- GET  http://127.0.0.1:8090/page/{slug}
- GET  http://127.0.0.1:8090/sitemap
- POST http://127.0.0.1:8090/recommend

Additional Content Ops endpoints:
- GET  http://127.0.0.1:8090/changes
- POST http://127.0.0.1:8090/lint (admin)
- POST http://127.0.0.1:8090/clusters (admin)
- POST http://127.0.0.1:8090/export (admin)
- POST http://127.0.0.1:8090/daily-brief (admin)

### 4) Start the MCP server (repo + website tools)

This exposes:
- repo tools: list_dir, read_file, search_text, git_status, git_diff, git_log, git_grep
- website tools: get_sitemap, get_page, search_pages, recommend_content

```bash
export MCP_ALLOWED_ROOTS="/path/to/your/repo:/another/allowed/path"
export CONNECTOR_API_BASE="http://127.0.0.1:8090"
make run-mcp-stdio
```

---

## Security

### Bearer token

Set tokens to protect the Website Connector API:

```bash
export CONNECTOR_TOKEN="your-long-random-token"           # used by clients (e.g., MCP)
export CONNECTOR_ADMIN_TOKEN="your-long-random-admin-token" # optional; falls back to CONNECTOR_TOKEN
```

Then send `Authorization: Bearer <token>` to the connector endpoints.
The Website Connector accepts:
- read token from `CONNECTOR_READ_TOKEN` or `CONNECTOR_TOKEN`
- admin token from `CONNECTOR_ADMIN_TOKEN` or `CONNECTOR_TOKEN`

The MCP server forwards `CONNECTOR_TOKEN` automatically if set.

### Sandbox roots (MCP)

MCP is **deny-by-default**. Only paths in `MCP_ALLOWED_ROOTS` can be accessed.

---

## Local dev HTTPS tunnel (for ChatGPT Actions)

ChatGPT Actions and remote MCP clients generally require HTTPS. For local dev:
- Cloudflare Tunnel (`cloudflared`) or ngrok
- Point the tunnel at `http://127.0.0.1:8090` (connector) and/or `http://127.0.0.1:8080` (console)

Then use the tunnel URL as your `servers.url` in the OpenAPI schema.

---

## Components

### DGX Ollama Console
Location: `dgx_ollama_console/`

### Website Connector
Location: `apotheon_connector/`

- Uses **Chroma** for fast local persistent vector storage (`./.chroma`).
- Uses **Ollama embeddings** (default model: `nomic-embed-text`).

Environment variables:
- `CONNECTOR_TARGET_URL` (preferred) or `CONNECTOR_BASE_URL` – website base to crawl
- `CONNECTOR_CHROMA_DIR` – chroma storage directory (default: `./.chroma`)
- `CONNECTOR_TOKEN` / `CONNECTOR_READ_TOKEN` – bearer for read endpoints
- `CONNECTOR_ADMIN_TOKEN` – bearer for admin endpoints

### MCP Connector
Location: `mcp_repo_connector/`

---

## Scripts

- `scripts/claude-ollama` – runs Claude Code with env vars pointing to local Ollama.
- `scripts/claude-anthropic` – runs Claude Code without the Ollama base URL override (for future Anthropic use).
