#!/usr/bin/env bash
set -euo pipefail

export MCP_ALLOWED_ROOTS="${MCP_ALLOWED_ROOTS:-$(pwd)}"
export CONNECTOR_API_BASE="${CONNECTOR_API_BASE:-http://127.0.0.1:8090}"

export MCP_TRANSPORT=streamable-http

python -m mcp_repo_connector.server
