#!/usr/bin/env bash
set -euo pipefail

REPORTS_DIR="${CONNECTOR_REPORTS_DIR:-./reports}"
RETENTION_DAYS="${CONNECTOR_RETENTION_DAYS:-14}"

if [ -d "$REPORTS_DIR" ]; then
  find "$REPORTS_DIR" -type f -name "daily-brief-*.md" -mtime "+${RETENTION_DAYS}" -print -delete || true
fi
