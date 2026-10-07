# System implementation
## Project organization and development baseline
The implementation consists of a Vue browser client, a Spring Boot service, versioned database migrations and Docker Compose deployment files. Maven and Java 21 build the backend, and the pinned package lockfile fixes the Vue bundle that Nginx serves. MySQL retains the business records, while Redis provides the optional warning-page cache. Release images are published to GHCR, with infrastructure images falling back to Docker Hub.

Within the com.shelfwise package, InventoryService coordinates accepted stock changes, and dedicated batch, warning, purchasing and review services supply the related domain behavior. On the client, a login view handles sign-in and a single workspace hosts the selected task. At startup Flyway applies migrations V1–V8 and Hibernate validates the entity mappings, so a failed migration prevents the application from starting. Demonstration data is seeded only when configured and never overwrites existing accounts or stock. The complete collection of interface captures and source excerpts is available in thesis/figure-assets/index.html; this chapter shows a representative selection.
## API routes and interface navigation
The resource families below /api separate authentication, catalog identity and accepted movements from the stateful batch, warning, purchasing and review operations. {tab:route-groups} summarizes their responsibilities, and Appendix A lists the individual routes.
@table route-groups|API resource groups and their implemented purpose
Resource group | Representative path | Responsibility
Authentication | /api/auth/login and /api/auth/me | Establish and inspect the session
Catalog | /api/products and /api/products/{id} | Identity and filtered inventory
Threshold policy | /api/products/{id}/thresholds | Manager-accessible policy update
Reference data | /api/categories and /api/suppliers | Product grouping and partners
Batch inventory | /api/batches and /api/batches/{id}/control | Balances and quarantine
Purchasing | /api/replenishment and /api/purchases | Suggestions, approval and receipts
Stock reviews | /api/stock-reviews and action resources | Reviewed corrections and counts
Movement ledger | /api/transactions | Accepted commands and history
Warnings | /api/warnings and /api/warnings/{id}/ack | Conditions and reviewer attribution
Reporting | /api/dashboard and /api/reports/summary | Recorded stock summaries
Administration | /api/users and /api/settings | Account access and preferences

Before any protected navigation, Vue Router restores the current account, and a query parameter selects the workspace view. The HTTP client centralizes credentials and CSRF headers and redirects to sign-in after an unauthenticated response, but authorization is decided on the server for every request. Controllers map failures to distinct responses for invalid input, missing authentication, insufficient permission, absent records and conflicts. Product filtering is expressed as database predicates with allow-listed sort fields, an ID tie-breaker and a page-size limit of one hundred. Because an equivalent stock retry returns its original movement with HTTP 201, clients recognize a replay by the returned identifier rather than by the status code.
## Authentication and session implementation
The login screen in {fig:login-desktop} collects the user's credentials; the stockroom image beside the form is decorative. Signing in first obtains a CSRF token, then validates that the account is enabled and that the password matches its hash, rotates the session identifier and stores the security context. From then on, controllers take the actor of every movement from the authenticated session and never accept an actor ID in the request body.
@fig login-desktop|ui/01-login-desktop.png|Desktop login with illustrative stockroom content

Effective permissions follow the role matrix of Chapter 3. Managers change thresholds and approve reviews but cannot post ordinary movements. Clerks receive, dispatch and record SALE movements, and they submit corrections and counts for approval rather than applying them directly; administrators retain that direct access. Because the enabled flag and role are reloaded on each request, a change of access applies immediately. Restarting the application can end in-process sessions, but inventory data in MySQL is unaffected.

The effect of these bundles is visible in the navigation itself. The clerk's workspace in {fig:clerk-ui} offers inventory, batches, purchasing, stock reviews, stock activity and the catalog directories, but no warning board, reports or administration entries. The movement list on the same page shows the before and after balances, actor and reason of each accepted change.
@fig clerk-ui|ui/25-clerk-workspace.png|Clerk workspace with role-restricted navigation and attributed stock activity
## Overview and inventory inspection
The dashboard combines current-stock summaries, the movement trend, the category mix and a list of priority products. Its seven-day series counts all movements by UTC date, including receipts and corrections; the stock value multiplies physical quantity by current price; and category totals add unit counts without normalizing different units. These definitions keep the operational summaries distinct from sales or accounting figures. {fig:dashboard-ui} shows the administrator's overview, including the products that currently need attention and shortcuts to the most frequent stock tasks.
@fig dashboard-ui|ui/02-dashboard.png|Administrator overview with stock summaries, movement trend and priority products

The reporting page in {fig:reports-ui} expands these summaries. Beside the daily movement series and category mix, it breaks recorded activity down by movement type, shows the share of healthy, low and out-of-stock products by sellable quantity, counts open warnings by rule and ranks the products furthest below their reorder level. A note on the page repeats that inventory value is a current-price estimate rather than supplier cost.
@fig reports-ui|ui/09-reports.png|Reporting page with movement types, sellable stock health and open warning composition

The inventory view in {fig:inventory-ui} shows each product's identity, quantity, threshold context and price, together with search and pagination controls. Stock health is conveyed by text labels as well as colors. The browser requests twelve products per page and the server returns the filtered total. A search without matches offers a reset of the filters, whereas a failed request is shown as an error, so the two situations cannot be confused.
@fig inventory-ui|ui/03-inventory.png|Inventory quantities, policy context and pagination
## Catalog and supporting administration
The catalog view in {fig:catalog-ui} works on the same product records as the inventory view, listing sellable and physical quantities next to each product's category, status and price. Administrators create products with zero stock and edit their identity, references and policy; opening stock is then recorded as a movement like any other receipt. Each edit validates the identifiers, references and threshold hierarchy, and a product lock coordinates policy changes with warning evaluation.
@fig catalog-ui|ui/04-catalogue.png|Product catalog with sellable and physical quantities

The two edit forms in {fig:product-forms} show how the role boundary appears in the interface. The administrator's form (a) exposes identity, references, unit, price and both thresholds, whereas the manager's form (b) presents the same product with every field except safety stock and reorder threshold disabled, matching the narrow threshold endpoint. Neither form contains a quantity field; both state that stock changes only through a recorded transaction.
@fig product-forms|ui/15-edit-product.png+ui/23-manager-thresholds.png|Product editing by role: (a) administrator edit form; (b) manager threshold-only form

Categories group products, and supplier records hold partner contact details; foreign-key constraints prevent the deletion of either while it is still referenced. Archiving a product preserves its history, rejects new movements and resolves its open warnings. Staff administration, shown in {fig:team-ui}, never exposes password hashes, offers only the three fixed roles, lets an administrator pause an account instead of deleting it and protects the last enabled administrator. Store preferences change the displayed store name and currency label without converting prices, and the CSV export contains the inventory page currently loaded. The category, supplier and settings screens follow the same pattern and are included in the supplementary figure collection.
@fig team-ui|ui/10-team.png|Team access with fixed roles and account suspension
## Audited stock operations
### Locking and transactional coordination
Every stock change begins with the repository query in {fig:lock-code}, which acquires a pessimistic lock on the product row. The service then checks the active flag and the actor-scoped request key against this locked state. The balance the user saw in the browser serves only as context; the authoritative before quantity is always the one read under the lock.
@fig lock-code|code/01-code-product-lock.png|Repository product locking query

The sequence in {fig:movement-sequence} follows a request from authentication through the replay check and validation to the MySQL commit. A request for an archived product is rejected, an equal replay returns the movement already accepted, and a reused key with altered content produces a conflict. Only a genuinely new movement updates quantity, batches, audit history, warnings and cache revision, all within one transaction.
@fig movement-sequence|diagrams/19-seq-stock.png|Stock validation, replay and database commit

The service method in {fig:movement-code} implements this path. It trims the reason, compares receipt metadata with any prior movement, derives the signed effect and detects arithmetic overflow with Math.addExact, keeping the resulting quantity between zero and one billion. For a stocktake the delta is derived from the observed absolute count, and an unchanged count still produces a zero-delta record. Each accepted row stores the actor, reason, timestamp and before and after quantities.
@fig movement-code|code/02-code-stock-transaction.png|Transactional stock changes with replay and audit coordination
### Input semantics and browser retries
The receipt form in {fig:receipt-ui} submits a STOCK_IN movement with a positive quantity, a reason and optional batch dates; the capture shows an unsubmitted draft. STOCK_OUT and SALE also take positive input but reduce stock, and only SALE feeds the sales signal used by the slow-moving rule.
@fig receipt-ui|ui/16-stock-receipt.png|Representative receipt form with batch metadata

ADJUSTMENT expects a signed, non-zero change, whereas STOCKTAKE expects an absolute, non-negative count: with a balance of eight, an accepted count of three yields a delta of minus five. Administrators may post either directly, while clerks submit them as reviews. On approval, a COUNT is validated against its quantity and version snapshot, a DISPOSAL against the current batch remainder, and an ADJUSTMENT is applied to the current locked balance. {fig:adjust-count} contrasts the two forms: the adjustment asks for a quantity change that may be positive or negative, while the stocktake asks for the counted quantity. Both require a reason and remind the user that the entry records their name, the time and the before and after quantities.
@fig adjust-count|ui/18-stock-adjustment.png+ui/19-stocktake.png|Relative and absolute stock input: (a) signed adjustment; (b) absolute stock count

To make retries safe, the browser keeps one request key for as long as the form stays open and blocks a second save while the first is pending. {fig:form-code} shows the UUID generation and the pending-submit check. The key survives an error, so a retry after a lost response retrieves the result that was already accepted. The client guard reduces duplicates but cannot replace the server's handling of repeated HTTP requests.
@fig form-code|code/14-code-stock-form.png|Client request-key retention and pending-submit guard
### Attributed history
The history page in {fig:history-ui} lists each movement's product, type, actor, reason and before and after balances. Corrections appear as later records rather than as edits, and the unique database constraint on actor and request key backs the replay check. The application offers no endpoint for editing or deleting accepted movements; direct SQL access by a privileged administrator remains a separate authority boundary.
@fig history-ui|ui/07-history.png|Attributed movement history and quantity arithmetic
## Warning review and cached retrieval
The warning board in {fig:warnings-ui} shows each episode's type, its quantity or batch context, the threshold and the review status. Acknowledging a warning leaves the stock quantity unchanged. A first acknowledgement requires an OPEN episode, whereas an existing acknowledgement can be replayed even after resolution. Managers adjust thresholds through a deliberately narrow endpoint that cannot touch identity fields.
@fig warnings-ui|ui/08-warnings.png|Warning conditions and independent reviewer attribution

The code in {fig:lifecycle-code} evaluates the current episodes of a product, resolves superseded conditions and records recovery. A shortage that continues at the same severity keeps its reviewer, batch-age and sales-history rules contribute their own conditions, and archiving a product resolves its open episodes. Chapter 5 tests the critical boundaries of these transitions.
@fig lifecycle-code|code/05-code-warning-lifecycle.png|Warning transition and recovery coordination

The cache in {fig:cache-code} keys each response by the durable revision, the filters and the pagination parameters. If Redis fails, the query falls back to the database and the optional fill is abandoned. Filtering happens in SQL before pagination, and the complete page is serialized with a thirty-second TTL. Because every relevant write advances the revision, later readers can never pick up a fill stored under the old one. Redis thus plays no part in authenticating sessions or deciding stock changes.
@fig cache-code|code/04-code-warning-cache.png|Revision-keyed cache with database fallback
## Batch inventory, purchasing and stock reviews
The batch view in {fig:batches-ui} shows physical and sellable balances, dates and quarantine status. Expired or quarantined stock remains on hand for disposal but is withheld from ordinary dispatch. Dated batches are allocated by FEFO, and undated stock is ordered by receipt time and identifier.
@fig batches-ui|ui/28-batches.png|Physical and sellable batch inventory

The Purchasing view in {fig:purchasing-ui} combines replenishment suggestions with purchase documents. A suggestion compares sellable stock plus the quantity still pending on approved orders with the product's trigger and target levels. Drafting, submission, approval and receipt are separate actions: a rejected document can be edited and resubmitted, and approved or partially received documents accept further receipts.
@fig purchasing-ui|ui/29-purchasing.png|Suggestions and purchase workflow

The guards in {fig:purchasing-code} enforce these transitions. Approval locks the order and its products in a stable order and rechecks the current suggestion. A receipt validates its actor-scoped key and the remaining approved amount, posts a batch-aware STOCK_IN and advances the order to PARTIAL or COMPLETED. Cancellation keeps any stock already received and closes the remainder, and a completed order cannot be cancelled.
@fig purchasing-code|code/15-code-purchasing.png|Purchase approval and state-transition guards

The Stock reviews view in {fig:reviews-ui} keeps requests for observation and correction apart from the mutations they eventually cause. The creator and the reviewer are recorded separately, and an approved review is linked to the movement it produced. A stale COUNT cannot overwrite a later receipt, and a DISPOSAL cannot remove a remainder that has already been consumed.
@fig reviews-ui|ui/30-stock-reviews.png|Submitted stock reviews and approval decisions

{fig:batch-workflow} relates batches, allocations and approved reviews to the movement history. Allocations record which batches a movement affected, while the ledger records the product-level arithmetic; both are written in the same transaction. An approved disposal also reduces the remaining quantity of its selected batch.
@fig batch-workflow|diagrams/27-batch-fefo.png|Batch allocation and reviewed stock changes
## Responsive access and deployment
Phones use the same client and backend as desktop browsers. The capture in {fig:phone-inventory-ui} shows the inventory at a width of 390 CSS pixels, with wide tables scrolling inside their own container; the recorded check found no overflow of the page itself. A broader usability and accessibility evaluation lies outside the selected scenarios.
@fig phone-inventory-ui|ui/27-mobile-inventory.png|Responsive inventory at 390 CSS pixels

In the release deployment shown in {fig:deployment}, Nginx serves the static assets and proxies /api and /actuator to Spring Boot. MySQL holds all transactions, and Redis may accelerate warning reads. Release images, secrets supplied through the environment, health checks and a named MySQL volume make start-up reproducible. Infrastructure images fall back to Docker Hub when the GHCR pull fails, and Redis persistence is disabled because cached pages are disposable.
@fig deployment|diagrams/24-deployment.png|Release deployment with durable MySQL and optional Redis

Git and image tags identify each release, and the manifests and migrations pin its dependency and schema baselines. Production operation would additionally require TLS, secure cookies, private database networking, verified backup and restore, and shared or affine sessions once more than one application node is deployed.
## Chapter summary
The implementation turns each stock intention into an attributable movement with its batch allocations and warning transitions, while the review and purchasing workflows validate state and snapshots before any correction takes effect. Chapter 5 evaluates these mechanisms.
