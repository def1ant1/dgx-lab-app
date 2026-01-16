#!/usr/bin/env bash
set -euo pipefail
tailscale serve 8080
tailscale serve status
