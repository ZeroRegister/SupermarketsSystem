# System design
## Architecture and ownership of state
Shelfwise comprises a responsive browser client, one Spring Boot application, MySQL and an optional Redis cache. The browser presents stock information and submits operational intentions; the application authorizes and validates them. MySQL owns durable product balances, movement history, warning episodes, user access and preferences, while Redis holds only short-lived serialized warning pages. This division of ownership determines both the normal request path and the behavior under failure.

The runtime architecture in {fig:architecture} is layered rather than divided into business microservices. Controller, service and repository boundaries separate responsibilities inside one process, so a stock change can coordinate quantity, history, warning state and cache revision without a cross-service commit protocol. This choice suits the single-store scope and keeps each acceptance condition inspectable.
@fig architecture|diagrams/08-runtime-architecture.png|Runtime layers and the ownership of durable inventory state

The server reads the existing quantity, computes the accepted balance from the requested operation or observed count, and updates warning episodes and reviewer attribution in the same request. All changes to durable inventory and review data pass through the application service; the warning cache only stores serialized views of the resulting database state. Because the process also keeps servlet sessions locally, a multi-node deployment would require a renewed assessment of service responsibilities, session handling, database capacity and monitoring. The present design targets the single-store deployment evaluated in Chapter 5.
## Refinement of the browser and server architecture
### Browser modules and state
The browser separates the application shell, authenticated navigation, pages and API exchange. LoginView owns sign-in, while WorkspaceView selects the operational task from a query parameter. Pinia retains the current user; local reactive state holds loaded pages and drafts.

The API client centralizes the base path, credentials and CSRF header. TypeScript describes the response shapes that components expect, whereas the server validates input and constructs response records; runtime response validation would require additional checks. The client reports a failed read as an error and a successful zero-match query as an empty selection.

This page structure keeps the demonstrator compact, but WorkspaceView consequently contains many sections and modal forms. Splitting it into view-level components and composables would improve frontend maintainability without altering the API or the stock semantics.
### Server layers and transaction ownership
The server separates security filters, controllers, services, repositories and entities. Controllers translate validated requests into service calls, InventoryService coordinates business changes, and repositories provide selection, pagination and locking. Flyway creates the schema and JPA validates the mappings at startup.

The service is intentionally central: it contains catalog, stock, warning, report and access operations, which makes the coordinated write path easy to follow. A growing codebase would benefit from separating query and command responsibilities, but any refactoring must preserve the effective transaction boundary. Moving warning evaluation into another service, for instance, would break correctness if the call no longer joined the stock transaction.
## Relational database design
### Core schema and migrations
{fig:er-overall} shows the initial V1 core schema. Products optionally reference categories and suppliers, movements require a product and an actor, and warnings optionally record a reviewer. Store settings and the cache revision are independent support tables. Seven later migrations extend this core, as summarized in {tab:migration-layers}; the current schema of eighteen tables is the combined V1–V8 result. Field-level definitions remain in the migration sources and the supplementary schema catalog. In this and the following ER figures, each relationship label names the foreign key and gives the parent's participation followed by the child's multiplicity: actor_id with 1 : 0..*, for instance, means that every movement has exactly one actor while a user may have any number of movements.
@fig er-overall|diagrams/11-er-overall.png|Initial V1 core relational schema excerpt
@table migration-layers|Schema extensions introduced by migrations V2–V8
Migration | Principal additions | Design purpose
V2 Warning workflow | Review stage, assignee, recovery time and predecessor on warnings; warning_actions | Separate review handling from the warning lifecycle and retain action history
V3 Batch inventory | Sellable quantity; inventory_batches, batch_allocations and batch_actions; receipt metadata | Distinguish physical from sellable stock and record per-batch allocation
V4 Expiry rules | Batch link and active-rule key on warnings; warning_policy | Keep one open episode per rule identity under an explicit business timezone
V5 Slow-moving rules | Slow-stock window and minimum; product creation time; sales-time index | Support product-age and SALE-only inactivity queries
V6 Purchasing | Target stock and supplier lead time; purchase_orders, purchase_lines, purchase_receipts and purchase_actions | Reviewable purchasing with bounded, replay-aware partial receipts
V7 Stock review | stock_reviews with snapshot quantity and version, creator, reviewer and movement link | Approve counts, adjustments and disposal against a recorded snapshot
V8 Review request keys | Actor-scoped request key on stock_reviews | Replay identity for review submission, backfilled for earlier records

Optionality in the schema mirrors the domain. A product can be unclassified or have no supplier, and one category or supplier can serve many products. A movement always has a product and an actor, whereas review attribution is nullable because an episode may not yet have been acknowledged. Batch allocations, warning actions, purchase receipts and stock reviews keep explicit links to the records that caused them.
### Identity, catalog and support data
The users table stores a unique username, display name, password hash, fixed role and enabled flag. The hash is never included in user responses, and disabling an account preserves the historical actor relationships that a deletion would break. The fixed-role design avoids a configurable permission editor and limits the number of authorization combinations to test; the cost is that a store cannot define a fourth role without changing and revalidating the permission rules.

Product identity is protected by a unique SKU and an optional unique barcode. Database checks bound quantity and price and require a non-negative safety stock no greater than the reorder threshold. Category names are unique, supplier names are descriptive, and foreign keys reject deletion of referenced records. The version column supports the JPA entity mapping, while stock operations additionally take an explicit pessimistic lock. Because catalog input does not expose quantity, product editing cannot bypass the movement ledger. Archival clears the active flag instead of deleting the row, so earlier movements and warnings remain explainable after a product is discontinued.

Store settings are key–value pairs for the business name and display currency. The cache revision table holds a singleton counter that advances whenever stock, thresholds or other warning-relevant state changes; keeping it in MySQL lets cache namespaces survive an application restart consistently with the data. The counter is, however, a shared write target: updates to different products can contend on it even though their product locks differ. The evaluated workload does not quantify this contention, and a high-write deployment could consider partitioned revisions while preserving the same post-write query contract.
### Movement ledger and warning episodes
The movement relationships in {fig:er-detail}(a) connect each accepted change to a product and an actor. A row stores type, signed delta, before and after quantities, a mandatory reason, the request key and a server timestamp. The composite unique constraint on actor and idempotency key is independent of the product, so one actor's key can identify only one accepted intention. The application offers no edit or delete endpoint for accepted movements; privileged SQL access and backups fall under a separate authority, and stronger audit requirements would call for restricted administration and append-only or signed storage.
@fig er-detail|diagrams/13-er-movements.png+diagrams/14-er-warnings.png|Detailed V1 relationships: (a) mandatory product and actor references in movement history; (b) warning episodes with optional reviewer attribution

The warning model in {fig:er-detail}(b) stores type, lifecycle state, observed quantity, threshold and timestamps, later extended with rule-policy data for expiry and slow-moving evaluation. An open episode therefore has two independent dimensions: its shortage or recovery lifecycle and whether a person has acknowledged it. Acknowledgement is not encoded by replacing OPEN with a reviewed state. Observed quantity and threshold describe the current interpretation and are updated while a shortage stays at the same severity; the movement table, not the warning row, holds the full history.
## Transactional stock consistency
Product, UserAccount, InventoryTransaction and WarningEpisode objects map the core relationships above, and batch, review and purchase entities extend them as listed in {tab:migration-layers}. Repository methods perform individual reads and writes, but the service owns the enclosing transaction. Saving a movement row alone is insufficient: quantity, batch effects, warning state and cache revision must agree when the operation commits.
### Batch allocation and rule policy
Batch receipts create dated inventory identities. Dispatch selects sellable batches by FEFO when expiry dates exist and falls back to FIFO for deterministic ordering. Expired or quarantined batches remain physically present but are excluded from sellable quantity. The batch remainder is rechecked when a disposal or review is approved, so an approval cannot remove stock that another transaction has already consumed.

Expiry uses the configured business timezone and an inclusive boundary: a batch is sellable on its expiry date and expires on the following business date. Slow-moving detection considers only SALE movements, excluding receipts, adjustments and stocktakes. These policies are explicit because a single quantity threshold cannot express product age or sales inactivity.
### Product locking and bounded arithmetic
The server first loads the authenticated actor and then acquires a locking read on the product row. MySQL documents locking reads as a way to reserve a row for coordinated updates until commit or rollback [@mysql-locks], and Spring Data JPA exposes such lock modes at repository level [@spring-locks]. Shelfwise applies them at the product boundary instead of calculating a new quantity from a previously displayed value.

The movement method runs at READ_COMMITTED isolation and derives its delta from the locked product. Addition is checked for arithmetic overflow and against the supported quantity bounds. An absolute stocktake computes the observed quantity minus the locked quantity; a count equal to the current balance creates a zero-delta observation, whereas a zero-delta relative adjustment is rejected. The distinction is a business rule, not an optimization.

The locked write coordinates product quantity, audit record, warning evaluation and revision advancement. If a domain or persistence exception aborts the transaction, all of these effects roll back together. Saving the audit record flushes the persistence context so that certain integrity errors surface during the operation; the flush is not a separate commit.
### Idempotency and retry scope
After acquiring the product lock, the service looks up any prior movement for the same actor and key. The original view is returned only if product, type, normalized reason, quantity meaning and batch metadata all match. STOCKTAKE compares the earlier after quantity with the requested count, other types compare signed deltas, and receipt batch numbers and dates or the batch selected for a negative adjustment form part of the comparison. A mismatched replay produces HTTP 409.

This ordering serializes the ordinary same-product retry, and the unique constraint adds a durable backstop. Reusing one key concurrently for different products is a different pattern: separate product locks do not serialize it, and the outcome may be a uniqueness conflict rather than an exact replay. The concurrent test of identical submissions covers a single product, so its result is not generalized to cross-product races. {tab:stock-consistency} summarizes the controls and their limits.
@table stock-consistency|Consistency controls and the problems they address
Control | Protected fact | Important boundary
Product row lock | Current balance used to derive the new result | Lock scope is one product
Transaction boundary | Quantity, ledger, warning and revision agree | Persistence exceptions must abort the whole operation
Actor-key uniqueness | One accepted movement per key namespace | Different actors may use the same textual key
Normalized replay comparison | A retry returns the original intention's result | A reused key with changed content conflicts
Quantity bounds | Accepted balance is non-negative and bounded | Does not define decimal unit conversion
Mandatory actor and reason | Every accepted movement remains explainable | Does not prevent privileged direct database modification
## Warning lifecycle design
The lifecycle in {fig:warning-state} separates shortage severity from recovery. A sellable quantity of zero selects OUT; a positive quantity at or below the threshold selects LOW. A healthy quantity closes an open shortage and may create RESTOCKED. A transition between LOW and OUT closes the former severity and opens the latter, whereas remaining at one severity updates its quantity context without resetting review attribution.
@fig warning-state|diagrams/22-warning-state.png|Shortage and recovery episode lifecycle with independent acknowledgement

A RESTOCKED episode expires twenty-four hours after creation, and a renewed shortage closes it earlier; archiving a product closes all of its open episodes. Warning queries exclude expired recovery rows, and a scheduled cleanup marks them resolved. Because a cached page can persist until the revision or TTL changes and cleanup is periodic, the design does not promise a zero-delay change at the expiry boundary; clock-controlled expiry and cache tests would strengthen this part of the evaluation.

Acknowledgement locks the warning row and preserves the first recorded reviewer. Repeating an existing acknowledgement returns that attribution, even after the episode has resolved. A new acknowledgement requires an OPEN episode, so a resolved episode without a reviewer rejects a first acknowledgement with HTTP 409. The interface offers the action only for open, unreviewed episodes.
## Revision-based cache design
The warning query first reads the durable revision and builds a key from revision, type, lifecycle state, page and size. A valid cache hit returns the decoded page. A miss or cache exception triggers a database query and a best-effort fill with a thirty-second TTL, as shown in {fig:cache-sequence}. Reading the revision from the database is part of the cost even when Redis holds the response.
@fig cache-sequence|diagrams/20-seq-warning.png|Warning retrieval through a revision namespace and cache-aside fallback

A fill that started before a write may complete under the old revision, but later queries read the new revision and never address that key. This closes a stale-fill race that simple key deletion would leave open. It does not cancel in-flight reads or synchronize every open browser screen; a user may need a new read to see the committed change.

SQL filtering precedes pagination, and page content, total elements and total pages are serialized together, so cache equivalence covers the whole response contract rather than the first displayed row.
## Permissions and request security
The authorization matrix in {tab:role-matrix} combines HTTP method and route rules with controller checks. Administrators and clerks post receipts, dispatches and SALE movements; clerks submit corrections and counts for review, which administrators and managers approve together with purchases. Administrators also retain direct ADJUSTMENT and STOCKTAKE access. Managers update thresholds and targets, review warnings and control batch quarantine, while staff accounts, catalog identity and store preferences remain administrator operations.
@table role-matrix|Server authorization matrix
Operation | Administrator | Manager | Clerk
Read inventory, movement history, stock summary and preferences | Yes | Yes | Yes
Post receipt, dispatch or SALE | Yes | No | Yes
Post direct adjustment or stocktake | Yes | No | No
Submit count or disposal review | Yes | No | Yes
Approve stock review or purchase | Yes | Yes | No
Update stock thresholds and target | Yes | Yes | No
Read warning board and reports; acknowledge warnings | Yes | Yes | No
Create, edit or archive products | Yes | No | No
Manage users, access and store preferences | Yes | No | No

The request path in {fig:security} combines session identity, CSRF protection, account refresh and endpoint authorization. Because browsers send session credentials automatically, unsafe methods require CSRF protection [@spring-csrf]; Shelfwise issues a readable token, separate from the HttpOnly session cookie, and sends it as a header on unsafe requests.
@fig security|diagrams/23-security-flow.png|Security checks preceding controller execution

Passwords are hashed with BCrypt, the session identifier is rotated after authentication, and account access is reloaded from MySQL on later requests. Rate limiting, MFA, password recovery, TLS and secure cookie settings are deployment obligations outside the implemented controls.
## Chapter summary
The design keeps product balances, batches, movement history, warning episodes, review snapshots and purchase documents within one transactional service boundary. MySQL holds durable state, a revision namespace governs cached warning pages, and server permissions restrict every state transition; the shared revision row, fixed roles and local sessions are the main deployment constraints. Chapter 4 presents the implementation.
