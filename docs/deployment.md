# Local deployment, operations and recovery

## Local development

Install Java 21, Maven 3.9.9+, Node 22.16.0/npm 10, and Docker Compose. macOS authoring uses Colima when Docker Desktop is not active. Copy `.env.example` to `.env`, change all three passwords, and run:

```sh
docker compose up -d --wait
./scripts/start-local.sh
# second terminal
cd frontend && npm ci && npm run dev
```

The backend reads the repository `.env` through `scripts/backend.sh`. Direct `mvn` users export `DB_PASSWORD`, `DEMO_ENABLED` and `DEMO_PASSWORD` themselves. Vite proxies `/api` and `/actuator` to `localhost:8080`. Services bind to `127.0.0.1`; they are not exposed to a LAN.

Demonstration accounts are seeded only for an empty user table when `DEMO_ENABLED=true` and the supplied password has at least 12 characters. The same temporary password is used for `admin`, `manager`, and `clerk`. The seeder adds a fictitious product catalog and opening-stock transactions, never real user data. Turn off demonstration seeding before deployment; it does not reset existing passwords or add new users after the first administrator exists. Create real team members through the admin interface.

## Production hardening

Use a dedicated secrets manager, TLS reverse proxy, `SESSION_COOKIE_SECURE=true`, strong unique credentials, private MySQL/Redis networks, regular backups, and restore drills. Do not publish service ports. This prototype has no rate limiter, password reset workflow, email verification, MFA, multi-instance session store, or production threat review. Restrict deployment to a trusted internal network until those controls are added. The default servlet session store is in-process; restarting the sole application node logs users out.

## Backup and recovery

MySQL is authoritative. Back up the MySQL volume with a consistent database dump and store it away from the host. Before a schema change, capture a verified restore point; test restore against the same pinned MySQL major. `docker compose down` preserves the named volume. `docker compose down -v` deletes the database and must be treated as a destructive reset. Redis holds disposable warning response cache only; it can be recreated or restarted without changing inventory history. During a Redis outage, warning reads query MySQL directly and writes continue.
