#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if git ls-files | rg '(^|/)(SPEC\.md|AGENTS\.md|CLAUDE\.md|\.env$|node_modules/|target/|\.runtime/|.*\.tsbuildinfo$)';then
 echo 'Private or generated files are tracked.' >&2; exit 1
fi
if git grep -n -E 'Demo-74x|local-root-7|local-app-9|gho_[A-Za-z0-9]{20,}|-----BEGIN .*PRIVATE KEY-----' -- . ':(exclude)scripts/check-clean.sh';then
 echo 'Potential local credential tracked.' >&2; exit 1
fi
echo 'PASS: private files, runtime data and local credential patterns are excluded.'
