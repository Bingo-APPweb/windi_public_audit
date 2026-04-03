-- W-VD-CUT-001 — Initial Schema
-- WINDI Video Cut Engine
-- Liga IA+H · Kempten, Bavaria · 2026

-- Video Projects (master record)
CREATE TABLE IF NOT EXISTS video_projects (
    id TEXT PRIMARY KEY,
    wallet_id TEXT NOT NULL,
    telegram_id INTEGER,
    title TEXT,
    status TEXT DEFAULT 'CREATED',  -- CREATED, PROCESSING, COMPLETED, FAILED, SEALED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Video Assets (incoming files)
CREATE TABLE IF NOT EXISTS video_assets (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    original_filename TEXT,
    stored_path TEXT NOT NULL,
    file_size INTEGER,
    duration_seconds REAL,
    width INTEGER,
    height INTEGER,
    codec TEXT,
    fps REAL,
    content_hash TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- 24h retention for originals
    FOREIGN KEY (project_id) REFERENCES video_projects(id)
);

-- Video Jobs (encode queue)
CREATE TABLE IF NOT EXISTS video_jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    edl_json TEXT NOT NULL,          -- Edit Decision List
    preset TEXT DEFAULT 'story_clean',
    status TEXT DEFAULT 'QUEUED',    -- QUEUED, ACTIVE, COMPLETED, FAILED
    progress_percent INTEGER DEFAULT 0,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES video_projects(id),
    FOREIGN KEY (asset_id) REFERENCES video_assets(id)
);

-- Video Exports (completed outputs)
CREATE TABLE IF NOT EXISTS video_exports (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    output_path TEXT NOT NULL,
    thumbnail_path TEXT,
    file_size INTEGER,
    duration_seconds REAL,
    width INTEGER,
    height INTEGER,
    content_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- 7 days retention for sealed
    FOREIGN KEY (job_id) REFERENCES video_jobs(id),
    FOREIGN KEY (project_id) REFERENCES video_projects(id)
);

-- Video Receipts (Ledger seals with I9 gate)
CREATE TABLE IF NOT EXISTS video_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    export_id TEXT NOT NULL,
    wallet_id TEXT NOT NULL,
    receipt_id TEXT,                  -- Ledger receipt ID
    content_hash TEXT NOT NULL,       -- Hash that goes to Ledger (I11: only hash, never content)
    human_approved INTEGER DEFAULT 0, -- I9 gate: must be 1 before seal
    approved_at TIMESTAMP,
    sealed_at TIMESTAMP,
    verify_url TEXT,
    status TEXT DEFAULT 'PENDING',    -- PENDING, APPROVED, SEALED, REJECTED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES video_projects(id),
    FOREIGN KEY (export_id) REFERENCES video_exports(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_wallet ON video_projects(wallet_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON video_projects(status);
CREATE INDEX IF NOT EXISTS idx_assets_project ON video_assets(project_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON video_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_project ON video_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_exports_project ON video_exports(project_id);
CREATE INDEX IF NOT EXISTS idx_receipts_wallet ON video_receipts(wallet_id);
CREATE INDEX IF NOT EXISTS idx_receipts_status ON video_receipts(status);
