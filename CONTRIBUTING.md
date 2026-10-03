# Contributing

Use small branches named `codex/<topic>` or a conventional feature prefix. Commits follow Conventional Commits, with one coherent change per commit. Every stock mutation must preserve audit history and the non-negative quantity invariant. Do not introduce a direct product quantity setter.

Before proposing a change, run the backend Testcontainers suite, frontend type/unit/build checks, and the affected browser/API journeys. Change migrations by adding a new version, not rewriting an applied migration. Update the API contract and thesis evidence where behavior or claims change. Record benchmark workloads and raw measurements; avoid comparing numbers from different environments as though they were controlled experiments.

Keep `.env`, runtime folders, local database files, dependencies and generated compiler caches out of Git. Commit source diagrams, schema migrations, test fixtures, dependency lockfiles and approved screenshots. The final thesis PDF is a release asset; compile it locally with `thesis/build.sh` before release.
