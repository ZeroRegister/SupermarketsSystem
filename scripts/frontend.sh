#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -d "$ROOT/.runtime/node-v22.16.0-darwin-arm64/bin" ]];then export PATH="$ROOT/.runtime/node-v22.16.0-darwin-arm64/bin:$PATH";fi
cd "$ROOT/frontend"
exec npm "$@"
