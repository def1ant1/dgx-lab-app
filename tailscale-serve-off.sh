#!/usr/bin/env bash
set -euo pipefail
tailscale serve off
tailscale serve status || true
