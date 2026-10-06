# Inventory warning expansion

This upgrade extends the existing single-store application. Existing migrations remain immutable; new schema versions preserve inventory and warning history. Each feature is committed separately after its relevant checks.

Planned delivery sequence:

1. Warning handling: severity, confirmation, assignment, processing, append-only notes and recovery history.
2. Batch inventory: receipt dates, expiry dates, quarantine, FEFO/FIFO dispatch and durable batch allocations; migrate existing balances.
3. Expiry warnings: business-timezone date boundaries, scheduled refresh and configurable rules.
4. Slow-moving stock: distinct sales movements, configurable observation window and minimum quantity.
5. Purchasing: explainable replenishment, approval, partial receipt, cancellation and warning links.

Defaults: Asia/Shanghai; expiry date inclusive; near-expiry window 7 days; no-sales window 30 days; slow-stock minimum 10 units. Shortage warnings use sellable inventory. Confirmation, assignment and purchase creation never clear a rule condition. All data is demonstration data.

The existing thesis and its screenshots describe the earlier release; regenerating the thesis is a separate task.

## Batch upgrade

V3 preserves existing physical balances as undated `MIGRATED-{productId}` batches. Historical movements are retained; their batch allocation is unknown and is not fabricated. New movements carry durable signed allocations. Physical balances equal the sum of batch balances. Expired/quarantined batches cannot be dispatched, but remain physical stock until an explicit adjustment/disposal. Undated receipt batches are generated when no batch number is entered. Exact replay also checks receipt dates and batch identity. Product locking serializes batch changes and dispatch.

## Time rules and recovery

Expiry day remains sellable through the end of the configured business day. Near-expiry applies to valid, non-quarantined batches within the inclusive day window. Expired applies to physical batch remainder, including quarantined units; expiry never disposes inventory. V4 adds a unique active-rule key per product/batch/type. Cleared events retain handling history and recurrent events link to their predecessor.

Stock changes update warnings in the same MySQL transaction, so failed writes cannot leave partial rule results. Configuration commits before a full sweep. Date-based rules are rechecked every 30 seconds; failed products retry on the next sweep. `/warnings/refresh-status` exposes completion/failure counts; operators can force a sweep. This interval is a schedule, not a hard latency guarantee under arbitrary load. Redis remains a revision-keyed optional query cache; unchanged sweeps do not invalidate it.

## Slow-moving stock

V5 introduces `SALE` separately from ordinary `STOCK_OUT`. Earlier dispatches are not retroactively relabeled as sales. A slow-stock event requires at least the configured sellable minimum, a product age covering the whole observation window, and no `SALE` since the start of the observation window in the business timezone. Default: 30 days and 10 units. Fresh catalogue entries are not immediately marked slow. Other receipts, transfers and adjustments are not sales. This is an explainable inactivity rule, not demand forecasting.

## Purchasing

V6 supports multi-product drafts, submission, rejection/editing, approval, partial receipts, completion and cancellation of the remainder. Approval is manager/admin-only and receiving is clerk/admin-only. Approval may be performed by the creator if their role permits it; this is the chosen small-store default. Product locks in ID order serialize concurrent approvals and receipts. Each approval rechecks sellable stock plus approved/partial pending units against the trigger and target. Draft/submitted/rejected/cancelled units never inflate stock position. Receipt replay validates the whole payload and creates one batch/movement atomically. Cancelling a partially received order retains all receipt history and physical stock. Ordinary receipts remain available for opening balances and non-purchase transfers; supplier purchases should use approved purchase receipts. No payment or settlement is provided.
