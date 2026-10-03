# REST API contract

Base path `/api`; JSON request/response bodies, UTF-8, timestamps are UTC ISO-8601. Sessions use `JSESSIONID`; first call `GET /auth/csrf`, preserve `XSRF-TOKEN`, and include that value in `X-XSRF-TOKEN` on every unsafe method. `GET /auth/me` returns the current user. Login is `POST /auth/login` with `{ "username", "password" }`; logout is `POST /auth/logout`. Passwords are never returned. Authentication failures return 401; permission failures return 403; missing IDs return 404; business conflicts return 409; Bean Validation/bounds errors return 400.

| Method | Path | Roles | Purpose |
|---|---|---|---|
| GET | `/auth/csrf`, `/auth/me` | anonymous / signed in | issue CSRF / current user |
| POST | `/auth/login`, `/auth/logout` | anonymous / signed in | sign in/out |
| GET | `/dashboard`, `/reports/summary` | admin, manager | current metrics and recent activity |
| GET | `/products` | any signed-in user | filter/search/sort/paginate; `q`, `categoryId`, `status`, `archived`, `page`, `size`, `sort`, `direction` |
| GET | `/products/{id}` | any signed-in user | product details |
| POST/PUT/DELETE | `/products[/{id}]` | admin | create/update/archive catalog record; quantity is read-only |
| GET/POST | `/categories`, `/suppliers` | signed in / admin | list or add classification/partner |
| GET | `/transactions` | signed in | newest movements, optionally filtered by `productId` |
| POST | `/transactions` | admin, clerk | receive, dispatch, adjustment or stocktake |
| GET | `/warnings` | admin, manager | `type=LOW\|OUT\|RESTOCKED`, `state=open\|resolved\|all`, `cache=true\|false`, `page`, `size` |
| POST | `/warnings/{id}/ack` | admin, manager | record reviewer and acknowledgement time |
| GET/POST/PATCH | `/users` | admin | list/create; patch `/{id}/enabled` |
| GET/PUT | `/settings` | signed in / admin | store name and display currency |

Stock request: `{ "productId": 7, "type": "STOCK_IN", "quantity": 12, "reason": "Morning delivery", "idempotencyKey": "client-generated-unique-value" }`. Positive quantity is required for stock-in/out. An adjustment quantity is signed and non-zero. Stocktake quantity is absolute and may be zero. A successful write responds 201 with actor, before/delta/after, and timestamp. Replaying the exact key and payload returns the same transaction ID; mismatched replay returns 409.

Paginated responses are `{items,page,size,totalElements,totalPages}`. Page is zero-based. Maximum page size is 100. Product sort allow-list: `name`, `sku`, `quantity`, `price`, `updatedAt`; unsupported sort falls back to `name`, and ID provides a deterministic tie-breaker. `status` supports `healthy`, `low`, `out`. Error body is `{code,message,timestamp}` for application errors.

Detailed request and response examples are exercised by `scripts/smoke.py`. CSRF state, authentication and authorization are part of the smoke journey.
