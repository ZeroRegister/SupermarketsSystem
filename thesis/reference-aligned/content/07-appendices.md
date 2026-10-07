# Appendices
## Appendix A API and response contracts
This appendix lists the HTTP routes at the source revision used in this thesis: {tab:api-catalog} covers the core routes and {tab:extension-api} the batch, warning, purchasing and review routes; roles refer to ADMIN, MANAGER and CLERK. Read access to the category and supplier lists for every signed-in user does not imply catalog write access. A stock request expresses only the intended change, while the returned movement carries the authoritative actor and quantities.
@table api-catalog|Core HTTP route catalog
Method | Path | Allowed callers | Meaning
GET | /api/auth/csrf | Anonymous or signed in | Obtain CSRF token
POST | /api/auth/login | Anonymous with CSRF | Authenticate and create session
GET | /api/auth/me | Signed in | Current account
POST | /api/auth/logout | Any caller with CSRF | End session; returns 204
GET | /api/products | Signed in | Filtered bounded inventory page
GET | /api/products/{id} | Signed in | Product detail
POST | /api/products | Administrator | Create zero-stock catalog record
PUT | /api/products/{id} | Administrator | Edit identity and policy
DELETE | /api/products/{id} | Administrator | Archive product
PATCH | /api/products/{id}/thresholds | Administrator or manager | Update threshold policy
GET | /api/categories and /api/suppliers | Signed in | Reference directory
POST PUT DELETE | Category and supplier resources | Administrator | Maintain reference records
GET | /api/transactions | Signed in | Movement history optionally by product
POST | /api/transactions | Administrator or clerk | Receipt, dispatch or SALE; direct correction and count are administrator-only
GET | /api/warnings | Administrator or manager | Filtered warning page
POST | /api/warnings/{id}/ack | Administrator or manager | Preserve first reviewer
GET | /api/dashboard and /api/reports/summary | Administrator or manager | Stock aggregates
GET | /api/stock-summary | Signed in | Summary view without warning items
GET POST PATCH | /api/users and access resources | Administrator | Accounts, roles and enabled state
GET | /api/settings | Signed in | Current display preferences
PUT | /api/settings | Administrator | Store name and display currency

@table extension-api|Batch, warning, purchasing and review route catalog
Method | Actual path | Allowed caller | Implemented meaning / boundary
GET | /api/batches | Signed in | Paginated batch balances; optional productId filter
POST | /api/batches/{id}/control | ADMIN or MANAGER | Set quarantine flag with reason and actor; refresh product warning interpretation in the enclosing transaction
GET | /api/batches/{id}/history | Signed in | Movement allocations for the selected batch
GET | /api/batches/{id}/controls | Signed in | Batch quarantine-control history
GET | /api/transactions/{id}/allocations | Signed in | Batch allocations belonging to one inventory movement
GET | /api/warnings/assignees | ADMIN or MANAGER | Enabled staff available for warning assignment
GET | /api/warnings/{id}/history | ADMIN or MANAGER | Chronological warning-action history
POST | /api/warnings/{id}/actions | ADMIN or MANAGER | ASSIGN, PROCESS or NOTE; ASSIGN/PROCESS require OPEN, while NOTE may be added after recovery
GET | /api/warnings/policy | ADMIN or MANAGER | Near-expiry days, business timezone, slow-stock window/minimum and policy version
PUT | /api/warnings/policy | ADMIN or MANAGER | Validate and update warning policy, then trigger a refresh sweep
POST | /api/warnings/refresh | ADMIN or MANAGER | Trigger product warning refresh; return sweep status
GET | /api/warnings/refresh-status | ADMIN or MANAGER | Interval, retry interval, last completion, failed-product count and running flag
GET | /api/replenishment | Signed in | Positive suggestions from sellable quantity plus outstanding APPROVED/PARTIAL purchase quantity
PATCH | /api/products/{id}/target | ADMIN or MANAGER | Set target stock, strictly above reorder threshold
GET | /api/purchases | Signed in | Paginated purchase documents
GET | /api/purchases/{id} | Signed in | Purchase details and lines
POST | /api/purchases | Signed in | Create draft with supplier, unique product lines, reason and optional linked warning
PUT | /api/purchases/{id} | Signed in | Edit DRAFT/REJECTED document and return it to DRAFT
POST | /api/purchases/{id}/actions | SUBMIT: signed in; APPROVE/REJECT/CANCEL: ADMIN or MANAGER | Controller adds the action-dependent role check; service validates state and rechecks current suggestion before approval
POST | /api/purchases/{id}/receipts | ADMIN or CLERK | Actor-key replay-aware receipt against APPROVED/PARTIAL document; creates audited STOCK_IN and batch metadata
GET | /api/purchases/{id}/receipts | Signed in | Purchase receipt history
GET | /api/purchases/{id}/history | Signed in | Purchase action history
GET | /api/stock-reviews | Signed in | Paginated count/adjustment/disposal reviews
POST | /api/stock-reviews | ADMIN or CLERK | Submit COUNT, ADJUSTMENT or DISPOSAL with actor-scoped review request key; captures physical product quantity/version, and selected batch for disposal
POST | /api/stock-reviews/{id}/actions | ADMIN or MANAGER | APPROVE or REJECT; approval creates linked movement. COUNT validates quantity/version snapshot; DISPOSAL checks current batch remainder

Every unsafe browser method requires a CSRF token in addition to the role checks listed. For purchase actions, the security filter only requires a signed-in user; the controller then applies the role check, because the permitted role depends on the action. Similarly, direct ADJUSTMENT and STOCKTAKE movements pass the filter for clerks but are refused by the transaction controller unless the caller is an administrator.

Paginated responses contain items, page, size, totalElements and totalPages. Product queries accept q, categoryId, status, archived, page, size, sort and direction, where status is one of healthy, low or out. Warning queries accept type, state, page, size and cache, and the controller rejects unsupported values. Timestamps are emitted in UTC as ISO-8601 strings and formatted in local time by the browser. {tab:status-codes} summarizes how clients should interpret each response status.

A transaction payload contains productId, type, quantity, reason and idempotencyKey, plus, where applicable, a batch number, production and expiry dates or a selected batch. Quantities for STOCK_IN, STOCK_OUT and SALE are positive, with STOCK_OUT and SALE reducing stock; ADJUSTMENT is signed and non-zero; STOCKTAKE is an absolute, non-negative count. A request to receive twelve units therefore carries no actor ID, quantityBefore or quantityAfter: the server derives these from the authenticated session and the locked product.
@table status-codes|Response status interpretation
Status | Meaning in the application | Client interpretation
200 | Successful query, update or acknowledgement | Inspect returned representation
201 | Transaction or creation endpoint success | Use returned identifier; replay can return an existing movement
204 | Successful archive or logout response | No JSON representation expected
400 | Validation or supported-boundary error | Correct the submitted intention
401 | Authentication missing or invalid | Establish a valid session
403 | CSRF or role restriction | Check credentials, token and authority
404 | Requested record absent | Refresh selection or correct identifier
409 | Identity, reference or replay conflict | Resolve the conflicting intention or record
## Appendix B Backend acceptance catalog
{tab:acceptance-catalog} lists the 45 backend integration cases and the behavior each one asserts; counts and results correspond to the execution of 7 October 2026 described in Chapter 5. The renewed-shortage case checks that a new episode opens after replenishment, whereas expiry of the recovery TTL would require a separate clock-controlled test.
@tests

The cases run against disposable service instances with synthetic records. They validate isolated boundaries and selected concurrent requests rather than a realistic mix of transactions over a working day. Batch allocation, expiry, slow-moving, purchasing and review cases are part of the current suite, while fractional units, multi-store isolation and point-of-sale reconciliation would need additional scenarios.
## Appendix C Reproduction and evidence locations
The application can be reproduced from source or from prebuilt images. Development from source uses the pinned Java, Maven and Node versions; the release deployment uses Docker Desktop, .env.release, docker-compose.release.yml and the Windows helper script. Secrets stay in local environment files and are not reproduced here.

Testcontainers uses the current Docker socket; on the recorded Colima host, DOCKER_HOST points to the Colima Unix socket, an execution-environment setting rather than a business parameter. Frontend unit tests run through the pinned package scripts. The earlier browser script posts a demonstration receipt and review, whereas the capture script opens draft forms without submitting any business change. {tab:reproduce} maps each action to its entry point and output.
@table reproduce|Reproduction actions and their artifacts
Action | Repository entry point | Inspectable result
Start full container stack | docker-compose.yml or docker-compose.release.yml | Four healthy services and frontend on port 5173
Run release deployment | scripts/start-release.ps1 | GHCR pull with Docker Hub fallback and healthy frontend
Run browser client in source mode | scripts/frontend.sh run dev | Responsive application on development port
Backend integration suite | scripts/backend.sh test | Surefire result and test log
Frontend unit suite | scripts/frontend.sh test | Three boundary-test results
Operational browser journey | scripts/browser-smoke.mjs | Earlier write, review and navigation evidence
Expanded interface capture | scripts/capture-paper-ui.mjs | Screens and capture verification
Cache benchmark | scripts/benchmark.py | Workload, environment and raw latency samples
Failure and persistence checks | scripts/fault-recovery.py and persistence-snapshot.py | Recovery and selected-row equality records
Figure drawing | scripts/prepare-paper-diagrams.py | Editable diagrams and image exports
Thesis assembly | scripts/build-expanded-thesis.py and thesis/reference-aligned/build.sh | Editable LaTeX manuscript and compiled PDF

The figure collection includes a manifest of image dimensions, source paths, capture dates and content hashes, and every code image reproduces its excerpt token for token with the original line numbers. Because the source is written in a dense style, long lines are broken at statement boundaries and indented for display; only the first display row of each source line carries its number, and the unaltered excerpt is stored alongside the image. Current result logs are kept separate from historical raw measurements. A reader can therefore tell what was drawn, what was captured and what was measured, instead of treating every image as equivalent evidence.
