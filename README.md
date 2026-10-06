# Shelfwise — supermarket inventory and stock warnings

A single-store inventory application and an English software-engineering thesis. Spring Boot, Vue 3, MySQL and Redis form a modular monolith. All stock changes retain an actor, reason, before/after quantity and idempotency key.

## Quick start

Prerequisites: Docker Desktop or Docker Engine with the Docker Compose plugin. The container build supplies Java, Maven, Node.js, npm, Nginx, MySQL and Redis; Java, Maven and Node.js do not need to be installed on the deployment host.

```sh
cp .env.example .env
# Edit .env with local passwords; these are never committed.
docker compose up -d --build --wait
```

Open http://localhost:5173. The Compose stack builds and runs the Vue/Nginx frontend, Spring Boot backend, MySQL and Redis. With `DEMO_ENABLED=true`, the accounts `admin`, `manager`, and `clerk` use the password you supplied as `DEMO_PASSWORD`. Demo credentials are read only on initial creation; changing the environment does not overwrite existing accounts. Disable demonstration seeding for a real deployment. See [deployment](docs/deployment.md) for production setup, backups and recovery.

## Verification and artifacts

```sh
./scripts/backend.sh test
cd frontend && npm ci && npm run check && npm test && npm run build
```

The MySQL/Redis integration smoke, browser journeys, benchmark and thesis build commands are documented in [reproducibility](docs/reproducibility.md). Documentation includes [requirements](docs/requirements.md), [API](docs/api.md), [architecture](docs/architecture.md), and [evaluation](docs/evaluation.md). Thesis source and its compiled submission PDF are under `thesis/` and `dist/` respectively; build the PDF using `thesis/build.sh`.

The inventory upgrade adds batch receipts, FEFO/FIFO dispatch, sellable balances, expiry and slow-stock rules, an auditable warning center, replenishment/purchase approval and partial receipt, and reviewed counts/disposal. See [upgrade rules](docs/warning-expansion.md) and [release history](CHANGELOG.md). It remains an educational demonstrator; purchasing handles stock documents, not payments or accounting.

Identity fields in the thesis intentionally remain placeholders pending institutional requirements. The current thesis and screenshots describe the earlier release and have not yet been regenerated for this upgrade.
