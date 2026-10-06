CREATE TABLE stock_reviews (
 id BIGINT PRIMARY KEY AUTO_INCREMENT, product_id BIGINT NOT NULL, batch_id BIGINT,
 kind VARCHAR(20) NOT NULL, state VARCHAR(20) NOT NULL, quantity BIGINT NOT NULL,
 snapshot_quantity BIGINT NOT NULL, snapshot_version BIGINT NOT NULL,
 reason VARCHAR(300) NOT NULL, review_note VARCHAR(300),
 created_by BIGINT NOT NULL, reviewed_by BIGINT, transaction_id BIGINT,
 created_at TIMESTAMP(6) NOT NULL, reviewed_at TIMESTAMP(6),
 CONSTRAINT fk_review_product FOREIGN KEY(product_id) REFERENCES products(id),
 CONSTRAINT fk_review_batch FOREIGN KEY(batch_id) REFERENCES inventory_batches(id),
 CONSTRAINT fk_review_creator FOREIGN KEY(created_by) REFERENCES users(id),
 CONSTRAINT fk_review_reviewer FOREIGN KEY(reviewed_by) REFERENCES users(id),
 CONSTRAINT fk_review_transaction FOREIGN KEY(transaction_id) REFERENCES inventory_transactions(id)
);
