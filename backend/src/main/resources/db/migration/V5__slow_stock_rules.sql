ALTER TABLE warning_policy ADD COLUMN slow_stock_days INT NOT NULL DEFAULT 30,
 ADD COLUMN slow_stock_minimum BIGINT NOT NULL DEFAULT 10;
ALTER TABLE products ADD COLUMN created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6);
UPDATE products SET created_at=COALESCE((SELECT MIN(t.created_at) FROM inventory_transactions t WHERE t.product_id=products.id),updated_at);
CREATE INDEX idx_tx_sales_time ON inventory_transactions(product_id,type,created_at);
