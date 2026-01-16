#!/usr/bin/env bash
set -euo pipefail

curl -sS -X POST "http://127.0.0.1:8080/api/stop" -H "Content-Type: application/json" -d '{}' || true

PID="$(lsof -ti:8080 || true)"
if [[ -n "${PID}" ]]; then
  kill "${PID}" || true
fi
