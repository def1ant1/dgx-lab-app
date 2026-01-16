#!/usr/bin/env bash
set -euo pipefail

# Example:
# export CONNECTOR_TARGET_URL="http://127.0.0.1:5173"
# export CONNECTOR_TOKEN="..."
# export OLLAMA_BASE_URL="http://127.0.0.1:11434"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

make run-connector
