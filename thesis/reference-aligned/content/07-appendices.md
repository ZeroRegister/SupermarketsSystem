# Appendices
## Appendix A API and response contracts
The following catalog records the implemented route families at the source revision used by this thesis. Roles refer to ADMIN, MANAGER and CLERK. Authenticated GET access to category and supplier lists does not imply catalogue write access. An inventory request identifies the stock intention, while the returned movement supplies the authoritative actor and quantities.
@table api-catalog|Implemented HTTP route catalog
Method | Path | Allowed callers | Meaning
GET | /api/auth/csrf | Anonymous or signed in | Obtain CSRF token
POST | /api/auth/login | Anonymous with CSRF | Authenticate and create session
GET | /api/auth/me | Signed in | Current account
POST | /api/auth/logout | Signed in with CSRF | End session
GET | /api/products | Signed in | Filtered bounded inventory page
GET | /api/products/{id} | Signed in | Product detail
POST | /api/products | Administrator | Create zero-stock catalogue record
PUT | /api/products/{id} | Administrator | Edit identity and policy
DELETE | /api/products/{id} | Administrator | Archive product
PATCH | /api/products/{id}/thresholds | Administrator or manager | Update threshold policy
GET | /api/categories and /api/suppliers | Signed in | Reference directory
POST PUT DELETE | Category and supplier resources | Administrator | Maintain reference records
GET | /api/transactions | Signed in | Movement history optionally by product
POST | /api/transactions | Administrator or clerk | Submit audited stock intention
GET | /api/warnings | Administrator or manager | Filtered warning page
POST | /api/warnings/{id}/ack | Administrator or manager | Preserve first reviewer
GET | /api/dashboard and /api/reports/summary | Administrator or manager | Stock aggregates
GET | /api/stock-summary | Signed in | Summary view without warning items
GET POST PATCH | /api/users and access resources | Administrator | Accounts roles and enabled state
GET | /api/settings | Signed in | Current display preferences
PUT | /api/settings | Administrator | Store name and display currency

Paginated responses contain items, page, size, totalElements and totalPages. Product queries accept q, categoryId, status, archived, page, size, sort and direction. Supported stock-health values are healthy, low and out. Warning queries accept type, state, page, size and cache. Unsupported warning values are rejected by the controller. Timestamps are emitted as UTC ISO-8601 values; the browser formats local display times.

A transaction payload includes productId, type, quantity, reason and idempotencyKey. STOCK_IN and STOCK_OUT quantities are positive. ADJUSTMENT is signed and non-zero. STOCKTAKE is an absolute non-negative count. An example intention to receive twelve units does not carry an actor ID, quantityBefore or quantityAfter: the server supplies those fields from its authenticated and locked context.
@table status-codes|Response status interpretation
Status | Meaning in the application | Client interpretation
200 | Successful query update or acknowledgement | Inspect returned representation
201 | Transaction or creation endpoint success | Use returned identifier; replay can return an existing movement
204 | Successful archive or logout response | No JSON representation expected
400 | Validation or supported-boundary error | Correct the submitted intention
401 | Authentication missing or invalid | Establish a valid session
403 | CSRF or role restriction | Check credentials token and authority
404 | Requested record absent | Refresh selection or correct identifier
409 | Identity reference or replay conflict | Resolve the conflicting intention or record
## Appendix B Backend acceptance catalog
This catalog names the 27 executable backend cases and states the behavior their assertions address. It is provided to make a passed count interpretable. The wording of a test name is not itself an assertion; the renewed-shortage case is consequently described according to its executed operations rather than as a complete time-expiry experiment.
@tests

The cases use disposable service instances and synthetic records. They validate isolated boundaries and selected concurrent requests, not a production mix of transactions over a working day. New batch, fractional-unit or purchasing features would require new acceptance scenarios in addition to the present catalog.
## Appendix C Reproduction and evidence locations
The application is reproduced by installing the pinned project baseline, preparing local environment values, starting the Compose services and running the backend and browser client. The backend wrapper reads the repository's local environment and selects the local Java and Maven installations when present. The frontend wrapper selects the project Node baseline. Secrets remain in the local environment and are not included in this document.

Backend integration tests use the current Docker socket for Testcontainers. On the recorded Colima host, DOCKER_HOST points to its Unix socket. This is an execution-environment setting, not a business parameter. Frontend unit tests run through the pinned package scripts. The earlier operational browser script posts a demonstration receipt and review, whereas the expanded capture script opens draft forms without submitting business changes.
@table reproduce|Reproduction actions and their artifacts
Action | Repository entry point | Inspectable result
Start local infrastructure | docker-compose.yml | MySQL and Redis health checks
Run backend | scripts/backend.sh spring-boot:run | Migrated schema and API health
Run browser client | scripts/frontend.sh run dev | Responsive application on development port
Backend integration suite | scripts/backend.sh test | Surefire result and test log
Frontend unit suite | scripts/frontend.sh test | Three boundary-test results
Operational browser journey | scripts/browser-smoke.mjs | Earlier write review and navigation evidence
Expanded interface capture | scripts/capture-paper-ui.mjs | Screens and capture verification
Cache benchmark | scripts/benchmark.py | Workload environment and raw latency samples
Failure and persistence checks | scripts/fault-recovery.py and persistence-snapshot.py | Recovery and selected-row equality records
Figure drawing | scripts/prepare-paper-diagrams.py | Editable diagrams and image exports
Thesis assembly | scripts/build-expanded-thesis.py | Editable LaTeX manuscript and compiled PDF

The figure collection includes a manifest of image dimensions, source paths, capture dates and content hashes. Code images preserve the original source line locations and exact excerpt text. The current result logs and historical raw measurements remain separate. These artifacts allow a reader to identify what was drawn, what was captured and what was measured, without treating every image as equivalent evidence.
