#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[[ -f .env ]] || { cp .env.example .env; echo 'Edit .env with local passwords, then run this script again.'; exit 1; }
docker compose up -d --wait
./scripts/backend.sh spring-boot:run
