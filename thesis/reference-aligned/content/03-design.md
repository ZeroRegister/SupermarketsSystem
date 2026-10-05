# System design
## Architecture and ownership of state
Shelfwise uses a responsive browser client, one Spring Boot application, MySQL and optional Redis. The browser presents stock information and submits operational intentions. The application authorizes and validates those intentions. MySQL owns durable product balances, movement history, warning episodes, user access and preferences. Redis stores a short-lived serialized warning-page response. This ownership distinction determines both the normal path and the failure path.

The runtime architecture in {fig:architecture} is layered rather than distributed across business microservices. Controller, service and repository boundaries describe responsibility inside the same process. A stock change can therefore coordinate quantity, history, warning state and cache revision without a cross-service commit protocol. This choice fits the single-store implementation and keeps its acceptance conditions easier to inspect.
@fig architecture|diagrams/08-runtime-architecture.png|Runtime layers and the ownership of durable inventory state

The browser and database do not share the right to assign a balance. A request can identify an absolute observed count or a relative operation, but the server obtains the existing quantity and computes the accepted result. Similarly, the cached warning page is not allowed to resolve an episode or assign a reviewer. A cache contains a representation of database state; it is not a second business ledger.

A modular monolith also has limits. One process contains a central service with several responsibilities, and the default servlet session store is local to that process. A wider deployment would need to reconsider service boundaries, session handling, database capacity and operational monitoring. No conclusion about distributed scalability follows merely from separating source files into layers.
## Refinement of the browser and server architecture
### Browser modules and state
The browser architecture in {fig:frontend} distinguishes the application shell, authenticated navigation, pages and API exchange. LoginView owns the sign-in form. WorkspaceView selects the operational view from a query parameter and contains inventory, catalogue, stock activity, warning, reporting and administration screens. Pinia retains current-user state, while local reactive state owns loaded pages and form drafts.
@fig frontend|diagrams/09-frontend-structure.png|Frontend responsibilities and typed HTTP exchange

The API client centralizes the base path, credentials and CSRF header. TypeScript types describe response shapes used by components. These types improve development-time inspection but do not validate an arbitrary server response at runtime. The server's input validation and response construction remain separate responsibilities. A failed read is presented as an error; it should not be interpreted as a successful empty inventory selection.

The chosen page structure keeps the demonstrator compact. WorkspaceView is consequently a substantial component with multiple sections and modal forms. A maintenance extension could split it into view-level components and composables while preserving the API and domain semantics. This would address frontend code organization rather than alter stock correctness.
### Server layers and transaction ownership
The server refinement in {fig:backend} maps security filters, controllers, the inventory service, repositories and entities. Controllers translate validated HTTP requests into service calls and construct responses. InventoryService coordinates business changes. Repositories implement database selection, pagination and locking. Flyway creates the relational schema, while JPA validates entity mapping rather than silently replacing the migration.
@fig backend|diagrams/10-backend-structure.png|Backend request layers and the inventory service boundary

The service is intentionally central to the current implementation. It contains catalogue, stock, warning, report and access operations. This concentration makes the coordinated write path visible, although a growing codebase would benefit from separating query and command responsibilities. Any later refactoring must preserve the effective transaction boundary; extracting a warning method into another service is insufficient if the invocation no longer participates in the stock transaction.
## Relational database design
### Overall relationships
The relational model in {fig:er-overall} comprises eight tables. Products may reference a category and supplier. Inventory transactions require a product and actor. Warnings require a product and optionally reference a reviewer. Settings and cache revision are independent supporting tables. The schema does not contain purchase orders, sales orders, stores or permission-association tables because those objects are not part of the implemented boundary.
@fig er-overall|diagrams/11-er-overall.png|Overall schema derived from the initial Flyway migration

The reference-data relationships are nullable on the product side. A product can be unclassified or have no supplier; one category or supplier can be associated with many products. Actor relationships for movements are mandatory. Review attribution is nullable because an episode may not yet have been acknowledged. These distinctions are reflected by foreign keys and by the relationship notation in the figures.
### Users and access data
The users table stores identity and a fixed role name. Username is unique. The password field contains a hash and is excluded from user response records. The enabled flag supports account suspension without deleting historical actor relationships. Creation time provides administrative context rather than an authentication event log.
@schema users

The fixed-role design avoids introducing a configurable permission editor that the application does not implement. It also reduces the number of authorization combinations that need to be tested. Its limitation is flexibility: a store cannot define a fourth role or assign one isolated capability without changing and validating the program's permission rules.
### Catalogue and reference tables
The local catalogue relationship in {fig:er-catalogue} connects products to categories and suppliers. Category name is unique, whereas supplier name is descriptive and not constrained as a unique identifier. Deleting a referenced record is rejected by the relationship constraint. The program converts integrity conflicts into an application error that the interface can display.
@fig er-catalogue|diagrams/12-er-catalogue.png|Product relationships with category and supplier data
@schema categories
@schema suppliers
@schema products

Product quantity and price have database bounds, and the threshold check requires a non-negative safety stock no greater than the reorder threshold. SKU and barcode uniqueness protect inventory identity. The version column participates in the JPA entity mapping; the stock operation additionally uses an explicit pessimistic lock. Catalogue input does not expose quantity, so normal product editing cannot bypass the movement ledger.

Archival changes the active flag rather than deleting a product. Historical movements and warnings can still refer to the same identifier. This is useful when a product is discontinued: explanation of earlier stock must remain available even though the catalogue no longer accepts new operations for it.
### Inventory movement ledger
The movement relationships in {fig:er-movements} connect the operational change to both product and actor. Each accepted row stores type, signed delta, before and after quantities, a mandatory reason, request key and server timestamp. The composite unique constraint on actor and idempotency key is independent of the product. Its purpose is to prevent one authenticated actor's key from identifying multiple accepted intentions.
@fig er-movements|diagrams/13-er-movements.png|Mandatory product and actor relationships in movement history
@schema inventory_transactions

The ledger is retained by application behavior: there is no edit or delete endpoint for accepted movements. This is not a cryptographic tamper-evidence mechanism. Database administrators, backup tools and direct SQL have a different authority boundary. A production audit requirement would need to specify retention, access controls and possibly append-only or signed storage beyond this application-level history.
### Warning episodes and review attribution
The warning model in {fig:er-warnings} stores severity, lifecycle state, observed quantity, threshold and timestamps. Review attribution is optional. An open episode therefore has two independent dimensions: the shortage or recovery lifecycle and whether a person has acknowledged it. The design does not encode acknowledgement by replacing OPEN with a reviewed state.
@fig er-warnings|diagrams/14-er-warnings.png|Warning episodes with optional reviewer attribution
@schema warnings

Observed quantity and threshold describe the current episode interpretation. They are updated while a shortage remains within the same severity. They are not a snapshot of every stock movement; the movement table supplies that history. A new severity closes the old episode, while a healthy replenishment creates a recovery record that can remain visible temporarily.
### Supporting settings and revision data
Store settings are key-value pairs for the business name and display currency. The cache revision table contains a singleton counter that advances when stock, thresholds or other warning-relevant state changes. It is not a timestamp, demand estimate or session store. Keeping the counter durable makes cache namespaces survive an application restart consistently with database state.
@fig er-support|diagrams/15-er-support.png|Independent settings and cache revision tables
@schema app_settings
@schema cache_revision

The global counter is simple, but it is also a shared write target. Updates to different products can contend on that row even when product locks differ. The current workload does not quantify this contention. A future high-write deployment could consider partitioned revisions or another invalidation design after preserving the same post-write query contract.
## UML classes and repository dependencies
The domain class diagram in {fig:domain-classes} shows the implemented Product, UserAccount, InventoryTransaction and WarningEpisode relationships. Its attributes use the source-level visibility of the current entity classes. The diagram focuses on the core associations and selected fields; the schema tables provide the complete persistence fields. A class diagram and an ER diagram answer different questions: one explains program objects, while the other explains stored relationships and constraints.
@fig domain-classes|diagrams/16-uml-domain.png|Core domain classes and their implemented associations

The dependency diagram in {fig:service-classes} identifies InventoryService methods and the repository interfaces used by the stock and warning paths. A repository dependency does not transfer responsibility for an operation's overall consistency. For example, saving a transaction row is only one step: the service must also assign the quantity, evaluate warning state and advance revision before the encompassing transaction completes.
@fig service-classes|diagrams/17-uml-service.png|Inventory service dependencies on repository interfaces
## Transactional stock consistency
### Product locking and bounded arithmetic
The server first loads the authenticated actor and acquires a product-row locking read. MySQL documents locking reads as a mechanism for reserving a row for coordinated updates until commit or rollback [@mysql-locks]. Spring Data JPA exposes repository-level lock modes through its locking facilities [@spring-locks]. Shelfwise uses these mechanisms at the product boundary instead of calculating a new quantity from a previously displayed value.

The movement method uses READ_COMMITTED isolation and derives its delta from the locked product. Addition is checked for arithmetic overflow and for the supported quantity bounds. An absolute stocktake computes observed quantity minus the current locked quantity. A count equal to the current balance creates a zero-delta observation, while zero-delta relative adjustments are rejected. This distinction is a business rule, not an optimization of the write path.

The locked write coordinates product quantity, audit record, warning evaluation and revision advancement. If a domain or persistence exception aborts the transaction, the accepted database effects are rolled back together. The source uses a flush when saving the audit record so that certain integrity errors surface during the operation. Flushing is not a separate transaction commit.
### Idempotency and retry scope
After acquiring the product lock, the service checks the actor-key relationship for a prior movement. If the product, type, normalized reason and quantity meaning match, the original view is returned. For a count, the earlier after quantity is compared with the requested observed amount. For other types, the earlier signed delta is compared with the requested effect. A mismatched replay produces HTTP 409.

This ordering serializes the ordinary same-product retry path. The composite unique constraint adds a durable backstop. Simultaneously reusing a key across different products is a different contention pattern: separate product locks do not serialize it, and a uniqueness conflict may be the outcome rather than an exact-replay response. The current concurrent-identical test concerns one product. The thesis does not generalize it to every cross-product reuse race.
@table stock-consistency|Consistency controls and the problems they address
Control | Protected fact | Important boundary
Product row lock | Current balance used to derive the new result | Lock scope is one product
Transaction boundary | Quantity ledger warning and revision agree | Persistence exceptions must abort the whole operation
Actor-key uniqueness | One accepted movement per key namespace | Different actors may use the same textual key
Normalized replay comparison | Retry returns the prior intention's result | Reused key with changed content conflicts
Quantity bounds | Accepted balance is non-negative and bounded | Does not define decimal unit conversion
Mandatory actor and reason | Accepted movement remains explainable | Does not prevent privileged direct database modification
## Warning lifecycle design
The lifecycle in {fig:warning-state} separates shortage severity from recovery. Quantity zero selects OUT. Positive quantity at or below threshold selects LOW. Healthy quantity closes an open shortage and may create RESTOCKED. A transition between LOW and OUT closes the former severity and opens the latter. Remaining in one severity updates its quantity context without resetting review attribution.
@fig warning-state|diagrams/22-warning-state.png|Shortage and recovery episode lifecycle with independent acknowledgement

RESTOCKED has a stored expiry twenty-four hours after creation. Warning queries exclude expired recovery rows, and a scheduled cleanup marks expired recovery episodes resolved. The cache can retain a previously serialized page until revision or TTL changes; cleanup is periodic rather than instantaneous. The design therefore does not promise a zero-delay screen change at the expiry boundary. Dedicated clock-controlled expiry and cache-boundary tests would strengthen this part of the evaluation.

Acknowledgement locks the warning row and preserves the first recorded reviewer. Repeating acknowledgement returns the existing attribution. The interface offers the action for open unreviewed episodes. The service method itself checks whether a reviewer already exists but does not require an OPEN state, so an authorized API caller can first-review a resolved record by identifier. This is an explicit current behavior to review before defining a stricter production review policy.
## Revision-based cache design
The warning query first reads the durable revision and constructs a key containing revision, type, lifecycle state, page and size. A valid cache hit returns a decoded page. A miss or cache exception causes a database query and a best-effort fill with a thirty-second TTL. The sequence in {fig:cache-sequence} makes this alternate path visible. The database-backed revision is part of the read cost even when Redis has the response.
@fig cache-sequence|diagrams/20-seq-warning.png|Warning retrieval through a revision namespace and cache-aside fallback

A cache fill that began before a write can complete under the old revision. A later query reading the new revision will not address that old key. This addresses a stale-fill race that simple deletion alone would not describe. It does not cancel in-flight reads or establish a globally synchronized view across all open browser screens. A user may need a new read to observe the committed change.

The SQL filtering precedes pagination so totals correspond to the requested warning type and lifecycle selection. Page content, total elements and total pages are serialized together. Cache equivalence is therefore defined over the response contract, not merely over the first displayed row. Malformed cached JSON and broader database outages remain useful fault cases beyond the recorded Redis interruption.
## Permissions and request security
The authorization matrix in {tab:role-matrix} is implemented by HTTP method and route patterns. Threshold changes have a narrower route so managers can alter stock policy without editing SKU, name or supplier. Posting a movement is allowed for administrators and clerks. Warnings and reports are allowed for administrators and managers. Staff accounts and settings changes are administrator operations.
@table role-matrix|Server authorization matrix
Operation | Administrator | Manager | Clerk
Read inventory and movement history | Yes | Yes | Yes
Post receipt dispatch adjustment or count | Yes | No | Yes
Create edit or archive product | Yes | No | No
Update stock thresholds | Yes | Yes | No
Read warning board and reports | Yes | Yes | No
Acknowledge a warning | Yes | Yes | No
Manage users and access | Yes | No | No
Change store preferences | Yes | No | No
Read stock summary and preferences | Yes | Yes | Yes

The request-security path in {fig:security} combines session identity, CSRF protection, account refresh and endpoint authorization. Spring Security's CSRF documentation identifies unsafe browser methods as requiring protection when credentials can be supplied automatically [@spring-csrf]. Shelfwise issues a token and sends the matching header for unsafe requests. The readable CSRF token has a different purpose from the HttpOnly session cookie.
@fig security|diagrams/23-security-flow.png|Security checks preceding controller execution

Password hashes use BCrypt, and session ID rotation occurs after authentication. Account access is reloaded from MySQL during later requests. These implemented measures do not supply rate limiting, MFA, password recovery or a completed penetration assessment. Production deployment would also require TLS and secure cookie configuration. The design chapter distinguishes those deployment obligations from the controls that are present in the source.
## Chapter summary
The design assigns authoritative state to MySQL, preserves accepted stock intentions and keeps shortage review separate from quantity. Its architecture supports one coordinated movement transaction and a disposable cache. The diagrams and schema describe the implementation as it exists, including the shared revision counter, fixed roles and session boundary. Chapter 4 explains how these choices appear in executable code and in the user interface.
