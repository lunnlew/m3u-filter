-- 创建失效URL跟踪表
CREATE TABLE IF NOT EXISTS invalid_urls (
    url TEXT PRIMARY KEY,
    first_failure_time DATETIME,
    last_failure_time DATETIME,
    failure_count INTEGER DEFAULT 1,
    source_ids TEXT,
    last_success_time DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 在stream_tracks表中添加新字段
ALTER TABLE stream_tracks ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE stream_tracks ADD COLUMN last_success_time DATETIME;