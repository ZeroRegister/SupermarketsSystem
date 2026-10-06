# Container deployment, operations and recovery

## Container deployment

Install Docker Desktop (macOS/Windows) or Docker Engine and the Docker Compose plugin (Linux). Java, Maven and Node.js are installed inside the build stages, so they are not required on the deployment host. Copy `.env.example` to `.env`, change all three passwords, and run:

```sh
cp .env.example .env
# Edit .env before starting; never commit it.
docker compose up -d --build --wait
```

Open `http://localhost:5173`. The `frontend` container serves the compiled Vue application through Nginx and proxies `/api` and `/actuator` to the `backend` container. The backend connects to MySQL and Redis through the private Compose network. The frontend is published on `127.0.0.1:5173`; MySQL and Redis are only bound to loopback ports for local diagnostics and host-development mode, while the backend remains internal to the stack.

The build uses two stages for each application: Maven compiles the Spring Boot jar and Node.js builds the Vue bundle, while the runtime containers contain only what is needed to run the result. `docker compose up -d --build --wait` is the complete build and start command.

To follow logs or stop the stack:

```sh
docker compose logs -f backend
docker compose ps
docker compose down                 # keeps the MySQL volume
docker compose down -v              # destructive: removes the database volume
```

## Host development mode

For hot-reload development, run only the infrastructure containers and start the applications on the host. This requires Java 21, Maven 3.9.9+, Node 22.16.0/npm 10 and Docker Compose:

```sh
docker compose up -d --wait mysql redis
./scripts/backend.sh spring-boot:run
# in a second terminal
cd frontend && npm ci && npm run dev
```

The Vite development proxy targets `localhost:8080`. Do not start the Compose `backend` and `frontend` services at the same time as this host mode unless you intentionally want both deployments.

## Prebuilt image delivery for Windows

For a recipient who should only install Docker Desktop, use the registry Compose file instead of building from source. The repository includes `.github/workflows/publish-images.yml`, which publishes the `backend` and `frontend` images to GitHub Container Registry when a version tag such as `v1.2.0` is pushed. The workflow uses the repository's `GITHUB_TOKEN`; no registry password is stored in the repository.

The maintainer publishes a release after pushing a tag:

```sh
git tag v1.2.0
git push origin v1.2.0
```

The GitHub repository owner must make the GHCR packages public for password-free pulls, or the recipient must sign in to GHCR with a GitHub token that has package read access. On the Windows deployment machine, copy `.env.release.example` to `.env.release`, replace the image prefix and passwords, then run in PowerShell:

```powershell
docker compose --env-file .env.release -f docker-compose.release.yml pull
docker compose --env-file .env.release -f docker-compose.release.yml up -d --wait
```

The recipient then opens `http://localhost:5173`. This route does not run Maven, npm or a local source build; Docker only downloads the prebuilt application images and the pinned MySQL/Redis images. Set `SHELFWISE_IMAGE_TAG` to a version such as `1.2.0` when the deployment should remain on a fixed release. The MySQL volume is still created locally and must be backed up separately.

Demonstration accounts are seeded only for an empty user table when `DEMO_ENABLED=true` and the supplied password has at least 12 characters. The same temporary password is used for `admin`, `manager`, and `clerk`. The seeder adds a fictitious product catalog and opening-stock transactions, never real user data. Turn off demonstration seeding before deployment; it does not reset existing passwords or add new users after the first administrator exists. Create real team members through the admin interface.

## Production hardening

Use a dedicated secrets manager, TLS reverse proxy in front of the frontend, `SESSION_COOKIE_SECURE=true`, strong unique credentials, private MySQL/Redis networks, regular backups, and restore drills. The provided Compose file binds the frontend to loopback for local delivery; change the binding only behind an approved reverse proxy and firewall. This prototype has no rate limiter, password reset workflow, email verification, MFA, multi-instance session store, or production threat review. Restrict deployment to a trusted internal network until those controls are added. The default servlet session store is in-process; restarting the sole application node logs users out.

## Backup and recovery

MySQL is authoritative. Create a logical backup from the running container and store it away from the host:

```sh
docker compose exec -T mysql sh -c 'exec mysqldump -ushelfwise -p"$MYSQL_PASSWORD" shelfwise' > shelfwise-backup.sql
```

Before a schema change, capture a verified restore point and test restore against the same pinned MySQL major. `docker compose down` preserves the named volume. `docker compose down -v` deletes the database and must be treated as a destructive reset. Redis holds disposable warning response cache only; it can be recreated or restarted without changing inventory history. During a Redis outage, warning reads query MySQL directly and writes continue.
