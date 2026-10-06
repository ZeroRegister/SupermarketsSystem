ALTER TABLE stock_reviews ADD COLUMN request_key VARCHAR(80) NULL;
UPDATE stock_reviews SET request_key=CONCAT('migrated-',id);
ALTER TABLE stock_reviews MODIFY request_key VARCHAR(80) NOT NULL,
 ADD CONSTRAINT uk_review_request UNIQUE(created_by,request_key);
INSERT INTO warning_actions(warning_id,actor_id,action,note,created_at)
 SELECT id,acknowledged_by,'CONFIRM','Confirmation retained from the previous release',acknowledged_at
 FROM warnings w WHERE acknowledged_at IS NOT NULL
 AND NOT EXISTS (SELECT 1 FROM warning_actions a WHERE a.warning_id=w.id AND a.action='CONFIRM');
