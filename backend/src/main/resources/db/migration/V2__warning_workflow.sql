ALTER TABLE warnings
  ADD COLUMN review_stage VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  ADD COLUMN assigned_to BIGINT NULL,
  ADD COLUMN recovered_at TIMESTAMP(6) NULL,
  ADD COLUMN previous_id BIGINT NULL,
  ADD CONSTRAINT fk_warning_assignee FOREIGN KEY(assigned_to) REFERENCES users(id),
  ADD CONSTRAINT fk_warning_previous FOREIGN KEY(previous_id) REFERENCES warnings(id);
UPDATE warnings SET review_stage='CONFIRMED' WHERE acknowledged_by IS NOT NULL AND state='OPEN';
UPDATE warnings SET review_stage='RECOVERED' WHERE state='RESOLVED';
CREATE TABLE warning_actions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  warning_id BIGINT NOT NULL,
  actor_id BIGINT NULL,
  action VARCHAR(30) NOT NULL,
  note VARCHAR(1000) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL,
  CONSTRAINT fk_warning_action_event FOREIGN KEY(warning_id) REFERENCES warnings(id),
  CONSTRAINT fk_warning_action_actor FOREIGN KEY(actor_id) REFERENCES users(id)
);
CREATE INDEX idx_warning_action_time ON warning_actions(warning_id,created_at);
