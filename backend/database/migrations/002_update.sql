PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

ALTER TABLE stream_tracks ADD COLUMN probe_failure_count INTEGER DEFAULT 0;
ALTER TABLE stream_tracks ADD COLUMN last_failure_time TEXT;

COMMIT;
PRAGMA foreign_keys = on;