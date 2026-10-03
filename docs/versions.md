# Version matrix and validation host

Pinned project baseline on 2026-10-04:

| Component | Version | Pin location |
|---|---:|---|
| Java | Temurin 21.0.12.1+1 | `.runtime` local only; production Java 21 LTS |
| Spring Boot | 3.5.16 | `backend/pom.xml` |
| Maven | 3.9.9 | local development wrapper under `.runtime` |
| Vue | 3.5.22 | `frontend/package.json` / lock |
| Vite | 7.3.6 | `frontend/package.json` / lock |
| Node | 22.16.0 | `.nvmrc` |
| npm | 10.9.2 | shipped with Node 22.16.0 |
| Element Plus | 2.11.5 | `frontend/package.json` / lock |
| MySQL | 8.4.8 | `docker-compose.yml` |
| Redis | 7.4.9 Alpine | `docker-compose.yml` |
| TeX Live | 2025 | host TeX installation; no generated files committed |
| Graphviz | 16.1.0 | editable source and generator in `scripts/` |

The repository wrapper downloads neither Java nor Maven. It uses task-local Java/Maven when present, otherwise the normal Java 21 and Maven on PATH; for a fresh checkout, install Java 21 and Maven 3.9.9+, then run `mvn` from `backend/`. Node is resolved through standard `nvm` use or system PATH. Docker image tags are explicit. `.runtime/`, `target/`, `node_modules/`, and output intermediates are ignored.

Validation platform: Apple Silicon macOS, Docker via Colima; local services published only on loopback (MySQL 3307, Redis 6380). TeX Live 2025 with pdfLaTeX/latexmk and Poppler for inspection. These results do not establish production behavior.
