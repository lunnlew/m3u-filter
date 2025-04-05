CREATE TABLE IF NOT EXISTS rule_test_tasks (
    task_id INTEGER PRIMARY KEY,
    rule_set_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_items INTEGER NOT NULL DEFAULT 0,
    processed_items INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES stream_tasks(id),
    FOREIGN KEY (rule_set_id) REFERENCES filter_rule_sets(id)
);