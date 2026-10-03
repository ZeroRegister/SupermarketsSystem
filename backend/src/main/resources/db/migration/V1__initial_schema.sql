CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT, username VARCHAR(80) NOT NULL UNIQUE,
  display_name VARCHAR(100) NOT NULL, password_hash VARCHAR(100) NOT NULL,
  role VARCHAR(20) NOT NULL, enabled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
);
CREATE TABLE categories (
  id BIGINT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100) NOT NULL UNIQUE,
  description VARCHAR(500), active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE suppliers (
  id BIGINT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(120) NOT NULL,
  contact_name VARCHAR(120), email VARCHAR(120), phone VARCHAR(40), active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE products (
  id BIGINT PRIMARY KEY AUTO_INCREMENT, sku VARCHAR(64) NOT NULL UNIQUE, barcode VARCHAR(64) UNIQUE,
  name VARCHAR(180) NOT NULL, unit VARCHAR(40) NOT NULL DEFAULT 'pcs', price DECIMAL(12,2) NOT NULL DEFAULT 0,
  quantity BIGINT NOT NULL DEFAULT 0, safety_stock BIGINT NOT NULL DEFAULT 0,
  reorder_threshold BIGINT NOT NULL DEFAULT 0, category_id BIGINT, supplier_id BIGINT,
  active BOOLEAN NOT NULL DEFAULT TRUE, version BIGINT NOT NULL DEFAULT 0,
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_product_category FOREIGN KEY(category_id) REFERENCES categories(id),
  CONSTRAINT fk_product_supplier FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
  CONSTRAINT ck_product_qty CHECK(quantity BETWEEN 0 AND 1000000000),
  CONSTRAINT ck_product_threshold CHECK(safety_stock BETWEEN 0 AND reorder_threshold AND reorder_threshold <= 1000000000),
  CONSTRAINT ck_product_price CHECK(price >= 0)
);
CREATE INDEX idx_product_name ON products(name);
CREATE INDEX idx_product_category ON products(category_id);
CREATE INDEX idx_product_quantity ON products(quantity);
CREATE TABLE inventory_transactions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT, product_id BIGINT NOT NULL, actor_id BIGINT NOT NULL,
  type VARCHAR(20) NOT NULL, delta BIGINT NOT NULL, quantity_before BIGINT NOT NULL, quantity_after BIGINT NOT NULL,
  reason VARCHAR(300) NOT NULL, idempotency_key VARCHAR(80) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_tx_product FOREIGN KEY(product_id) REFERENCES products(id),
  CONSTRAINT fk_tx_actor FOREIGN KEY(actor_id) REFERENCES users(id),
  CONSTRAINT uk_tx_actor_key UNIQUE(actor_id,idempotency_key)
);
CREATE INDEX idx_tx_product_time ON inventory_transactions(product_id,created_at);
CREATE TABLE warnings (
  id BIGINT PRIMARY KEY AUTO_INCREMENT, product_id BIGINT NOT NULL, type VARCHAR(20) NOT NULL,
  state VARCHAR(20) NOT NULL DEFAULT 'OPEN', observed_quantity BIGINT NOT NULL, threshold BIGINT NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), expires_at TIMESTAMP(6) NOT NULL,
  acknowledged_by BIGINT, acknowledged_at TIMESTAMP(6),
  CONSTRAINT fk_warning_product FOREIGN KEY(product_id) REFERENCES products(id),
  CONSTRAINT fk_warning_ack FOREIGN KEY(acknowledged_by) REFERENCES users(id)
);
CREATE INDEX idx_warning_state_time ON warnings(state,created_at);
CREATE TABLE app_settings (setting_key VARCHAR(80) PRIMARY KEY, setting_value VARCHAR(240) NOT NULL);
CREATE TABLE cache_revision (id BIGINT PRIMARY KEY, revision BIGINT NOT NULL);
INSERT INTO cache_revision(id,revision) VALUES(1,0);
INSERT INTO app_settings(setting_key,setting_value) VALUES('currency','USD'),('business_name','Neighborhood Market');
