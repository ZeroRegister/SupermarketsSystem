# Requirements and acceptance traceability

| ID | Actor / use case | API | Data / UI | Acceptance evidence |
|---|---|---|---|---|
| R1 | All: sign in/out | `/auth/*` | users, session / login | invalid login, logout, CSRF, role denial |
| R2 | Admin: manage catalog | `/products`, `/categories`, `/suppliers` | products, categories, suppliers / catalog | unique SKU/barcode, valid threshold hierarchy, FK validation |
| R3 | Clerk/Admin: receive and dispatch | `/transactions` | product, movement, warning / stock form | positive delta, insufficient stock, atomic history |
| R4 | Clerk/Admin: adjust and count | `/transactions` | movement / count form | signed adjustment, absolute count, zero-count audit |
| R5 | All: inspect inventory | `/products` | product / search and pagination | empty results, filters, deterministic sorting |
| R6 | Manager/Admin: review warnings | `/warnings` | warning episode / warning board | zero, equality threshold, recovery, repeated low episode |
| R7 | Manager/Admin: acknowledge | `/warnings/{id}/ack` | actor/time/status / warning board | clerk forbidden, repeat ack, resolved warning retained |
| R8 | Manager/Admin: reports | `/reports` | aggregates / report screen | totals derived from MySQL, transaction history |
| R9 | Admin: users/settings | `/users`, `/settings` | users/settings / administration | role update, disabled login, last-admin guard |
| R10 | System: reliable writes | `/transactions` | unique request key / retry | exact replay, mismatched replay, concurrent dispatch |
| R11 | System: cache/recovery | `/warnings?cache=false` | revision+Redis / same warning UI | same results, post-write new revision, Redis fallback |

## Domain invariants

Quantity is an integer between zero and 1,000,000,000. `0 <= safetyStock <= reorderThreshold <= 1,000,000,000`. Money is non-negative decimal with at most two fractional digits. Products start at zero; initial balances use a stock-in movement. Product edits cannot set quantity. Products with history are archived rather than deleted; archived products retain reports/history and reject new movements. Category/supplier deletion is rejected while referenced. Reasons are mandatory and bounded, actors are derived from authentication.

OUT: sellable quantity zero. LOW: positive sellable quantity at or below reorder threshold. Safety stock marks urgency within LOW. When a warning product becomes healthy, resolve its open warning and create a RESTOCKED episode. RESTOCKED remains visible for 24 hours, with its expiry stored at creation; it is resolved on expiry or on renewed shortage. LOW→OUT and OUT→LOW resolve the former episode and open the new severity. Remaining within one severity keeps the same acknowledgement. Metadata/threshold edits also recalculate episodes. Acknowledgement is orthogonal to OPEN/RESOLVED lifecycle. Batch expiry, slow-stock rules, assignment/handling, purchasing and review requirements are detailed in [warning expansion](warning-expansion.md); API boundaries are in [API](api.md).

Managers read inventory, maintain thresholds, quarantine batches and approve purchases/stock reviews; they do not post ordinary stock movements or edit product identities. Clerks read inventory/history, receive/dispatch/sell stock, and submit adjustment/count/disposal requests. Managers/admins alone read warnings/reports. Admins manage all catalog, users and settings and retain a direct stock-maintenance route. Session authority is reloaded from MySQL per request so role removal/disablement takes effect without waiting for logout. No password is returned by an API.

Search supports product name/SKU/barcode substring, category, active/archive and stock status. Pages are capped at 100; supported sort fields are name, SKU, quantity and price with ID as tie-breaker. Dates are UTC ISO-8601; the UI renders local time. Setting currency changes display labels, not stored amounts or conversion.
