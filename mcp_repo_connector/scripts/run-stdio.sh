#!/usr/bin/env bash
set -euo pipefail

# Example:
# export MCP_ALLOWED_ROOTS="/srv/www:/home/heath/projects"
export MCP_ALLOWED_ROOTS="${MCP_ALLOWED_ROOTS:-$(pwd)}"

# Retrieval API base (FastAPI) for website search/get/recommend tools
export CONNECTOR_API_BASE="${CONNECTOR_API_BASE:-http://127.0.0.1:8090}"

export MCP_TRANSPORT=stdio

python -m mcp_repo_connector.server
