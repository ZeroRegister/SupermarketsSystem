# System implementation
## Project organization and development baseline
The implemented repository contains backend, frontend, Dockerfiles, Compose manifests, scripts, documentation and thesis materials. The backend is built with Maven and Java 21 in a multi-stage image. The browser application uses the pinned dependencies in its package manifest and lockfile, is built by Node.js and is served by Nginx in the release image. MySQL and Redis run as Compose services; a release Compose file can pull all four images from GHCR. The thesis figures are maintained with editable sources and provenance so that interface evidence can be connected to a particular source revision and capture time.

Backend domain entities, request and response records, repository interfaces, controllers, the inventory service and security configuration are kept in the com.shelfwise package. The organization is compact rather than a separate class file for every domain object. It exposes the main consistency path in one service but would need further decomposition as more workflows are added. The frontend similarly uses a login view and a substantial workspace view with several operational sections.

Flyway applies the initial migration, and Hibernate validates the entity mapping at startup. A migration failure prevents normal service startup rather than silently recreating tables. Demonstration seeding is guarded by configuration, password length and the presence of existing user records. It does not overwrite existing accounts when a local environment password changes. This behavior preserves previously created state during ordinary restarts.
## API routes and interface navigation
The application exposes JSON resources below /api. Authentication endpoints obtain a CSRF token, create a session, return the current account and log out. Catalogue paths create, edit and archive products. A separate threshold path narrows manager authority. Transactions represent accepted stock operations. Warnings support filtered retrieval and review attribution. Reports, users and preferences have their own permission boundaries.
@table route-groups|API resource groups and their implemented purpose
Resource group | Representative path | Responsibility
Authentication | /api/auth/login and /api/auth/me | Establish and inspect the session
Catalogue | /api/products and /api/products/{id} | Product identity and filtered inventory
Threshold policy | /api/products/{id}/thresholds | Manager-accessible policy update
Reference data | /api/categories and /api/suppliers | Product grouping and partner directory
Batch inventory | /api/batches and /api/batches/{id}/control | Batch balances, sellable quantity and quarantine
Purchasing | /api/replenishment and /api/purchases | Suggestions, drafts, approval and receipts
Stock reviews | /api/stock-reviews and action resources | Snapshot-based count and disposal review
Movement ledger | /api/transactions | Accepted stock commands and history
Warnings | /api/warnings and /api/warnings/{id}/ack | Episode retrieval and reviewer attribution
Reporting | /api/dashboard and /api/reports/summary | Recorded stock summaries
Administration | /api/users and /api/settings | Accounts access and workspace preferences

Vue Router separates the login path from the workspace. Within the workspace, a query parameter selects the operational view. Route guards restore the current account and redirect selected unauthorized deep links. The code in {fig:route-code} shows the actual guard. It is an interface aid: the server still checks every API operation, including a request made without Vue Router.
@fig route-code|code/09-code-navigation.png|Authenticated navigation and role guards in the frontend source

The browser API client uses credentials on requests and centralizes CSRF preparation and headers. Its response interceptor triggers session recovery behavior when a protected request is unauthenticated. The source in {fig:client-code} provides a shared place for these rules, reducing the chance that one form submits an unsafe request differently from another.
@fig client-code|code/08-code-api-client.png|Typed client functions and the unsafe-request CSRF header

Application errors distinguish invalid input, lack of authentication, lack of authority, missing records and conflicts. Controllers validate supported warning filters before calling the service. Database uniqueness or referenced-record failures become conflicts. A replay can return the original movement while retaining the transaction endpoint's 201 response annotation; clients should use the returned identifier to recognize equivalence rather than assume every 201 created a new row.
## Authentication and session implementation
The desktop login screen in {fig:login-desktop} collects account credentials without exposing the password in a response. Its left-side stockroom preview is explicitly illustrative interface content. The authenticated dashboard is obtained later from the server. The login screen should not be treated as performance or current-inventory evidence merely because it contains stock-themed graphics.
@fig login-desktop|ui/01-login-desktop.png|Desktop login interface with an illustrative stockroom preview

The authentication sequence in {fig:login-sequence} begins with CSRF preparation, submits credentials and delegates authentication to the configured manager. The user repository supplies the enabled account and hash. Successful authentication rotates the session identifier and stores the security context in the servlet session. The persistent user table and the in-process session are distinct stores.
@fig login-sequence|diagrams/18-seq-login.png|Authentication interaction with the user repository and servlet session

The code excerpt in {fig:login-code} contains the corresponding controller operation. User-facing data is returned through a view record. The username and role are not accepted from later movement payloads as actor authority: controllers obtain the principal from the server authentication context. Restarting the sole application process can invalidate its in-memory sessions without removing the durable inventory records.
@fig login-code|code/07-code-session-login.png|Credential authentication and session ID rotation in the controller

The security rules in {fig:security-code} define the implemented endpoint permissions and CSRF handling. They are a clearer basis for assessing authority than whether a sidebar item happens to be visible. For example, managers can patch thresholds but cannot post a movement, while clerks can post a movement but cannot acknowledge a warning.
@fig security-code|code/06-code-security.png|Implemented security filter configuration and role-specific route rules
## Overview and inventory inspection
The dashboard in {fig:dashboard-ui} combines a current-stock summary, movement trend, category mix, priority products and quick links. It is intended to help the manager identify the next inspection task. Counts and value come from server aggregation over active products. The display does not estimate customer demand or independently establish that a replenishment will arrive.
@fig dashboard-ui|ui/02-dashboard.png|Administrator overview rendered from the current demonstration database

The movement trend uses the recorded seven-day date series. Zero-activity days appear as zero rather than being omitted. The category visualization sums current unit counts. These definitions matter when interpreting the graphic: a spike means more recorded movements, and combining bottles with kilograms does not produce a standardized physical measure. Detailed numerical evaluation is presented separately in Chapter 5.

The inventory interface in {fig:inventory-ui} provides search, category and stock-health filters, quantities, threshold context, unit price and paging. It also shows the role-appropriate product actions. Quantity is presented with its unit and reorder level so that a red or amber badge can be interpreted without relying only on color.
@fig inventory-ui|ui/03-inventory.png|Inventory page with product identity quantity policy context and pagination

Filtering is implemented as database predicates. The source in {fig:filter-code} selects active or archived products, combines text and category conditions, and distinguishes OUT, LOW and healthy quantities. Sorting uses an allow-list and ID tie-breaker, while page size is capped. The code explains why the result count belongs to the selected query rather than to a separately filtered browser array.
@fig filter-code|code/03-code-product-filter.png|Server-side inventory predicates and bounded stable pagination
## Catalogue administration
The catalogue view in {fig:catalogue-ui} shares inventory data with an administrative emphasis. The separate view name is a navigation choice rather than a second stock store. Administrators can create and edit identity fields, set references and configure policy. Stock remains outside the catalogue payload.
@fig catalogue-ui|ui/04-catalogue.png|Product catalogue view within the same inventory workspace

The creation form in {fig:add-product-ui} collects product identity, unit, price, references and thresholds. It explains that stock changes through a recorded transaction. A newly created product begins with zero quantity; opening stock must be entered through a stock operation so that the accepted balance has an explanation. The screenshot is a captured draft form, not a posted creation result.
@fig add-product-ui|ui/14-add-product.png|Product creation form with no direct quantity editor

The existing-product form in {fig:edit-product-ui} displays stored descriptive and policy values. Its save operation checks uniqueness and reference validity. It acquires a product lock before applying changes that can affect warning interpretation. Preserving quantity during editing prevents an administrator from inadvertently erasing the meaning of the ledger while correcting a product name.
@fig edit-product-ui|ui/15-edit-product.png|Product edit form populated from an existing catalogue record

The category page in {fig:categories-ui} groups products through named categories and optional descriptions. The related creation form in {fig:category-form-ui} exposes those fields. Category identifiers are referenced by products; category cards and filtering are views of that relationship. Referenced deletion conflicts preserve consistency instead of detaching records silently.
@fig categories-ui|ui/05-categories.png|Category administration and links to grouped inventory
@fig category-form-ui|ui/20-category-form.png|Category creation form captured without submission

The supplier directory in {fig:suppliers-ui} provides partner names and available contact details. The form in {fig:supplier-form-ui} creates descriptive supplier data. The supplier directory remains descriptive, while the Purchasing view turns a replenishment suggestion into a draft purchase document. Approval and receipt are separate actions; a receipt creates a batch-aware stock movement, while payment and supplier settlement remain outside the implementation.
@fig suppliers-ui|ui/06-suppliers.png|Supplier directory with descriptive partner information
@fig supplier-form-ui|ui/21-supplier-form.png|Supplier creation fields for name and contact information
## Audited stock operations
### Locking and coordination
The product repository exposes a pessimistic locking query, shown in {fig:lock-code}. The service uses it before inspecting the active flag, calculating a result or checking the ordinary same-product retry path. A value previously displayed by the browser is never used as the authoritative before quantity.
@fig lock-code|code/01-code-product-lock.png|Repository query that acquires the product write lock

The interaction in {fig:movement-sequence} connects browser intention, controller authentication, service decisions and MySQL commit. Its return path includes the accepted movement view with attributed quantities. It represents the normal request path and selected replay checks, rather than a claim that every database or network failure is handled by a distributed recovery protocol.
@fig movement-sequence|diagrams/19-seq-stock.png|Stock intention validation and database commit sequence

The workflow in {fig:movement-flow} emphasizes where a request can terminate without applying another change: archival rejection, equivalent replay, conflicting replay or invalid quantity. The accepted path writes the new quantity, audit row, warning changes and revision. This makes the order visible before the reader inspects the compact source.
@fig movement-flow|diagrams/21-stock-flow.png|Stock transaction workflow including replay and quantity boundaries

The source in {fig:movement-code} implements these steps in one transactional method. The reason is trimmed for comparison and storage. Before and after quantities are assigned by the service. Math.addExact detects overflow before the supported bounds are applied. An absolute count uses the locked balance when deriving delta, which makes repeated display values irrelevant to its arithmetic.
@fig movement-code|code/02-code-stock-transaction.png|Actual stock movement method with audit idempotency and warning coordination
### Receipt and dispatch forms
The receipt form in {fig:receipt-ui} presents a positive quantity and reason. It identifies the selected product and current display quantity as context. Saving the form submits STOCK_IN, and the server accepts a positive effect only after checking the request and product. The captured figure uses an existing demonstration product and an unsubmitted reason draft.
@fig receipt-ui|ui/16-stock-receipt.png|Receiving form as an unsubmitted demonstration of the stock command

The dispatch form in {fig:dispatch-ui} also asks for a positive input amount. The operation type gives it a negative stock effect on the server. This interface avoids asking staff to enter a minus sign for an ordinary dispatch. A displayed balance can become stale; insufficient-stock protection must consequently remain in the locked server operation.
@fig dispatch-ui|ui/17-stock-dispatch.png|Dispatch form with positive input and server-derived negative delta
### Adjustment and physical count forms
The adjustment form in {fig:adjustment-ui} uses a signed change and makes that interpretation explicit. It can represent removal of damaged goods or addition of a known correction. A zero adjustment is rejected because it does not describe a relative change. Its reason explains why the correction differs from routine receiving or dispatch.
@fig adjustment-ui|ui/18-stock-adjustment.png|Adjustment form with an explicitly signed quantity change

The count form in {fig:count-ui} instead asks for the observed absolute quantity. If the recorded locked balance is eight and the count is three, the service writes a delta of negative five. A count equal to eight still records an observation with zero delta. The distinction between count and adjustment is preserved by the type field, labels and integration tests.
@fig count-ui|ui/19-stocktake.png|Stocktake form using an absolute counted quantity

The browser retains a request key for the opened form and guards against a simultaneous second save while a request is pending. The source in {fig:form-code} shows this client behavior. It reduces accidental repetition but does not replace server idempotency: a lost response or manually repeated HTTP request can bypass a disabled button.
@fig form-code|code/14-code-stock-form.png|Client request-key retention and stock-form submission guard
### Attributed history
The history page in {fig:history-ui} connects each accepted operation to product, actor, reason, timestamp and before-and-after balance. Relative adjustments and counts remain distinguishable by their type. This view provides an explanation when the current inventory is questioned, rather than merely recording that some field was edited.
@fig history-ui|ui/07-history.png|Movement history preserving actor reason and before-and-after quantities

The persistence excerpt in {fig:schema-code} contains mandatory actor and product references and the composite request-key uniqueness constraint. It also shows the warning table alongside the ledger. The database constraint protects accepted uniqueness even when concurrency bypasses an application-level prior-result check.
@fig schema-code|code/10-code-schema.png|Flyway ledger and warning definitions including the actor-key constraint
## Warning review and cached retrieval
The warning board in {fig:warnings-ui} presents shortage type, current quantity, threshold, detection time and review status. The note below the table explains that acknowledgement does not change stock. This is part of the operational meaning of the interface: a reviewed out-of-stock item remains out of stock until a separate movement changes it.
@fig warnings-ui|ui/08-warnings.png|Warning board showing shortage context and independent reviewer attribution

The lifecycle code in {fig:lifecycle-code} examines open episodes, chooses severity, resolves prior types and creates recovery when stock becomes healthy. Continued same-severity shortage updates its context while retaining attribution. Archived products resolve their open episodes and cannot accept future movements. This behavior is checked by selected tests rather than inferred solely from a badge color.
@fig lifecycle-code|code/05-code-warning-lifecycle.png|Warning episode transitions in the implemented inventory service

The cache implementation in {fig:cache-code} incorporates the durable revision into each warning-page key. Exceptions during Redis access lead to database retrieval or a failed optional fill, while SQL filtering occurs before pagination. Redis does not store the servlet session, allocate stock or authenticate users. Its limited role is important when interpreting the recovery and performance results.
@fig cache-code|code/04-code-warning-cache.png|Revision-keyed warning retrieval with database fallback and TTL

The manager workspace in {fig:manager-ui} exposes warning review without administrator account controls. The threshold edit form in {fig:threshold-ui} disables descriptive product fields for that role. Its narrower PATCH endpoint prevents the manager from changing SKU or price through the threshold operation even if a client attempts to send additional catalogue data.
@fig manager-ui|ui/24-manager-workspace.png|Manager workspace for warning inspection and review

## Batch inventory, purchasing and stock reviews
The batch page in {fig:batches-ui} exposes physical and sellable balances, expiry dates and quarantine state. It makes the distinction between what is present in the stockroom and what can be dispatched visible to the user.
@fig batches-ui|ui/28-batches.png|Batch inventory view with sellable balance and expiry information

The Purchasing view in {fig:purchasing-ui} combines replenishment suggestions with purchase documents. Its table keeps the trigger, target, pending position and suggested quantity visible together; the corrected header layout prevents English labels from breaking into isolated characters.
@fig purchasing-ui|ui/29-purchasing.png|Replenishment suggestions and purchase workflow interface
@fig purchasing-code|code/15-code-purchasing.png|Purchase approval and partial receipt service path

The Stock reviews view in {fig:reviews-ui} separates a physical count or disposal request from immediate stock mutation. A manager approves the snapshot after the service rechecks the current product or batch state.
@fig reviews-ui|ui/30-stock-reviews.png|Snapshot-based stock count and disposal review interface
@fig batch-workflow|diagrams/27-batch-fefo.png|Batch receipt, FEFO/FIFO allocation and review-controlled disposal
@fig threshold-ui|ui/23-manager-thresholds.png|Threshold-only product edit form presented to a manager
## Reports and administration
The reports view in {fig:reports-ui} presents the value estimate, active products, low and out-of-stock counts, movements and category mix. Its explanatory labels state that current quantity times current price is an estimate and that movement dates use UTC. These qualifications identify what the graphic represents before a reader attempts to interpret a trend as sales or profit.
@fig reports-ui|ui/09-reports.png|Implemented reporting view with explicit definitions of its metrics

The staff page in {fig:team-ui} presents fixed role bundles and account status. Administrative changes become effective on later server requests because access is reloaded. The creation form in {fig:account-form-ui} collects a display name, username, temporary password and role. Password fields are not returned in the staff list. The last-enabled-administrator control is enforced by service behavior, not by a decorative role card.
@fig team-ui|ui/10-team.png|Staff administration with role and enabled-account controls
@fig account-form-ui|ui/22-account-form.png|New staff-account form with role selection

The store settings page in {fig:settings-ui} controls the displayed business name and currency. Its currency help text states that no exchange-rate conversion occurs. The current schema stores preferences as key-value entries, so introducing accounting currency or historical conversion would require a different data policy rather than merely adding another option to this select control.
@fig settings-ui|ui/11-settings.png|Store preferences and the display-only currency setting

The clerk view in {fig:clerk-ui} provides movement recording and history without warning or staff-management operations. A direct link to a protected view is redirected by the browser guard, while a forbidden API action receives server denial. The distinction allows the user experience and the authority boundary to be assessed independently.
@fig clerk-ui|ui/25-clerk-workspace.png|Clerk stock-activity workspace with role-appropriate controls
## Responsive Web behavior
Phone-sized access uses the same browser application and backend. The login interface in {fig:phone-login-ui} adapts to the narrower viewport. It is not a React Native application and does not imply an iOS or Android package. The image records the actual responsive login layout at the captured browser size.
@fig phone-login-ui|ui/26-mobile-login.png|Responsive Web sign-in at a phone-sized viewport

The inventory image in {fig:phone-inventory-ui} is a full-page capture of the responsive page, including content that a user reaches by scrolling. Wide table content is confined to its own container. The capture check confirms that the document itself does not overflow the 390-pixel viewport. It does not establish usability on every device, touch target compliance or assistive-technology compatibility.
@fig phone-inventory-ui|ui/27-mobile-inventory.png|Full-page responsive Web inventory capture at 390 CSS pixels
## Version control and local deployment
The repository pins runtime and dependency baselines and excludes local secrets, service data, dependencies and compiler intermediates. Version control records code and document changes, while figure provenance records the source revision and capture time. The backend and frontend source manifests remain versioned independently, while the release deployment uses Git tags and GHCR image tags such as v1.2.2. This thesis distinguishes reproducible image delivery from a fully hardened production release process.

The topology in {fig:deployment} shows the release arrangement. A browser connects to the Nginx frontend container on port 5173; Nginx proxies `/api` and `/actuator` to the Spring Boot backend container. The backend connects to MySQL and Redis on the private Compose network. Development mode still supports Vite and host-run Java, but the deliverable for Windows uses prebuilt frontend and backend images. GHCR stores the application images and mirrored infrastructure images, while the MySQL named volume remains local to the deployment host.
@fig deployment|diagrams/24-deployment.png|Windows release topology with GHCR images and Docker Hub fallback

The Compose source in {fig:compose-code} supplies build-time Dockerfiles for development and a release manifest with prebuilt image references, environment-variable requirements, health checks, service dependencies and the MySQL named volume. The Windows helper first pulls from GHCR and falls back to official Docker Hub MySQL and Redis images if the GHCR infrastructure mirror is unavailable. It does not embed passwords. Redis persistence is disabled because cached responses are disposable; MySQL data must be retained and backed up independently of the application images.
@fig compose-code|code/11-code-deployment.png|Container configuration using environment references and durable MySQL storage

A production deployment would serve built assets through an appropriate Web server, terminate TLS, enable secure session cookies, keep database services private and define backups and restore drills. Multiple application nodes would also require session affinity or shared session storage. Those operations are future deployment requirements. The tested local development topology should not be presented as a complete hardened production platform.
## Chapter summary
The implementation translates the model into controls that preserve the meaning of each operation. Catalogue forms cannot directly assign stock, counts differ from adjustments, review differs from replenishment and Redis differs from durable storage. The interface images demonstrate how the implemented workflow is presented, while the source excerpts expose its critical mechanisms. The following chapter assesses the extent to which executable evidence supports those mechanisms.
