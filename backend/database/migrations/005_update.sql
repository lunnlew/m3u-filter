ALTER TABLE stream_tracks ADD COLUMN buffer_health REAL DEFAULT 0.0;
ALTER TABLE stream_tracks ADD COLUMN stability_score REAL DEFAULT 0.0;
ALTER TABLE stream_tracks ADD COLUMN quality_score REAL DEFAULT 0.0;