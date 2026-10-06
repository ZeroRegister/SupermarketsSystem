# Object analysis
## Description of the subject area
A supermarket inventory system records the relationship between identifiable products and quantities available for store operations. Products arrive through deliveries and leave through sales, transfers, damage or other dispatches. Physical counts provide observations that may disagree with the recorded balance. Even when the application does not execute a sale or purchase, it must represent the stock effect of those activities. The subject of this thesis is that inventory workflow within one store.

The current balance and the movement history serve complementary purposes. A balance answers a short operational question: how much of this product is recorded now? History answers a longer explanatory question: which accepted changes produced that balance? A system that stores only the balance cannot reconstruct an omitted reason or distinguish a double submission from two deliveries. A system that stores only events can explain changes but may require additional work to present fast, filtered inventory pages. Shelfwise stores the balance and its accepted movement records together.

The application uses product identity, category, supplier, unit and current price as descriptive context. SKU is a required unique identifier, and barcode is optional. Stock received through a purchase can carry a batch number, production date and expiry date. The unit label still describes a whole-number quantity: a label of kg does not introduce decimal weighing support. Sellable quantity excludes expired and quarantined batches, while physical quantity remains useful for disposal and reconciliation. A deployable weighing workflow would require fractional units and a defined rounding policy.

Inventory value is a presentation estimate obtained by multiplying each active product's current quantity by its current unit price. It is not supplier cost, historical cost of goods sold or an accounting valuation. The distinction prevents a convenient dashboard number from being used as evidence of financial correctness. The store currency preference changes the displayed currency code and symbol; it does not convert stored prices.
## Operational problems and system boundary
Manual stock work can fail in several different ways. A delivery may be entered twice after a slow response. Two dispatches may each use an old balance. A correction may be applied as a relative change when the staff member intended an absolute count. A manager may acknowledge a warning while the item is still out of stock. These are different problems, and their controls must preserve their meanings rather than translate them all into a generic update operation.

The system boundary includes product and reference-data administration, searchable inventory, receiving, dispatch, adjustment, stocktake, batch control, expiry and slow-moving warnings, warning review, replenishment suggestions, purchase drafts and approval, partial receipts, disposal/count reviews, reports and staff access. It excludes payment processing, supplier invoicing, checkout integration, customer reservations and multiple stores. A supplier record remains descriptive until a purchase document is created, and a purchase document remains a stock workflow until a receipt is accepted.

The selected store is a software case study using fictitious demonstration records. The work does not measure shelf availability or employee productivity in an operating supermarket. The practical motivation is the need for traceable inventory work; the evaluation measures software behavior under specified scenarios. This keeps the business context connected to a defensible engineering claim.
@table scope|Implemented domain and excluded extensions
Aspect | Implemented meaning | Extension outside the current boundary
Store organization | One shared store workspace | Tenant and branch isolation
Quantity | Bounded integer balance | Decimal weights and unit conversion
Stock operation | Receive dispatch adjustment stocktake with batch-aware receipt and dispatch | Checkout and reserved stock
Supplier | Product partner, replenishment suggestion and purchase workflow | Invoices and settlement
Warning | Quantity, expiry, slow-moving and recovery episodes with review | Demand forecasting and automatic purchasing
Financial display | Current price multiplied by sellable quantity as a presentation estimate | Accounting cost and profit
Phone access | Responsive browser interface | Native Android or iOS application
## Construction of the conceptual model
The overall model in {fig:functions} divides the system into identity and access, catalogue management, stock activity, warnings and reporting. These modules correspond to different responsibilities but share a product identity. Catalogue work defines what a product is and how it is classified. Stock work changes a bounded quantity. Warning work interprets a policy boundary and records review. Reporting summarizes the accepted facts for inspection.
@fig functions|diagrams/01-functional-model.png|Overall functional model of the supermarket inventory system

This division is useful when a requirement crosses several modules. Receiving stock changes a product, creates a movement, may resolve a shortage and changes dashboard totals. Treating these effects as separate responsibilities does not imply separate services. The design chapter shows why they remain coordinated within a single database transaction.
### Product catalogue model
A product has a SKU, optional barcode, name, unit, current price, category and optional supplier. Its stock policy contains safety stock and reorder threshold. The current quantity is displayed with the product but is not a catalogue input. Staff must use an inventory operation to change it. An archived product retains its identity and history while rejecting future stock movements.

The use cases in {fig:uc-catalogue} distinguish authority to change identity from authority to change policy. Administrators can manage the catalogue and archive products. Managers can inspect inventory and update thresholds. Clerks can inspect the product information needed to record stock. This model avoids granting catalogue write authority merely because someone performs daily receiving work.
@fig uc-catalogue|diagrams/02-uc-catalogue.png|Catalogue management use cases for the three implemented roles

Categories organize the inventory view and category totals. Suppliers provide descriptive partner information and may be associated with products. Neither reference type owns the stock balance. Deleting a referenced category or supplier conflicts with its foreign-key relationship; product archival provides a separate lifecycle for stock-bearing records.
### Stock activity model
Shelfwise exposes four types of movement. Stock received and dispatched use positive input quantities but have opposite signed effects. An adjustment uses a signed non-zero change. A stocktake uses an absolute observed quantity, from which the server derives the change while holding the product lock. The resulting record always preserves the actual before quantity, signed delta and after quantity.
@table movements|Meaning of stock input and resulting change
Movement type | Meaning of entered quantity | Derived delta | Operational example
STOCK_IN | Positive amount received | Positive entered amount | Morning delivery
STOCK_OUT | Positive amount dispatched | Negative entered amount | Goods leaving the stockroom
ADJUSTMENT | Signed correction | Entered signed amount | Two damaged units removed
STOCKTAKE | Absolute observed amount | Observed amount minus locked balance | Weekly physical count

The stock use cases in {fig:uc-stock} show that administrators and clerks can post these operations. Managers can read movement history but cannot post stock. Reading the ledger is therefore not equivalent to having authority to alter its operational result. The model also makes clear that the client submits an intention, not an authoritative before-and-after balance.
@fig uc-stock|diagrams/03-uc-stock.png|Stock operation and history use cases

A reason is mandatory for every accepted movement. Actor identity is derived from authentication. The timestamp is assigned by the server. These fields are not ornamental metadata: they are the minimum explanation available when a quantity is later questioned. A new correction should create another record rather than erase an earlier accepted movement.
### Warning and recovery model
A warning is a persisted episode connected to a product and a rule interpretation. OUT and LOW describe sellable quantity; EXPIRING and EXPIRED describe batch dates; SLOW describes a sales-only movement rule; RESTOCKED records a recovery interval. The business timezone controls the date boundary for expiry. A healthy replenishment can resolve a shortage and create a time-limited RESTOCKED episode. Warning acknowledgement remains independent from all of these conditions.

Acknowledgement records a reviewer and review time. It neither changes quantity nor resolves the shortage. The distinction is important after partial replenishment: a reviewed product may still be LOW, and the existing episode can retain its reviewer. A transition from LOW to OUT, or from OUT to LOW, creates a new severity episode and resolves the old one.
@fig uc-warning|diagrams/04-uc-warning.png|Warning inspection and acknowledgement use cases

The episode model supports both current attention and historical explanation. Open warnings tell the manager what currently needs review. Resolved records show that a shortage or recovery interval ended. The dashboard and warning board are views of these records, not independent sources of stock truth. Replenishment suggestions use sellable quantity, pending approved quantity and target stock; they do not silently create an order.
@fig warning-rules|diagrams/25-warning-rules.png|Warning rule evaluation across batches expiry sales history and threshold policy

### Batch and purchasing objects
A batch is the inventory identity used when a receipt carries production or expiry metadata. Physical quantity and sellable quantity are maintained separately. FEFO selects the earliest eligible expiry date; FIFO provides deterministic ordering when dates are absent. Quarantine is an explicit control state for a batch and does not erase its movement history.

A replenishment suggestion is derived from sellable quantity, pending purchase position, trigger threshold and target stock. A purchase document moves through DRAFT, SUBMITTED, APPROVED or REJECTED, and can be PARTIAL, COMPLETED or CANCELLED after receipt activity. This workflow turns a warning into a reviewable decision without claiming that the system has sent an external supplier order.
@fig purchasing-workflow|diagrams/26-purchasing-workflow.png|Replenishment suggestion through purchase approval and partial receipt

A stock review records a count or disposal intention against a quantity snapshot. Approval rechecks that snapshot and batch remainder before applying the resulting movement. This prevents a delayed approval from overwriting a later receipt or dispatch.
### Reporting model
Reporting presents active-product counts, shortage counts, the current-price value estimate, movement totals, recent activity and category mix. The seven-day activity chart counts recorded movements by UTC date. It is not a sales chart: receiving, adjustment and stocktake can also contribute entries. The category chart groups current unit counts, which are useful within this demonstration but do not normalize different physical units.
@fig uc-report|diagrams/05-uc-report.png|Inventory reporting and current-page export use cases

Inventory CSV export is a client-side export of the currently loaded product page. The distinction between one page and a complete database export matters when a filter matches more than twelve displayed products. The exported fields explain the visible selection; they do not represent a separate scheduled reporting service.
### Identity and administration model
The application uses the fixed ADMIN, MANAGER and CLERK roles. Users have a username, display name, password hash, role, enabled flag and creation time. Administrators create users and change access. Managers and clerks work within their assigned authority. Role changes and disabling are reloaded on subsequent requests, which limits reliance on old session authority.
@fig uc-access|diagrams/06-uc-access.png|Identity and administrative use cases

At least one enabled administrator must remain. The last-administrator guard is an operational control against losing access to staff administration. It is distinct from authentication: a valid session still requires a currently enabled account and a role permitted for the requested action.
## Domain invariants and representative scenarios
The stock invariant combines arithmetic, bounds and attribution. The accepted after quantity equals the locked before quantity plus the derived delta. Both the balance and the movement record are written within the transaction. The quantity lies between zero and one billion. Product policy also requires safety stock to be non-negative and no greater than the reorder threshold. An invalid operation must leave the prior stock history unchanged.
@equation balance|q_after = q_before + delta; 0 <= q_after <= 1,000,000,000

Consider a product with quantity seven and reorder threshold five. Dispatching two produces quantity five and a LOW episode because equality is included. Dispatching the remaining five changes severity to OUT. Acknowledging that episode records review but leaves quantity zero. Receiving eight later resolves the shortage and creates RESTOCKED. A count of three then derives a negative delta of five from the locked quantity eight; it is not interpreted as adding three.

A retry requires a different interpretation. If the request with a particular actor and key has already recorded the count of three, sending the same normalized intention must return the earlier record. Sending a count of four with that key conflicts. The concept of one intention per key therefore connects the business operation to the concurrency and retry design developed in Chapter 3.
## Chapter summary
The analysis identifies three linked objects: the present product balance, the accepted history that explains it and the warning episodes that interpret policy transitions. Human review is a separate fact. The following chapter turns these distinctions into requirements and acceptance conditions, so that the design can be evaluated against explicit behavior rather than against the visual appearance of a dashboard alone.
