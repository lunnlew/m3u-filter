CREATE TABLE IF NOT EXISTS group_mappings (
    channel_name TEXT NOT NULL,
    custom_group TEXT NOT NULL,
    rule_set_id INTEGER,
    PRIMARY KEY (channel_name, rule_set_id),
    FOREIGN KEY (rule_set_id) REFERENCES filter_rule_sets(id) ON DELETE CASCADE
);