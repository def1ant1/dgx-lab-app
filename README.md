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

### 1) Start the DGX Ollama Console

```bash
make run-console
```

Console:
- UI: http://127.0.0.1:8080
- API: http://127.0.0.1:8080/api/status

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
export CONNECTOR_TARGET_URL="http://127.0.0.1:5173"   # change this
make run-connector
```

Connector API:
- http://127.0.0.1:8090/health
- POST http://127.0.0.1:8090/reindex
- POST http://127.0.0.1:8090/search
- GET  http://127.0.0.1:8090/page/{slug}
- GET  http://127.0.0.1:8090/sitemap
- POST http://127.0.0.1:8090/recommend

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

Set a token to protect the Website Connector API:

```bash
export CONNECTOR_TOKEN="your-long-random-token"
```

Then send `Authorization: Bearer <token>` to the connector endpoints. The MCP server will forward the token automatically if `CONNECTOR_TOKEN` is set.

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

### MCP Connector
Location: `mcp_repo_connector/`

---

## Scripts

- `scripts/claude-ollama` – runs Claude Code with env vars pointing to local Ollama.
- `scripts/claude-anthropic` – runs Claude Code without the Ollama base URL override (for future Anthropic use).

