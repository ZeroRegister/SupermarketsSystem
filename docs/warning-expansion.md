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
