--
-- File generated with SQLiteStudio v3.4.4 on 周三 4月 16 22:24:16 2025
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: blocked_domains
CREATE TABLE IF NOT EXISTS blocked_domains (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    domain            TEXT    UNIQUE
                              NOT NULL,
    failure_count     INTEGER DEFAULT 0,
    last_failure_time TEXT,
    created_at        TEXT    DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT    DEFAULT CURRENT_TIMESTAMP,
    last_errors       TEXT
);


-- Index: sqlite_autoindex_blocked_domains_1
CREATE UNIQUE INDEX IF NOT EXISTS sqlite_autoindex_blocked_domains_1 ON blocked_domains (
    domain COLLATE BINARY
);


-- Table: db_version
CREATE TABLE IF NOT EXISTS db_version (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT    NOT NULL
);

-- Table: default_channel_logos
CREATE TABLE IF NOT EXISTS default_channel_logos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT    NOT NULL,
    logo_url     TEXT    NOT NULL,
    priority     INTEGER DEFAULT 0,
    UNIQUE (
        channel_name
    )
);


-- Index: sqlite_autoindex_default_channel_logos_1
CREATE UNIQUE INDEX IF NOT EXISTS sqlite_autoindex_default_channel_logos_1 ON default_channel_logos (
    channel_name COLLATE BINARY
);


-- Table: epg_channels
CREATE TABLE IF NOT EXISTS epg_channels (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id      TEXT    NOT NULL,
    display_name    TEXT    NOT NULL,
    language        TEXT    NOT NULL,
    category        TEXT,
    logo_url        TEXT,
    local_logo_path TEXT,
    source_id       INTEGER NOT NULL,
    FOREIGN KEY (
        source_id
    )
    REFERENCES epg_sources (id) ON DELETE CASCADE,
    UNIQUE (
        display_name,
        channel_id,
        source_id
    )
);


-- Index: idx_channel_id
CREATE INDEX IF NOT EXISTS idx_channel_id ON epg_channels (
    channel_id
);


-- Index: idx_epg_channels_name
CREATE INDEX IF NOT EXISTS idx_epg_channels_name ON epg_channels (
    display_name
);


-- Index: idx_source_id
CREATE INDEX IF NOT EXISTS idx_source_id ON epg_channels (
    source_id
);


-- Index: sqlite_autoindex_epg_channels_1
CREATE UNIQUE INDEX IF NOT EXISTS sqlite_autoindex_epg_channels_1 ON epg_channels (
    display_name COLLATE BINARY,
    channel_id COLLATE BINARY,
    source_id COLLATE BINARY
);



-- Table: epg_programs
CREATE TABLE IF NOT EXISTS epg_programs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id  TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    start_time  TEXT    NOT NULL,
    end_time    TEXT    NOT NULL,
    description TEXT,
    language    TEXT    NOT NULL,
    category    TEXT,
    source_id   INTEGER NOT NULL,
    FOREIGN KEY (
        source_id
    )
    REFERENCES epg_sources (id) ON DELETE CASCADE,
    FOREIGN KEY (
        channel_id,
        source_id
    )
    REFERENCES epg_channels (channel_id,
    source_id) ON DELETE CASCADE,
    UNIQUE (
        title,
        start_time,
        channel_id,
        source_id
    )
);


-- Index: idx_epg_programs_channel
CREATE INDEX IF NOT EXISTS idx_epg_programs_channel ON epg_programs (
    channel_id,
    source_id
);


-- Index: idx_epg_programs_time
CREATE INDEX IF NOT EXISTS idx_epg_programs_time ON epg_programs (
    start_time,
    end_time
);


-- Index: idx_program_channel
CREATE INDEX IF NOT EXISTS idx_program_channel ON epg_programs (
    channel_id
);


-- Index: idx_program_source
CREATE INDEX IF NOT EXISTS idx_program_source ON epg_programs (
    source_id
);


-- Index: sqlite_autoindex_epg_programs_1
CREATE UNIQUE INDEX IF NOT EXISTS sqlite_autoindex_epg_programs_1 ON epg_programs (
    title COLLATE BINARY,
    start_time COLLATE BINARY,
    channel_id COLLATE BINARY,
    source_id COLLATE BINARY
);


-- Table: epg_sources
CREATE TABLE IF NOT EXISTS epg_sources (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT    NOT NULL,
    url              TEXT    NOT NULL
                             UNIQUE,
    last_update      TEXT,
    active           BOOLEAN NOT NULL
                             DEFAULT 1,
    sync_interval    INTEGER NOT NULL
                             DEFAULT 6,
    default_language TEXT    NOT NULL
                             DEFAULT 'en'
);


-- Index: sqlite_autoindex_epg_sources_1
CREATE UNIQUE INDEX IF NOT EXISTS sqlite_autoindex_epg_sources_1 ON epg_sources (
    url COLLATE BINARY
);


-- Table: filter_rule_set_children
CREATE TABLE IF NOT EXISTS filter_rule_set_children (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_set_id INTEGER NOT NULL,
    child_set_id  INTEGER NOT NULL,
    FOREIGN KEY (
        parent_set_id
    )
    REFERENCES filter_rule_sets (id) ON DELETE CASCADE,
    FOREIGN KEY (
        child_set_id
    )
    REFERENCES filter_rule_sets (id) ON DELETE CASCADE
);


-- Table: filter_rule_set_mappings
CREATE TABLE IF NOT EXISTS filter_rule_set_mappings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_set_id INTEGER NOT NULL,
    rule_id     INTEGER NOT NULL,
    FOREIGN KEY (
        rule_set_id
    )
    REFERENCES filter_rule_sets (id),
    FOREIGN KEY (
        rule_id
    )
    REFERENCES filter_rules (id) 
);


-- Table: filter_rule_sets
CREATE TABLE IF NOT EXISTS filter_rule_sets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    description   TEXT,
    enabled       BOOLEAN DEFAULT TRUE,
    logic_type    TEXT    DEFAULT [AND],
    sync_interval INTEGER DEFAULT (6) 
);


-- Index: idx_filter_rule_sets_name
CREATE INDEX IF NOT EXISTS idx_filter_rule_sets_name ON filter_rule_sets (
    name
);


-- Table: filter_rules
CREATE TABLE IF NOT EXISTS filter_rules (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    type           TEXT    NOT NULL
                           CHECK (type IN ('name', 'keyword', 'resolution', 'group', 'bitrate', 'status') ) 
                           DEFAULT 'name',
    pattern        TEXT    NOT NULL,
    action         TEXT    NOT NULL
                           CHECK (action IN ('include', 'exclude') ) 
                           DEFAULT 'exclude',
    priority       INTEGER NOT NULL
                           DEFAULT 0,
    enabled        BOOLEAN NOT NULL
                           DEFAULT 1,
    case_sensitive BOOLEAN NOT NULL
                           DEFAULT 0,
    regex_mode     BOOLEAN NOT NULL
                           DEFAULT 0,
    min_value      INTEGER,
    max_value      INTEGER,
    created_at     TEXT    NOT NULL
                           DEFAULT CURRENT_TIMESTAMP,
    updated_at     TEXT    NOT NULL
                           DEFAULT CURRENT_TIMESTAMP,
    description    TEXT
);


-- Index: idx_filter_rules_enabled
CREATE INDEX IF NOT EXISTS idx_filter_rules_enabled ON filter_rules (
    enabled
);


-- Index: idx_filter_rules_name
CREATE INDEX IF NOT EXISTS idx_filter_rules_name ON filter_rules (
    name
);


-- Index: idx_filter_rules_priority
CREATE INDEX IF NOT EXISTS idx_filter_rules_priority ON filter_rules (
    priority
);


-- Table: group_mapping_template_items
CREATE TABLE IF NOT EXISTS group_mapping_template_items (
    template_id  INTEGER NOT NULL,
    channel_name TEXT    NOT NULL,
    custom_group TEXT    NOT NULL,
    display_name TEXT,
    PRIMARY KEY (
        template_id,
        channel_name
    ),
    FOREIGN KEY (
        template_id
    )
    REFERENCES group_mapping_templates (id) ON DELETE CASCADE
);


-- Index: sqlite_autoindex_group_mapping_template_items_1
CREATE UNIQUE INDEX IF NOT EXISTS sqlite_autoindex_group_mapping_template_items_1 ON group_mapping_template_items (
    template_id COLLATE BINARY,
    channel_name COLLATE BINARY
);


-- Table: group_mapping_templates
CREATE TABLE IF NOT EXISTS group_mapping_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    description TEXT,
    rule_set_id NUMERIC
);


-- Table: group_mappings
CREATE TABLE IF NOT EXISTS group_mappings (
    channel_name TEXT    NOT NULL,
    custom_group TEXT    NOT NULL,
    display_name TEXT,
    rule_set_id  INTEGER,
    PRIMARY KEY (
        channel_name,
        rule_set_id
    ),
    FOREIGN KEY (
        rule_set_id
    )
    REFERENCES filter_rule_sets (id) ON DELETE CASCADE
);


-- Index: sqlite_autoindex_group_mappings_1
CREATE UNIQUE INDEX IF NOT EXISTS sqlite_autoindex_group_mappings_1 ON group_mappings (
    channel_name COLLATE BINARY,
    rule_set_id COLLATE BINARY
);


-- Table: invalid_urls
CREATE TABLE IF NOT EXISTS invalid_urls (
    url                TEXT     PRIMARY KEY,
    first_failure_time DATETIME,
    last_failure_time  DATETIME,
    failure_count      INTEGER  DEFAULT 1,
    source_ids         TEXT,
    last_success_time  DATETIME,
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- Index: sqlite_autoindex_invalid_urls_1
CREATE UNIQUE INDEX IF NOT EXISTS sqlite_autoindex_invalid_urls_1 ON invalid_urls (
    url COLLATE BINARY
);



-- Table: proxy_config
CREATE TABLE IF NOT EXISTS proxy_config (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    enabled    BOOLEAN DEFAULT 0,
    proxy_type TEXT    DEFAULT 'http',
    host       TEXT,
    port       INTEGER,
    username   TEXT,
    password   TEXT
);


-- Table: rule_test_tasks
CREATE TABLE IF NOT EXISTS rule_test_tasks (
    task_id         INTEGER   PRIMARY KEY,
    rule_set_id     INTEGER   NOT NULL,
    status          TEXT      NOT NULL
                              DEFAULT 'pending',
    total_items     INTEGER   NOT NULL
                              DEFAULT 0,
    processed_items INTEGER   NOT NULL
                              DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP,
    FOREIGN KEY (
        task_id
    )
    REFERENCES stream_tasks (id),
    FOREIGN KEY (
        rule_set_id
    )
    REFERENCES filter_rule_sets (id) 
);


-- Table: sort_templates
CREATE TABLE IF NOT EXISTS sort_templates (
    id           INTEGER  PRIMARY KEY AUTOINCREMENT,
    name         TEXT     NOT NULL,
    description  TEXT,
    group_orders TEXT     NOT NULL,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- Table: stream_sources
CREATE TABLE IF NOT EXISTS stream_sources (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    url            TEXT    NOT NULL
                           UNIQUE,
    last_update    TEXT,
    type           TEXT,
    x_tvg_url      TEXT,
    catchup        TEXT,
    catchup_source TEXT,
    active         BOOLEAN NOT NULL
                           DEFAULT 1,
    sync_interval  INTEGER NOT NULL
                           DEFAULT 6
);


-- Index: sqlite_autoindex_stream_sources_1
CREATE UNIQUE INDEX IF NOT EXISTS sqlite_autoindex_stream_sources_1 ON stream_sources (
    url COLLATE BINARY
);


-- Table: stream_tasks
CREATE TABLE IF NOT EXISTS stream_tasks (
    id              INTEGER  PRIMARY KEY AUTOINCREMENT,
    task_type       TEXT     NOT NULL,
    status          TEXT     NOT NULL
                             CHECK (status IN ('pending', 'running', 'completed', 'failed') ),
    progress        REAL     DEFAULT 0,
    total_items     INTEGER,
    processed_items INTEGER  DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    result          TEXT
);



-- Table: stream_tracks
CREATE TABLE IF NOT EXISTS stream_tracks (
    id                  INTEGER   PRIMARY KEY AUTOINCREMENT,
    source_id           INTEGER   NOT NULL,
    name                TEXT      NOT NULL,
    url                 TEXT      NOT NULL,
    group_title         TEXT,
    tvg_id              TEXT,
    tvg_name            TEXT,
    tvg_logo            TEXT,
    tvg_language        TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    catchup             TEXT,
    catchup_source      TEXT,
    last_test_time      TEXT,
    test_status         NUMERIC,
    test_latency        REAL,
    video_codec         TEXT,
    audio_codec         TEXT,
    resolution          TEXT,
    bitrate             NUMERIC,
    frame_rate          REAL,
    ping_time           REAL,
    speed_test_time     DATETIME,
    download_speed      FLOAT,
    speed_test_status   INTEGER   DEFAULT 0,
    route_info          TEXT,
    probe_failure_count INTEGER   DEFAULT 0,
    last_failure_time   TEXT,
    buffer_health       REAL      DEFAULT 0.0,
    stability_score     REAL      DEFAULT 0.0,
    quality_score       REAL      DEFAULT 0.0,
    last_success_time   DATETIME,
    FOREIGN KEY (
        source_id
    )
    REFERENCES stream_sources (id) ON DELETE CASCADE
);


-- Index: idx_stream_track_group_title
CREATE INDEX IF NOT EXISTS idx_stream_track_group_title ON stream_tracks (
    group_title
);


-- Index: idx_stream_track_name
CREATE INDEX IF NOT EXISTS idx_stream_track_name ON stream_tracks (
    name
);


-- Index: idx_stream_track_source_id
CREATE INDEX IF NOT EXISTS idx_stream_track_source_id ON stream_tracks (
    source_id
);


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
