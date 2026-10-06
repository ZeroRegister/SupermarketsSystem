ALTER TABLE products ADD COLUMN sellable_quantity BIGINT NOT NULL DEFAULT 0;
UPDATE products SET sellable_quantity=quantity;
ALTER TABLE inventory_transactions ADD COLUMN request_metadata VARCHAR(500) NOT NULL DEFAULT '';
CREATE TABLE inventory_batches (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, product_id BIGINT NOT NULL,
 batch_number VARCHAR(80) NOT NULL, received_date DATE NOT NULL,
 production_date DATE NULL, expiry_date DATE NULL,
 quantity BIGINT NOT NULL, quarantined BOOLEAN NOT NULL DEFAULT FALSE,
 version BIGINT NOT NULL DEFAULT 0,
 CONSTRAINT fk_batch_product FOREIGN KEY(product_id) REFERENCES products(id),
 CONSTRAINT uk_batch_product_number UNIQUE(product_id,batch_number),
 CONSTRAINT ck_batch_quantity CHECK(quantity BETWEEN 0 AND 1000000000)
);
CREATE INDEX idx_batch_product_expiry ON inventory_batches(product_id,expiry_date);
INSERT INTO inventory_batches(product_id,batch_number,received_date,quantity)
 SELECT id,CONCAT('MIGRATED-',id),DATE(updated_at),quantity FROM products WHERE quantity>0;
CREATE TABLE batch_allocations (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, transaction_id BIGINT NOT NULL, batch_id BIGINT NOT NULL,
 delta BIGINT NOT NULL,
 CONSTRAINT fk_allocation_transaction FOREIGN KEY(transaction_id) REFERENCES inventory_transactions(id),
 CONSTRAINT fk_allocation_batch FOREIGN KEY(batch_id) REFERENCES inventory_batches(id)
);
CREATE INDEX idx_allocation_batch ON batch_allocations(batch_id,id);
CREATE TABLE batch_actions (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, batch_id BIGINT NOT NULL, actor_id BIGINT NOT NULL,
 quarantined BOOLEAN NOT NULL, reason VARCHAR(300) NOT NULL, created_at TIMESTAMP(6) NOT NULL,
 CONSTRAINT fk_batch_action_batch FOREIGN KEY(batch_id) REFERENCES inventory_batches(id),
 CONSTRAINT fk_batch_action_actor FOREIGN KEY(actor_id) REFERENCES users(id)
);
