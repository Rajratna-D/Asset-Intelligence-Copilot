PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS datasets_loaded (
    dataset_id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    loaded_at TEXT NOT NULL,
    well_count INTEGER,
    inspection_count INTEGER
);

CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    lead_user_id TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS areas (
    area_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    team_id TEXT,
    center_lat REAL,
    center_lon REAL,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    team_id TEXT,
    raw_json TEXT
);

CREATE TABLE IF NOT EXISTS well_type_rules (
    well_type TEXT PRIMARY KEY,
    doc_id TEXT,
    min_temp_delta_c REAL NOT NULL,
    max_temp_alarm_c REAL NOT NULL,
    spill_shutin_area_pct REAL NOT NULL DEFAULT 5.0,
    rca_corrective_count INTEGER NOT NULL DEFAULT 3,
    rca_window_months INTEGER NOT NULL DEFAULT 12,
    consecutive_downtime_report_days INTEGER NOT NULL DEFAULT 14,
    max_pressure_psi REAL,
    pump_jack_model TEXT,
    wellhead_model TEXT,
    manual_path TEXT,
    manual_markdown TEXT
);

CREATE TABLE IF NOT EXISTS sop_protocols (
    protocol_id TEXT PRIMARY KEY,
    sop_doc_id TEXT NOT NULL,
    sop_title TEXT NOT NULL,
    requirement_summary TEXT NOT NULL,
    threshold_json TEXT,
    file_path TEXT
);

CREATE TABLE IF NOT EXISTS fleet_documents (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_md TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS fleet_docs_fts USING fts5(
    doc_id, title, category, content_md
);

CREATE TABLE IF NOT EXISTS wells (
    asset_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    asset_category TEXT,
    well_type TEXT NOT NULL,
    area_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    in_charge_user_id TEXT,
    lat REAL,
    lon REAL,
    installed_on TEXT,
    recorded_status TEXT,
    last_inspection_id TEXT,
    last_inspection_at TEXT,
    last_inspector_user_id TEXT,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_wells_area ON wells(area_id);
CREATE INDEX IF NOT EXISTS idx_wells_type ON wells(well_type);

CREATE TABLE IF NOT EXISTS well_equipment (
    equipment_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    model TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_well_equip_asset ON well_equipment(asset_id);

CREATE TABLE IF NOT EXISTS inspections (
    inspection_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    inspected_at TEXT NOT NULL,
    inspected_date TEXT NOT NULL,
    inspector_user_id TEXT,
    method TEXT,
    ambient_temp_c REAL,
    wellhead_temp_c REAL,
    spill_detected INTEGER NOT NULL DEFAULT 0,
    spill_area_pct REAL,
    spill_est_volume_bbl REAL,
    evidence_images_json TEXT,
    notes TEXT,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_inspections_asset_date ON inspections(asset_id, inspected_at DESC);
CREATE INDEX IF NOT EXISTS idx_inspections_date ON inspections(inspected_date);
CREATE INDEX IF NOT EXISTS idx_inspections_spill ON inspections(spill_detected);

CREATE TABLE IF NOT EXISTS maintenance (
    maintenance_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    started_date TEXT NOT NULL,
    completed_at TEXT,
    completed_date TEXT,
    maintenance_type TEXT NOT NULL,
    equipment_kind TEXT NOT NULL,
    issue TEXT,
    action_taken TEXT,
    technician_user_id TEXT,
    contractor TEXT,
    downtime_hours REAL,
    cost_labor_usd REAL,
    cost_parts_usd REAL,
    cost_total_usd REAL,
    triggered_by_inspection_id TEXT,
    report_file TEXT,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_maint_asset_start ON maintenance(asset_id, started_date);
CREATE INDEX IF NOT EXISTS idx_maint_equip_type ON maintenance(equipment_kind, maintenance_type, started_date);

CREATE TABLE IF NOT EXISTS maintenance_reports (
    maintenance_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    report_file TEXT NOT NULL,
    triggered_by_inspection_id TEXT,
    containment_hours REAL,
    spill_class_listed TEXT,
    reporting_duty_listed TEXT,
    soil_tph_pct REAL,
    soil_samples_count INTEGER,
    waste_manifest_id TEXT,
    pressure_test_psi REAL,
    pressure_test_hours REAL,
    rca_status TEXT,
    non_compliant_items_json TEXT,
    content_md TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_maint_reports_asset ON maintenance_reports(asset_id);

CREATE VIRTUAL TABLE IF NOT EXISTS maintenance_reports_fts USING fts5(
    maintenance_id, asset_id, report_file, content_md
);

CREATE TABLE IF NOT EXISTS regulatory_events (
    event_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    date TEXT NOT NULL,
    agency TEXT,
    event_type TEXT NOT NULL,
    protocol_id TEXT,
    related_inspection_id TEXT,
    hours_to_report REAL,
    detail TEXT,
    fine_usd REAL,
    status TEXT,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_reg_asset ON regulatory_events(asset_id, date);
CREATE INDEX IF NOT EXISTS idx_reg_type ON regulatory_events(event_type);

CREATE TABLE IF NOT EXISTS context_notes (
    note_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    author_user_id TEXT,
    note_type TEXT NOT NULL,
    inspection_id TEXT,
    text TEXT NOT NULL,
    valid_from TEXT,
    valid_to TEXT,
    source TEXT NOT NULL DEFAULT 'dataset',
    verification_status TEXT DEFAULT 'verified',
    conflict_detail TEXT,
    raw_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_context_asset ON context_notes(asset_id);
CREATE INDEX IF NOT EXISTS idx_context_insp ON context_notes(inspection_id);

CREATE TABLE IF NOT EXISTS data_corrections (
    correction_id TEXT PRIMARY KEY,
    target_type TEXT NOT NULL, -- 'inspection_temp' | 'spill_false_positive' | 'spill_volume'
    asset_id TEXT NOT NULL,
    inspection_id TEXT,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    reason TEXT NOT NULL,
    author_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    conflict_warning TEXT
);

CREATE INDEX IF NOT EXISTS idx_corrections_asset_insp ON data_corrections(asset_id, inspection_id);

CREATE TABLE IF NOT EXISTS rule_overrides (
    override_id TEXT PRIMARY KEY,
    scope_type TEXT NOT NULL, -- 'well_type' | 'area' | 'asset'
    scope_value TEXT NOT NULL, -- e.g. 'T350'
    equipment_kind TEXT,       -- e.g. 'pump_jack'
    rule_key TEXT NOT NULL,    -- e.g. 'rca_corrective_count'
    old_value REAL,
    new_value REAL NOT NULL,
    author_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS private_chat_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS private_chat_messages (
    message_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    entities_discussed_json TEXT,
    visual_json TEXT,
    citations_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chat_user_session ON private_chat_messages(user_id, session_id);
