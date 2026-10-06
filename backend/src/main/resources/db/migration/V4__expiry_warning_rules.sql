ALTER TABLE warnings
 ADD COLUMN batch_id BIGINT NULL,
 ADD CONSTRAINT fk_warning_batch FOREIGN KEY(batch_id) REFERENCES inventory_batches(id),
 ADD COLUMN active_rule_key VARCHAR(150) GENERATED ALWAYS AS
 (CASE WHEN state='OPEN' THEN CONCAT(product_id,':',COALESCE(batch_id,0),':',type) ELSE NULL END) STORED,
 ADD CONSTRAINT uk_active_warning_rule UNIQUE(active_rule_key);
CREATE TABLE warning_policy (
 id BIGINT PRIMARY KEY, near_expiry_days INT NOT NULL,
 business_timezone VARCHAR(80) NOT NULL, version BIGINT NOT NULL DEFAULT 0
);
INSERT INTO warning_policy(id,near_expiry_days,business_timezone) VALUES(1,7,'Asia/Shanghai');
