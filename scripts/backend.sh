#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # Local .env is a shell-compatible file copied from .env.example.
  source "$ROOT/.env"
  set +a
fi
export DB_PASSWORD="${DB_PASSWORD:-${MYSQL_PASSWORD:-}}"
export DEMO_PASSWORD="${DEMO_PASSWORD:-}"
export DEMO_ENABLED="${DEMO_ENABLED:-false}"
if [[ -z "${JAVA_HOME:-}" && -d "$ROOT/.runtime/jdk-21.0.12.1+1/Contents/Home" ]];then
 export JAVA_HOME="$ROOT/.runtime/jdk-21.0.12.1+1/Contents/Home"
elif [[ -z "${JAVA_HOME:-}" && "$(uname)" == Darwin ]];then
 export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
fi
export PATH="${JAVA_HOME:+$JAVA_HOME/bin:}$ROOT/.runtime/apache-maven-3.9.9/bin:$PATH"
cd "$ROOT/backend"
exec mvn "$@"
