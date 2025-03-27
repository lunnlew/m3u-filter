--
-- File generated with SQLiteStudio v3.4.4 on 周二 3月 11 14:02:21 2025
--
-- Text encoding used: UTF-8
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

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

INSERT INTO epg_sources (
                            id,
                            name,
                            url,
                            last_update,
                            active,
                            sync_interval,
                            default_language
                        )
                        VALUES (
                            1,
                            '节目总表',
                            'http://epg.51zmt.top:8000/e.xml',
                            '2025-03-11T14:00:46.456765',
                            1,
                            6,
                            'en'
                        );

INSERT INTO epg_sources (
                            id,
                            name,
                            url,
                            last_update,
                            active,
                            sync_interval,
                            default_language
                        )
                        VALUES (
                            2,
                            '央视及各省卫视',
                            'http://epg.51zmt.top:8000/cc.xml',
                            '2025-03-11T14:00:47.017079',
                            1,
                            6,
                            'en'
                        );

INSERT INTO epg_sources (
                            id,
                            name,
                            url,
                            last_update,
                            active,
                            sync_interval,
                            default_language
                        )
                        VALUES (
                            3,
                            '地方及数字付费',
                            'http://epg.51zmt.top:8000/difang.xml',
                            '2025-03-11T14:00:50.105076',
                            1,
                            6,
                            'en'
                        );

INSERT INTO epg_sources (
                            id,
                            name,
                            url,
                            last_update,
                            active,
                            sync_interval,
                            default_language
                        )
                        VALUES (
                            4,
                            'epg.112114.xyz',
                            'https://epg.112114.xyz/pp.xml',
                            '2025-03-11T14:00:54.146018',
                            1,
                            6,
                            'en'
                        );

INSERT INTO epg_sources (
                            id,
                            name,
                            url,
                            last_update,
                            active,
                            sync_interval,
                            default_language
                        )
                        VALUES (
                            6,
                            '来自直播订阅识别',
                            'https://epg.iill.top/epg',
                            '2025-03-11T11:58:06.614623',
                            1,
                            6,
                            'zh'
                        );


-- Table: filter_rules
CREATE TABLE IF NOT EXISTS filter_rules (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    type           TEXT    NOT NULL
                           CHECK (type IN ('name', 'keyword', 'resolution', 'group', 'bitrate') ) 
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

INSERT INTO stream_sources (
                               id,
                               name,
                               url,
                               last_update,
                               type,
                               x_tvg_url,
                               catchup,
                               catchup_source,
                               active,
                               sync_interval
                           )
                           VALUES (
                               1,
                               'vbskycn',
                               'https://raw.githubusercontent.com/vbskycn/iptv/master/tv/iptv4.txt',
                               '2025-03-10 10:22:07',
                               'txt',
                               NULL,
                               NULL,
                               NULL,
                               1,
                               6
                           );

INSERT INTO stream_sources (
                               id,
                               name,
                               url,
                               last_update,
                               type,
                               x_tvg_url,
                               catchup,
                               catchup_source,
                               active,
                               sync_interval
                           )
                           VALUES (
                               2,
                               'YanG-1989-Gather.m3u「精简版」',
                               'https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u',
                               '2025-03-11 02:52:31',
                               'm3u',
                               'https://epg.iill.top/epg',
                               'append',
                               '?playseek=${(b)yyyyMMddHHmmss}-${(e)yyyyMMddHHmmss}',
                               1,
                               6
                           );

INSERT INTO stream_sources (
                               id,
                               name,
                               url,
                               last_update,
                               type,
                               x_tvg_url,
                               catchup,
                               catchup_source,
                               active,
                               sync_interval
                           )
                           VALUES (
                               3,
                               'YanG-1989-网络直播',
                               'https://tv.iill.top/m3u/Live',
                               '2025-03-10 10:54:26',
                               'm3u',
                               NULL,
                               NULL,
                               NULL,
                               1,
                               6
                           );

INSERT INTO stream_sources (
                               id,
                               name,
                               url,
                               last_update,
                               type,
                               x_tvg_url,
                               catchup,
                               catchup_source,
                               active,
                               sync_interval
                           )
                           VALUES (
                               4,
                               'YanG-1989-Gather.m3u「完整版」',
                               'https://tv.iill.top/m3u/Gather',
                               '2025-03-10 10:56:19',
                               'm3u',
                               NULL,
                               NULL,
                               NULL,
                               1,
                               6
                           );


-- Table: stream_tracks
CREATE TABLE IF NOT EXISTS stream_tracks (
    id                INTEGER   PRIMARY KEY AUTOINCREMENT,
    source_id         INTEGER   NOT NULL,
    name              TEXT      NOT NULL,
    url               TEXT      NOT NULL,
    group_title       TEXT,
    tvg_id            TEXT,
    tvg_name          TEXT,
    tvg_logo          TEXT,
    tvg_language      TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    catchup           TEXT,
    catchup_source    TEXT,
    last_test_time    TEXT,
    test_status       NUMERIC,
    test_latency      REAL,
    video_codec       TEXT,
    audio_codec       TEXT,
    resolution        TEXT,
    bitrate           NUMERIC,
    frame_rate        REAL,
    ping_time         REAL,
    speed_test_time   DATETIME,
    download_speed    FLOAT,
    speed_test_status INTEGER   DEFAULT 0,
    route_info        TEXT,
    FOREIGN KEY (
        source_id
    )
    REFERENCES stream_sources (id) ON DELETE CASCADE
);


-- Index: idx_channel_id
CREATE INDEX IF NOT EXISTS idx_channel_id ON epg_channels (
    channel_id
);


-- Index: idx_epg_channels_name
CREATE INDEX IF NOT EXISTS idx_epg_channels_name ON epg_channels (
    display_name
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


-- Index: idx_filter_rules_enabled
CREATE INDEX IF NOT EXISTS idx_filter_rules_enabled ON filter_rules (
    enabled
);


-- Index: idx_filter_rules_priority
CREATE INDEX IF NOT EXISTS idx_filter_rules_priority ON filter_rules (
    priority
);


-- Index: idx_program_channel
CREATE INDEX IF NOT EXISTS idx_program_channel ON epg_programs (
    channel_id
);


-- Index: idx_program_source
CREATE INDEX IF NOT EXISTS idx_program_source ON epg_programs (
    source_id
);


-- Index: idx_source_id
CREATE INDEX IF NOT EXISTS idx_source_id ON epg_channels (
    source_id
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


-- 创建filter_rules表
CREATE TABLE IF NOT EXISTS filter_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    pattern TEXT NOT NULL,
    action TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT TRUE,
    case_sensitive BOOLEAN DEFAULT FALSE,
    regex_mode BOOLEAN DEFAULT FALSE
);

-- 创建filter_rule_sets表
CREATE TABLE IF NOT EXISTS filter_rule_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    sync_interval INTEGER NOT NULL DEFAULT 6,
    logic_type TEXT NOT NULL DEFAULT 'AND' CHECK(logic_type IN ('AND', 'OR'))
);

CREATE TABLE IF NOT EXISTS filter_rule_set_children (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_set_id INTEGER NOT NULL,
    child_set_id INTEGER NOT NULL,
    FOREIGN KEY (parent_set_id) REFERENCES filter_rule_sets(id) ON DELETE CASCADE,
    FOREIGN KEY (child_set_id) REFERENCES filter_rule_sets(id) ON DELETE CASCADE
);

-- 创建filter_rule_set_mappings表
CREATE TABLE IF NOT EXISTS filter_rule_set_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_set_id INTEGER NOT NULL,
    rule_id INTEGER NOT NULL,
    FOREIGN KEY (rule_set_id) REFERENCES filter_rule_sets(id),
    FOREIGN KEY (rule_id) REFERENCES filter_rules(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_filter_rules_name ON filter_rules(name);
CREATE INDEX IF NOT EXISTS idx_filter_rule_sets_name ON filter_rule_sets(name);


CREATE TABLE IF NOT EXISTS stream_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    progress REAL DEFAULT 0,
    total_items INTEGER,
    processed_items INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    result TEXT
);

-- 创建排序模板表
CREATE TABLE IF NOT EXISTS sort_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    group_orders TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建排序模板表索引
CREATE INDEX IF NOT EXISTS idx_sort_templates_name ON sort_templates(name);