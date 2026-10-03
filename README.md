# Shelfwise — supermarket inventory and stock warnings

A single-store inventory application and an English software-engineering thesis. Spring Boot, Vue 3, MySQL and Redis form a modular monolith. All stock changes retain an actor, reason, before/after quantity and idempotency key.

## Quick start

Prerequisites: Java 21, Maven 3.9.9+, Node 22.12+ (tested version recorded in `docs/versions.md`), Docker Compose and a running Docker engine. macOS users may use Colima.

```sh
cp .env.example .env
# Edit .env with local passwords; these are never committed.
docker compose up -d --wait
./scripts/backend.sh spring-boot:run
# In a second terminal:
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. With `DEMO_ENABLED=true`, the accounts `admin`, `manager`, and `clerk` use the password you supplied as `DEMO_PASSWORD`. Demo credentials are read only on initial creation; changing the environment does not overwrite existing accounts. Disable demonstration seeding for a real deployment. See [deployment](docs/deployment.md) for production setup and recovery.

## Verification and artifacts

```sh
./scripts/backend.sh test
cd frontend && npm ci && npm run check && npm test && npm run build
```

The MySQL/Redis integration smoke, browser journeys, benchmark and thesis build commands are documented in [reproducibility](docs/reproducibility.md). Documentation includes [requirements](docs/requirements.md), [API](docs/api.md), [architecture](docs/architecture.md), and [evaluation](docs/evaluation.md). Thesis source and its compiled submission PDF are under `thesis/` and `dist/` respectively; build the PDF using `thesis/build.sh`.

Identity fields in the thesis intentionally remain placeholders pending institutional requirements. This is an educational demonstrator, not a procurement or accounting system.
