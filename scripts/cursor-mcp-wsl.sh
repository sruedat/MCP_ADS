#!/usr/bin/env bash
# Arranque del servidor MCP bajo WSL (evita pasar rutas Windows crudas a bash -lc).
set -euo pipefail

# Raíz del repo: este script vive en scripts/
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# shellcheck disable=SC1091
source .venv-ads/bin/activate
export MCP_ADS_CONFIG_DIR="${REPO_ROOT}/examples/wsl-tc3"
export MCP_ADS_LOG_LEVEL="${MCP_ADS_LOG_LEVEL:-INFO}"

exec python -m mcp_ads
