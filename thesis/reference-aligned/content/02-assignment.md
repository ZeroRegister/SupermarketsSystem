# Requirements and technology selection
## Assignment and acceptance approach
The assignment is to implement the inventory workflow of Chapter 1 as an inspectable single-store application. A requirement counts as complete only when its actor, server operation, data effect and acceptance evidence can all be identified. For the approval workflows added in the expanded release, the behavior on replay, on a stale snapshot and across state changes must also be defined. A screen that appears to offer an operation is insufficient if the matching server permission or transactional behavior is missing, and a correct API is equally insufficient if the interface presents an absolute count as a relative change.

The requirements in {tab:requirements} are grouped into identity, catalog, stock operations, inventory inspection, warning review, reporting and administration. Correctness concerns cut across these groups: retry handling belongs to stock operations but depends on the request key kept by the browser, and cache fallback belongs to warning retrieval but depends on the database remaining the durable owner. The table therefore also serves as a map across the implementation layers.
@table requirements|Functional requirements and acceptance evidence
ID | Required behavior | Principal acceptance evidence
R1 | Sign in and sign out with current role authority | Anonymous denial, invalid credentials, session and role checks
R2 | Maintain catalog categories and suppliers | Uniqueness validation, referenced-record conflicts and archival
R3 | Receive and dispatch stock with an audit record | Before–delta–after arithmetic and attributed history
R4 | Apply signed adjustments and absolute counts | Negative correction, count-to-zero and unchanged-count cases
R5 | Search, filter and paginate inventory | Empty result, stable ordering and page-size boundary
R6 | Maintain shortage and recovery episodes | Zero, equality, severity change, recovery and expiry scenarios
R7 | Record managerial acknowledgement independently | Reviewer visibility and unchanged stock quantity
R8 | Present stock reports and selected-page export | Server aggregates, rendered reports and export scope
R9 | Manage users, roles and store preferences | Administrator boundary, next-request access and last-admin guard
R10 | Resist duplicate and concurrent stock submission | Exact replay, changed-payload conflict and concurrent tests
R11 | Preserve warning results without Redis | Cache bypass comparison and recorded outage equivalence
R12 | Track batch balances and apply FEFO/FIFO allocation | Receipt replay, expiry boundaries and batch dispatch tests
R13 | Detect expiry and slow-moving conditions | Business-timezone and sales-only warning tests
R14 | Manage replenishment and purchase approval | Suggestion quantities, approval recheck, partial receipt and cancellation tests
R15 | Review counts and disposal with a snapshot | Stale snapshot, approval and idempotent review tests
## Functional requirements
### Authentication and role-specific access
Users must authenticate before they can read inventory, and the server exposes the current account and role through a session-based API. Administrators manage accounts, catalog records and preferences; managers review stock health, read reports and update thresholds; clerks record movements and inspect inventory history. These are fixed role bundles rather than a configurable permission hierarchy, following the separation of roles and permissions described in the RBAC literature [@sandhu1996].

{fig:permissions} shows the three bundles; the administrator holds every manager and clerk permission and adds product identity, staff accounts, store settings and direct corrections. Every protected operation must be authorized by the server: navigation guards spare users misleading paths, but a caller who bypasses the browser must receive the same decision. An account disabled after sign-in must not remain usable merely because its cookie still exists, and role changes must take effect on the next request.
@fig permissions|diagrams/07-permission-model.png|Fixed role bundles enforced by the server and reflected in navigation
### Catalog and inventory inspection
Catalog administration requires unique SKUs, bounded non-negative prices, valid references and a consistent threshold hierarchy. Editing a product must not change its quantity, and archiving it must preserve its ledger while rejecting new movements. Category and supplier administration must protect existing references instead of silently detaching products on deletion.

Inventory inspection requires search by name, SKU and barcode, category selection, stock-health filters, stable sorting and bounded page sizes. The result count and pagination must describe the filtered selection, and an empty selection must offer a way to reset the filters.

For API consumers, pages are numbered from zero and their size is capped at one hundred; the interface loads twelve products per page. Sort fields are allow-listed and always end with an ID tie-breaker, which avoids ambiguous ordering and prevents a request parameter from becoming an arbitrary database expression. Snapshot consistency across pages is not promised while concurrent writes change the data.
### Stock operation requirements
Each stock request must name a product, movement type, quantity, reason and idempotency key, while the actor is taken from the authenticated principal. The server must derive the signed effect and read the before balance under the product lock. A failed request must leave no accepted movement and no partial quantity change. An unchanged stocktake must still be recorded, because the observation itself carries information.

An exact replay must return the original transaction identifier without applying a second change, and reusing a key with different normalized content must produce a conflict. Requests that would make the quantity negative or exceed the supported maximum must be rejected. Concurrent dispatches must be serialized per product so that the successful ones can never oversell the locked balance.
### Warning and reporting requirements
A sellable balance of zero must be classified as OUT, even when the threshold is also zero, and a positive balance equal to the reorder threshold must be LOW. Batch expiry reduces sellable quantity at the configured business-day boundary while the physical quantity remains available for disposal. A healthy replenishment must resolve the shortage and open a recovery episode. Slow-moving detection considers sales only, over a configured window. Continued low stock at the same severity must keep its reviewer, and any change to the threshold or warning policy must re-evaluate the affected episodes.

Reports must describe the recorded stock state rather than invent business indicators: inventory value uses current prices, the activity trend counts movements by UTC date, and the category mix uses current quantity totals. Acknowledgement must record who reviewed an episode without changing stock, and this distinction must be visible in labels, API operations and database relationships alike.
## Non-functional requirements and quality boundaries
Correctness takes priority over optional acceleration. MySQL must retain products, movements, warnings and settings, and neither posting stock nor retrieving authoritative warning results may depend on Redis. The movement path must update the balance, audit record, warning state and cache revision in one transaction, so that a failure rolls back the whole change instead of exposing a partial result.

The application must be reproducible from explicit dependencies and migrations. Local services are versioned in the repository, and evaluation scripts record machine, workload and sample metadata where available. Because another host may yield different latencies, reproducibility here means that the workload and procedure can be inspected and repeated, not that every recorded number will recur exactly.

Responsiveness is checked in a phone-sized viewport, with table scrolling confined to its container. The interface pairs stock colors with text labels and gives form fields descriptive names. These choices address relevant accessibility concerns, but full WCAG conformance is not claimed, since that would require a broader manual and automated assessment [@wcag]. {tab:quality} lists each quality attribute with the limits of its current evidence.
@table quality|Quality requirements and limits of the current evidence
Attribute | Required behavior | Current verification boundary
Consistency | Atomic bounded stock changes | Selected real-database transaction and concurrency cases
Retry handling | One accepted result per actor key and intention | Exact and conflicting replay plus same-product concurrency
Authorization | Server permission for each protected operation | Integration checks and browser guard scenarios
Recoverability | MySQL state remains authoritative without cache | Recorded Redis interruption and application restart
Usability | Clear stock semantics and recoverable empty states | Interface inspection and responsive browser checks
Performance | Described latency under a documented workload | Small sequential local warning-query benchmark
Maintainability | Explicit layers, schema and reproducible dependencies | Source structure, migrations and runnable scripts
## Analysis of related inventory systems
### Reordering rules in Odoo
Odoo's replenishment workflow uses minimum and maximum stock quantities to decide when, and how much, to reorder [@odoo]. Shelfwise similarly derives a replenishment suggestion from an explicit stock boundary, but the suggestion only seeds a draft purchase: submission, approval and receipt remain separate audited actions. Approval rechecks the current suggestion, and partial receipts create batch-aware movements. Supplier settlement and lead-time optimization are outside the implemented workflow.
### Retained ledger explanations in ERPNext
ERPNext follows an immutable-ledger approach in which cancelling a document preserves the original entries and records reversing ones instead of deleting the earlier posting [@erpnext]. The underlying principle—accepted operational history must remain explainable after a correction—also guides Shelfwise, and ERPNext's stock ledger shows how such postings can be inspected within a larger enterprise system [@erpnext-stock].

Shelfwise likewise keeps accepted movement rows and records corrections as later adjustments or stocktakes. Its audit history is, however, enforced only through the application's endpoints; a privileged database administrator can still alter stored rows directly. Document cancellation, backdated reposting and accounting integration, which ERPNext also provides, are outside Shelfwise's scope.
### Spreadsheet and broader enterprise alternatives
A spreadsheet can serve a very small stock list well when a single person controls editing: it is easy to inspect and requires almost no deployment. The difficulty addressed here arises once several staff roles need coordinated writes, attributed changes and server-enforced permissions, which a shared worksheet could provide only with additional controls. This comparison is analytical rather than an experimental evaluation of a particular spreadsheet product.

Enterprise resource planning systems integrate inventory with purchasing, warehouse locations, finance and sales. Shelfwise instead concentrates on one store's inventory transactions, warning rules and reviewed stock workflows. The narrower scope reduces integration effort and leaves checkout, accounting and multi-store operation to later development. {tab:alternatives} summarizes the comparison.
@table alternatives|Comparison of inventory-management approaches within the project scope
Approach | Useful characteristics | Gap relative to this assignment
Shared stock worksheet | Simple deployment and direct visibility | Requires added controls for concurrency, roles and attributed changes
Documented Odoo replenishment | Quantity policies connected to replenishment | Broader enterprise and supplier scope
Documented ERPNext ledger | Retained posting and correction explanations | Broader document, accounting and reposting mechanisms
Shelfwise bounded application | Batch-aware stock, warning rules, review and purchase approval with tests | No checkout integration, accounting, multi-store isolation or store-user study
## Technology selection and comparative analysis
### Backend and persistence
Java 21 and Spring Boot 3.5.16 provide typed request records, validation, servlet security, JPA repositories, transaction management and health endpoints, within the Java and build-tool versions documented by the framework [@springboot]. The inventory-specific validation and consistency rules are implemented in the service layer.

MySQL serves as the durable relational store. Its locking reads provide a primitive for coordinating updates to a product row, and its constraints protect identities and foreign keys [@mysql-locks]. PostgreSQL could support an equivalent design; the choice reflects the existing project baseline and tested environment rather than a comparative benchmark. Flyway migrations define the schema, and JPA validates the mapping at startup.

Redis caches warning-page responses and nothing else. It follows the cache-aside pattern, in which a miss triggers an authoritative query and a best-effort cache fill [@redis-cache]. To prevent stale pages after a write, the project adds a revision namespace stored in the database. This adds a read to every query and a shared update to every relevant write, so the cache must be evaluated with these costs included rather than assumed to be faster.
### Frontend and communication
Vue 3 provides a component-based browser interface, and TypeScript describes the response shapes used by pages and the API client [@vue]. Vue Router handles navigation, Pinia holds the authenticated account, Axios performs HTTP requests, Element Plus supplies the controls and ECharts renders the summaries. Responsive styles adapt the same application to desktop and phone-sized screens.

Shelfwise exposes a resource-oriented JSON API with server-side session authentication. Since Fielding lists stateless interaction among the REST constraints [@fielding2000], the session-based API departs from REST in that the server retains request context. A second application node would therefore require shared sessions or session affinity.
### Development and verification tooling
Docker Compose packages both the local and the release deployment: MySQL and Redis run as infrastructure services, Spring Boot runs in a Java runtime image, and Nginx serves the Vue bundle. A GitHub Actions workflow publishes the frontend and backend images and mirrors the pinned infrastructure images to GHCR for delivery to Windows hosts. Maven and Vite build the application, and Testcontainers, Vitest and Playwright support backend, frontend and browser verification. {tab:stack} lists the pinned versions.
@table stack|Implemented technology baseline and responsibility
Layer | Pinned technology | Responsibility
Backend | Java 21 and Spring Boot 3.5.16 | HTTP validation, security and transaction coordination
Persistence | Spring Data JPA and Flyway | Entity mapping, repository access and schema lifecycle
Database | MySQL 8.4.8 | Durable records, constraints and locking
Cache | Redis 7.4.9 | Optional thirty-second warning-page cache
Browser | Vue 3.5.22 and TypeScript 5.9.3 | Reactive interface and typed client data
UI and charts | Element Plus 2.11.5 and ECharts 6.1.0 | Controls and stock visualizations
Frontend build | Vite 7.3.6 and project Node 22 baseline | Development proxy and asset build
Evaluation | JUnit, Testcontainers, Vitest and Playwright | Layer-specific executable checks
## Chapter summary
The requirements define an auditable stock intention, a warning review independent of stock, and a single durable source of truth. Odoo and ERPNext illustrate replenishment policy and retained ledger history, and the technology analysis shows how the narrower scope of this project can be implemented. Chapter 3 translates the requirements into an architecture and relational constraints that make each acceptance condition observable.
