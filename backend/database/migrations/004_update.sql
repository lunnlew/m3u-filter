CREATE TABLE IF NOT EXISTS group_mappings (
    channel_name TEXT NOT NULL,
    custom_group TEXT NOT NULL,
    rule_set_id INTEGER,
    PRIMARY KEY (channel_name, rule_set_id),
    FOREIGN KEY (rule_set_id) REFERENCES filter_rule_sets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS group_mapping_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    rule_set_id NUMERIC
);

CREATE TABLE IF NOT EXISTS group_mapping_template_items (
    template_id INTEGER NOT NULL,
    channel_name TEXT NOT NULL,
    custom_group TEXT NOT NULL,
    PRIMARY KEY (template_id, channel_name),
    FOREIGN KEY (template_id) REFERENCES group_mapping_templates(id) ON DELETE CASCADE
);