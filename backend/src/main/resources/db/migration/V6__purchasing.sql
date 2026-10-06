ALTER TABLE products ADD COLUMN target_stock BIGINT NOT NULL DEFAULT 1;
UPDATE products SET target_stock=LEAST(1000000000,GREATEST(reorder_threshold+1,reorder_threshold*2));
ALTER TABLE suppliers ADD COLUMN lead_time_days INT NOT NULL DEFAULT 3;
CREATE TABLE purchase_orders (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, supplier_id BIGINT NOT NULL, created_by BIGINT NOT NULL,
 state VARCHAR(20) NOT NULL, reason VARCHAR(300) NOT NULL, review_note VARCHAR(300),
 reviewed_by BIGINT, warning_id BIGINT, created_at TIMESTAMP(6) NOT NULL, updated_at TIMESTAMP(6) NOT NULL,
 CONSTRAINT fk_po_supplier FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
 CONSTRAINT fk_po_creator FOREIGN KEY(created_by) REFERENCES users(id),
 CONSTRAINT fk_po_reviewer FOREIGN KEY(reviewed_by) REFERENCES users(id),
 CONSTRAINT fk_po_warning FOREIGN KEY(warning_id) REFERENCES warnings(id)
);
CREATE TABLE purchase_lines (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, order_id BIGINT NOT NULL, product_id BIGINT NOT NULL,
 quantity BIGINT NOT NULL, received BIGINT NOT NULL DEFAULT 0,
 CONSTRAINT fk_po_line_order FOREIGN KEY(order_id) REFERENCES purchase_orders(id),
 CONSTRAINT fk_po_line_product FOREIGN KEY(product_id) REFERENCES products(id),
 CONSTRAINT uk_po_line_product UNIQUE(order_id,product_id),
 CONSTRAINT ck_po_line_quantity CHECK(quantity>0 AND received BETWEEN 0 AND quantity)
);
CREATE TABLE purchase_receipts (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, order_id BIGINT NOT NULL, line_id BIGINT NOT NULL,
 transaction_id BIGINT NOT NULL, actor_id BIGINT NOT NULL, request_key VARCHAR(80) NOT NULL,
 payload VARCHAR(600) NOT NULL, created_at TIMESTAMP(6) NOT NULL,
 CONSTRAINT fk_receipt_order FOREIGN KEY(order_id) REFERENCES purchase_orders(id),
 CONSTRAINT fk_receipt_line FOREIGN KEY(line_id) REFERENCES purchase_lines(id),
 CONSTRAINT fk_receipt_tx FOREIGN KEY(transaction_id) REFERENCES inventory_transactions(id),
 CONSTRAINT fk_receipt_actor FOREIGN KEY(actor_id) REFERENCES users(id),
 CONSTRAINT uk_receipt_request UNIQUE(actor_id,request_key)
);
CREATE TABLE purchase_actions (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, order_id BIGINT NOT NULL, actor_id BIGINT NOT NULL,
 action VARCHAR(30) NOT NULL, note VARCHAR(300) NOT NULL, created_at TIMESTAMP(6) NOT NULL,
 CONSTRAINT fk_po_action_order FOREIGN KEY(order_id) REFERENCES purchase_orders(id),
 CONSTRAINT fk_po_action_actor FOREIGN KEY(actor_id) REFERENCES users(id)
);
