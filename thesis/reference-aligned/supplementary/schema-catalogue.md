# Supplementary schema catalogue

Initial V1 excerpts retained from the expanded manuscript. These are not the complete V1–V8 schema. See the thesis migration summary and backend/src/main/resources/db/migration/ for extensions.

## Initial V1 users fields and constraints

Field | SQL type | Nullable | Constraint | Purpose
--- | --- | --- | --- | ---
id | BIGINT | No | Primary key | Record identifier
username | VARCHAR(80) | No | Unique | Sign-in identity
display_name | VARCHAR(100) | No | Column mapping | Human-readable staff name
password_hash | VARCHAR(100) | No | Column mapping | Stored password hash
role | VARCHAR(20) | No | Column mapping | Fixed ADMIN MANAGER or CLERK value
enabled | BOOLEAN | No | Column mapping | Current access flag
created_at | TIMESTAMP(6) | No | Column mapping | Server creation timestamp

## Initial V1 categories fields and constraints

Field | SQL type | Nullable | Constraint | Purpose
--- | --- | --- | --- | ---
id | BIGINT | No | Primary key | Record identifier
name | VARCHAR(100) | No | Unique | Descriptive name
description | VARCHAR(500) | Yes | Column mapping | Optional descriptive text
active | BOOLEAN | No | Column mapping | Available catalogue or reference record

## Initial V1 suppliers fields and constraints

Field | SQL type | Nullable | Constraint | Purpose
--- | --- | --- | --- | ---
id | BIGINT | No | Primary key | Record identifier
name | VARCHAR(120) | No | Column mapping | Descriptive name
contact_name | VARCHAR(120) | Yes | Column mapping | Supplier contact person
email | VARCHAR(120) | Yes | Column mapping | Supplier contact address
phone | VARCHAR(40) | Yes | Column mapping | Supplier telephone text
active | BOOLEAN | No | Column mapping | Available catalogue or reference record

## Initial V1 products fields and constraints

Field | SQL type | Nullable | Constraint | Purpose
--- | --- | --- | --- | ---
id | BIGINT | No | Primary key | Record identifier
sku | VARCHAR(64) | No | Unique | Unique required product identity
barcode | VARCHAR(64) | Yes | Unique | Optional unique scanned identity
name | VARCHAR(180) | No | Column mapping | Descriptive name
unit | VARCHAR(40) | No | Column mapping | Label for integer quantity
price | DECIMAL(12,2) | No | Check constraint | Current unit price not historical cost
quantity | BIGINT | No | Check constraint | Bounded current product balance
safety_stock | BIGINT | No | Check constraint | Urgency policy within the reorder level
reorder_threshold | BIGINT | No | Check constraint | Positive low-stock boundary including equality
category_id | BIGINT | Yes | Foreign key | Optional category reference
supplier_id | BIGINT | Yes | Foreign key | Optional supplier reference
active | BOOLEAN | No | Column mapping | Available catalogue or reference record
version | BIGINT | No | Column mapping | JPA entity version
updated_at | TIMESTAMP(6) | No | Column mapping | Latest product update time

## Initial V1 inventory_transactions fields and constraints

Field | SQL type | Nullable | Constraint | Purpose
--- | --- | --- | --- | ---
id | BIGINT | No | Primary key | Record identifier
product_id | BIGINT | No | Foreign key | Stock-bearing product reference
actor_id | BIGINT | No | Foreign key, Composite unique | Authenticated movement actor
type | VARCHAR(20) | No | Column mapping | Stock movement type
delta | BIGINT | No | Column mapping | Accepted signed stock effect
quantity_before | BIGINT | No | Column mapping | Locked balance before the operation
quantity_after | BIGINT | No | Column mapping | Accepted balance after the operation
reason | VARCHAR(300) | No | Column mapping | Required explanation of the stock intention
idempotency_key | VARCHAR(80) | No | Composite unique | Actor-scoped request intention key
created_at | TIMESTAMP(6) | No | Column mapping | Server creation timestamp

## Initial V1 warnings fields and constraints

Field | SQL type | Nullable | Constraint | Purpose
--- | --- | --- | --- | ---
id | BIGINT | No | Primary key | Record identifier
product_id | BIGINT | No | Foreign key | Stock-bearing product reference
type | VARCHAR(20) | No | Column mapping | Warning type
state | VARCHAR(20) | No | Column mapping | OPEN or RESOLVED episode lifecycle
observed_quantity | BIGINT | No | Column mapping | Quantity context of the warning episode
threshold | BIGINT | No | Column mapping | Policy context of the warning episode
created_at | TIMESTAMP(6) | No | Column mapping | Server creation timestamp
expires_at | TIMESTAMP(6) | No | Column mapping | Stored recovery visibility boundary
acknowledged_by | BIGINT | Yes | Foreign key | Optional first reviewer reference
acknowledged_at | TIMESTAMP(6) | Yes | Column mapping | Optional first review timestamp

## Initial V1 app_settings fields and constraints

Field | SQL type | Nullable | Constraint | Purpose
--- | --- | --- | --- | ---
setting_key | VARCHAR(80) | No | Primary key | Preference identity
setting_value | VARCHAR(240) | No | Column mapping | Display preference value

## Initial V1 cache_revision fields and constraints

Field | SQL type | Nullable | Constraint | Purpose
--- | --- | --- | --- | ---
id | BIGINT | No | Primary key | Record identifier
revision | BIGINT | No | Column mapping | Durable cache namespace counter
