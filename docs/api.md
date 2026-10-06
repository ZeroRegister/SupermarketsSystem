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
| POST | `/transactions` | admin, clerk | receive, dispatch, sale; direct adjustment/count restricted to admin |
| GET | `/warnings` | admin, manager | `type=LOW\|OUT\|RESTOCKED\|EXPIRING\|EXPIRED\|SLOW`, `state=open\|resolved\|all`, `cache=true\|false`, `page`, `size` |
| POST | `/warnings/{id}/ack` | admin, manager | record reviewer and acknowledgement time |
| GET/POST/PATCH | `/users` | admin | list/create; patch `/{id}/enabled` |
| GET/PUT | `/settings` | signed in / admin | store name and display currency |

Stock request: `{ "productId": 7, "type": "STOCK_IN", "quantity": 12, "reason": "Morning delivery", "idempotencyKey": "client-generated-unique-value" }`. Positive quantity is required for stock-in/out. An adjustment quantity is signed and non-zero. Stocktake quantity is absolute and may be zero. A successful write responds 201 with actor, before/delta/after, and timestamp. Replaying the exact key and payload returns the same transaction ID; mismatched replay returns 409.

Paginated responses are `{items,page,size,totalElements,totalPages}`. Page is zero-based. Maximum page size is 100. Product sort allow-list: `name`, `sku`, `quantity`, `price`, `updatedAt`; unsupported sort falls back to `name`, and ID provides a deterministic tie-breaker. `status` supports `healthy`, `low`, `out`. Error body is `{code,message,timestamp}` for application errors.

Detailed request and response examples are exercised by `scripts/smoke.py`. CSRF state, authentication and authorization are part of the smoke journey.

## Batch and warning upgrade

| Method | Path | Roles | Purpose |
|---|---|---|---|
| GET | `/batches?productId=&page=&size=` | signed in | physical batch balances, expiry/quarantine status |
| GET | `/batches/{id}/history`, `/batches/{id}/controls` | signed in | signed allocations and quarantine audit |
| POST | `/batches/{id}/control` | admin, manager | `{quarantined,reason}` |
| GET | `/transactions/{id}/allocations` | signed in | actual batches for a movement |
| GET | `/warnings/assignees`, `/warnings/{id}/history` | admin, manager | enabled assignees and append-only handling history |
| POST | `/warnings/{id}/actions` | admin, manager | `{action: ASSIGN\|PROCESS\|NOTE, assigneeId?, note}`; null assignee clears assignment |
| GET/PUT | `/warnings/policy` | admin, manager | `{nearExpiryDays,businessTimezone,slowStockDays,slowStockMinimum}` |
| GET/POST | `/warnings/refresh-status`, `/warnings/refresh` | admin, manager | scheduled sweep health / force refresh |
| GET | `/replenishment` | signed in | positive replenishment recommendations and calculation inputs |
| PATCH | `/products/{id}/target` | admin, manager | `{targetStock}`; target must exceed trigger |
| GET/POST/PUT | `/purchases[/{id}]` | signed in | list/get/create/edit drafts and rejected orders |
| POST | `/purchases/{id}/actions` | signed in / admin, manager | `{action,note}`; SUBMIT signed in; APPROVE/REJECT/CANCEL manager/admin |
| POST | `/purchases/{id}/receipts` | admin, clerk | `{lineId,quantity,batchNumber?,productionDate?,expiryDate?,idempotencyKey}` |
| GET | `/purchases/{id}/receipts`, `/purchases/{id}/history` | signed in | retained receipts and state changes |
| GET/POST | `/stock-reviews` | signed in / admin, clerk | list / submit `{kind: COUNT\|DISPOSAL\|ADJUSTMENT,productId,batchId?,quantity,reason,requestKey}` |
| POST | `/stock-reviews/{id}/actions` | admin, manager | `{action: APPROVE\|REJECT,note}` |

Receipt movement requests may include `batchNumber`, `productionDate`, `expiryDate`; omitted batch numbers are generated. `SALE` means recorded sales; `STOCK_OUT` is ordinary dispatch. Expired and quarantined batches cannot be used by either. Product `quantity` is physical; `sellableQuantity` excludes those batches. A negative admin maintenance adjustment may specify `batchId`; clerk adjustments/counts must use stock review. Dates are ISO `YYYY-MM-DD` in the configured business timezone. Date-based conditions refresh every 30 seconds. Acknowledgement never clears a rule condition.

Purchase drafts use `{supplierId,reason,warningId?,lines:[{productId,quantity}]}`. Approval rechecks inventory position and may reject an obsolete request with 409. Partially received orders can cancel only their remainder. Replay is supported for stock movements, receipts, stock-review submission and approvals; payload mismatch conflicts. `scripts/warning-upgrade-smoke.py` exercises the whole flow against a running local demo environment and adds named demo records without resetting existing data.
