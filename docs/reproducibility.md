# Reproducibility commands

```sh
# Infrastructure and local app
cp .env.example .env                 # change the local passwords
docker compose up -d --wait
./scripts/backend.sh test
cd frontend && npm ci && npm run check && npm test && npm run build
cd .. && python3 scripts/smoke.py
python3 scripts/warning-upgrade-smoke.py  # running demo environment; adds named demo records

# Editable diagrams and thesis PDF
python3 scripts/generate_diagrams.py
./thesis/build.sh
python3 scripts/inspect_thesis.py

# Exploratory cache comparison (requires running backend and demo user)
python3 scripts/benchmark.py --iterations 200 --output docs/evidence/cache-benchmark.json
```

`smoke.py` checks anonymous denial, all three role boundaries, idempotent replay/mismatch, negative-stock protection, warning review, and quantity persistence. `warning-upgrade-smoke.py` checks physical versus sellable balances, expiry rules, warning handling, replenishment approval, partial receipt/cancellation, request replay, disposal approval and cache agreement without resetting the database. It creates records with an `Upgrade demo` prefix. `frontend/src/inventory.spec.ts` tests zero and exact-threshold presentation boundaries. The benchmark records raw samples, machine/runtime metadata, medians, p95 and p99; it is descriptive evidence on this demonstration dataset only. Re-run it to replace the evidence JSON. The paper must report the accompanying workload and must not generalize the local numbers to supermarket production.

PDF inspection renders PNGs with Poppler and extracts text for page/placeholder/section checks. After recompiling, inspect the new cover, representative figure/table pages and final pages; automation alone cannot judge typography or composition.
