import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import sqlite3
from backend.config import SAMPLE_DATA_DIR, SQLITE_DB_PATH
from backend.db.database import get_db_connection, init_db

def parse_containment_hours(content: str) -> Optional[float]:
    """
    Extracts containment duration in hours from report text or table.
    Matches phrases such as:
    - 'contained about 7.1 hours after'
    - 'contained after about 7 hours'
    - 'containment took about 6.4 hours'
    - 'Contained about 8.1 hours after discovery'
    """
    patterns = [
        r'(?:contained|containment took|containment completed)\s+(?:about|after|in|approximately)?\s*([0-9]+(?:\.[0-9]+)?)\s*hours',
        r'SR-02\s*\|\s*(?:\*\*)?[A-Za-z\s]+(?:\*\*)?\s*\|\s*Contained\s+(?:about|after|in|approximately)?\s*([0-9]+(?:\.[0-9]+)?)\s*hours',
        r'contained\s+after\s+([0-9]+(?:\.[0-9]+)?)\s*hours',
    ]
    for pattern in patterns:
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None

def parse_report_fields(content: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {
        "containment_hours": parse_containment_hours(content),
        "spill_class_listed": None,
        "reporting_duty_listed": None,
        "soil_tph_pct": None,
        "soil_samples_count": None,
        "waste_manifest_id": None,
        "pressure_test_psi": None,
        "pressure_test_hours": None,
        "rca_status": None,
        "non_compliant_items": []
    }
    
    # Spill class listed
    m_class = re.search(r'\((\w+)\s+class\)', content, re.IGNORECASE)
    if not m_class:
        m_class = re.search(r'spill\s+class(?:ed)?\s+as\s+["\']?(\w+)["\']?', content, re.IGNORECASE)
    if m_class:
        fields["spill_class_listed"] = m_class.group(1).lower()

    # Soil TPH
    m_tph = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*%\s*TPH', content, re.IGNORECASE)
    if m_tph:
        fields["soil_tph_pct"] = float(m_tph.group(1))

    # Soil samples count
    m_samples = re.search(r'([0-9]+)\s+soil\s+samples\s+taken', content, re.IGNORECASE)
    if m_samples:
        fields["soil_samples_count"] = int(m_samples.group(1))

    # Waste manifest
    m_wm = re.search(r'manifest\s+([A-Z0-9\-]+)', content, re.IGNORECASE)
    if m_wm:
        fields["waste_manifest_id"] = m_wm.group(1)

    # Pressure test
    m_psi = re.search(r'pressure-tested[^\n]*?at\s+([0-9]+(?:\.[0-9]+)?)\s*psi', content, re.IGNORECASE)
    if m_psi:
        fields["pressure_test_psi"] = float(m_psi.group(1))
        
    m_pt_hrs = re.search(r'held\s+(?:it\s+)?for\s+([0-9]+(?:\.[0-9]+)?)\s*hours', content, re.IGNORECASE)
    if m_pt_hrs:
        fields["pressure_test_hours"] = float(m_pt_hrs.group(1))

    # RCA status
    if re.search(r'root-cause analysis[^\n]*?action required|Action required[^\n]*?RCA', content, re.IGNORECASE):
        fields["rca_status"] = "Action required"
    elif re.search(r'RCA required', content, re.IGNORECASE):
        fields["rca_status"] = "Required"

    # Non-compliant items (table parse)
    for line in content.splitlines():
        if "Not met" in line and "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                fields["non_compliant_items"].append({
                    "protocol": parts[0],
                    "status": "Not met",
                    "detail": parts[2] if len(parts) > 2 else ""
                })

    return fields

def ingest_dataset(dataset_dir: Path, db_path: Optional[Path] = None) -> Dict[str, Any]:
    t0 = time.time()
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    fleet_dir = dataset_dir / "fleet"
    assets_dir = dataset_dir / "assets"
    
    # 1. Ingest Areas & Teams
    areas_file = fleet_dir / "areas.json"
    if areas_file.exists():
        with open(areas_file, "r", encoding="utf-8") as f:
            areas_data = json.load(f)
            
        team_rows = []
        for team in areas_data.get("teams", []):
            team_rows.append((
                team["team_id"],
                team["name"],
                team.get("lead_user_id"),
                json.dumps(team)
            ))
        cursor.executemany(
            "INSERT OR REPLACE INTO teams (team_id, name, lead_user_id, raw_json) VALUES (?, ?, ?, ?)",
            team_rows
        )
        
        area_rows = []
        for area in areas_data.get("areas", []):
            center = area.get("center", {})
            area_rows.append((
                area["area_id"],
                area["name"],
                area.get("team_id"),
                center.get("lat"),
                center.get("lon"),
                json.dumps(area)
            ))
        cursor.executemany(
            "INSERT OR REPLACE INTO areas (area_id, name, team_id, center_lat, center_lon, raw_json) VALUES (?, ?, ?, ?, ?, ?)",
            area_rows
        )

    # 2. Ingest Users
    users_file = fleet_dir / "users.json"
    if users_file.exists():
        with open(users_file, "r", encoding="utf-8") as f:
            users_data = json.load(f)
        user_rows = []
        for u in users_data.get("users", []):
            user_rows.append((
                u["user_id"],
                u["name"],
                u["role"],
                u.get("team_id"),
                json.dumps(u)
            ))
        cursor.executemany(
            "INSERT OR REPLACE INTO users (user_id, name, role, team_id, raw_json) VALUES (?, ?, ?, ?, ?)",
            user_rows
        )

    # 3. Ingest Well-Type Rules & SOPs
    well_types_dir = fleet_dir / "well-types"
    if well_types_dir.exists():
        for mf in well_types_dir.glob("*.md"):
            wtype = mf.stem.upper()
            content = mf.read_text(encoding="utf-8")
            doc_id = f"OM-{wtype}"
            
            # Standard params
            min_delta = 15.0 if wtype == "T200" else 20.0
            max_alarm = 85.0 if wtype == "T200" else 95.0
            max_press = 3000.0 if wtype == "T200" else 5000.0
            pj_model = "PJ-228" if wtype == "T200" else "PJ-456"
            wh_model = "WH-3000" if wtype == "T200" else "WH-5000"
            
            cursor.execute("""
                INSERT OR REPLACE INTO well_type_rules 
                (well_type, doc_id, min_temp_delta_c, max_temp_alarm_c, spill_shutin_area_pct,
                 rca_corrective_count, rca_window_months, consecutive_downtime_report_days,
                 max_pressure_psi, pump_jack_model, wellhead_model, manual_path, manual_markdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (wtype, doc_id, min_delta, max_alarm, 5.0, 3, 12, 14, max_press, pj_model, wh_model, str(mf), content))
            
            cursor.execute("INSERT OR REPLACE INTO fleet_documents (doc_id, title, category, file_path, content_md) VALUES (?, ?, ?, ?, ?)",
                           (doc_id, f"{wtype} Operating Manual", "well_type_manual", str(mf), content))
            cursor.execute("INSERT INTO fleet_docs_fts (doc_id, title, category, content_md) VALUES (?, ?, ?, ?)",
                           (doc_id, f"{wtype} Operating Manual", "well_type_manual", content))

    sops_dir = fleet_dir / "sops"
    if sops_dir.exists():
        for sop_file in sops_dir.glob("*.md"):
            content = sop_file.read_text(encoding="utf-8")
            stem = sop_file.stem
            doc_id = "SOP-SR" if "spill" in stem else ("SOP-RC" if "regulatory" in stem else "SOP-WS")
            title = "Spill Response SOP" if "spill" in stem else ("Regulatory Compliance SOP" if "regulatory" in stem else "Field Work SOP")
            
            cursor.execute("INSERT OR REPLACE INTO fleet_documents (doc_id, title, category, file_path, content_md) VALUES (?, ?, ?, ?, ?)",
                           (doc_id, title, "sop", str(sop_file), content))
            cursor.execute("INSERT INTO fleet_docs_fts (doc_id, title, category, content_md) VALUES (?, ?, ?, ?)",
                           (doc_id, title, "sop", content))

    # 4. Ingest Assets (Wells, Inspections, Maintenance, Reports, Regulatory, Context)
    well_folders = sorted(list(assets_dir.glob("WELL-*")))
    total_wells = len(well_folders)
    
    all_wells = []
    all_equip = []
    all_inspections = []
    all_maintenance = []
    all_reports = []
    all_reports_fts = []
    all_reg_events = []
    all_context = []
    all_corrections = []

    for wf in well_folders:
        asset_id = wf.name
        
        # metadata.json
        meta_file = wf / "metadata.json"
        if meta_file.exists():
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            loc = meta.get("location", {})
            last_insp = meta.get("last_inspection", {})
            all_wells.append((
                asset_id,
                meta.get("name", asset_id),
                meta.get("asset_category", "oil_well"),
                meta.get("well_type", "T200"),
                meta.get("area_id", ""),
                meta.get("team_id", ""),
                meta.get("in_charge_user_id"),
                loc.get("lat"),
                loc.get("lon"),
                meta.get("installed_on"),
                meta.get("recorded_status", "active"),
                last_insp.get("inspection_id"),
                last_insp.get("inspected_at"),
                last_insp.get("inspector_user_id"),
                json.dumps(meta)
            ))
            for eq in meta.get("equipment", []):
                all_equip.append((
                    eq["equipment_id"],
                    asset_id,
                    eq["kind"],
                    eq["model"]
                ))
                
        # inspections.jsonl
        insp_file = wf / "inspections.jsonl"
        if insp_file.exists():
            with open(insp_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    inspected_at = item["inspected_at"]
                    all_inspections.append((
                        item["inspection_id"],
                        asset_id,
                        inspected_at,
                        inspected_at[:10],
                        item.get("inspector_user_id"),
                        item.get("method"),
                        item.get("ambient_temp_c"),
                        item.get("wellhead_temp_c"),
                        1 if item.get("spill_detected") else 0,
                        item.get("spill_area_pct"),
                        item.get("spill_est_volume_bbl"),
                        json.dumps(item.get("evidence_images", [])),
                        item.get("notes"),
                        json.dumps(item)
                    ))

        # maintenance.jsonl
        maint_file = wf / "maintenance.jsonl"
        if maint_file.exists():
            with open(maint_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    started_at = item["started_at"]
                    completed_at = item.get("completed_at")
                    costs = item.get("cost_usd", {})
                    all_maintenance.append((
                        item["maintenance_id"],
                        asset_id,
                        started_at,
                        started_at[:10],
                        completed_at,
                        completed_at[:10] if completed_at else None,
                        item.get("maintenance_type", "corrective"),
                        item.get("equipment_kind", ""),
                        item.get("issue"),
                        item.get("action_taken"),
                        item.get("technician_user_id"),
                        item.get("contractor"),
                        item.get("downtime_hours"),
                        costs.get("labor"),
                        costs.get("parts"),
                        costs.get("total"),
                        item.get("triggered_by_inspection_id"),
                        item.get("report_file"),
                        json.dumps(item)
                    ))
                    
                    # If report_file exists, read markdown report
                    rep_rel = item.get("report_file")
                    if rep_rel:
                        # Report can be relative to well directory or dataset directory
                        rep_path = wf / rep_rel
                        if not rep_path.exists():
                            rep_path = dataset_dir / rep_rel
                        if rep_path.exists():
                            rep_md = rep_path.read_text(encoding="utf-8")
                            parsed = parse_report_fields(rep_md)
                            all_reports.append((
                                item["maintenance_id"],
                                asset_id,
                                rep_rel,
                                item.get("triggered_by_inspection_id"),
                                parsed["containment_hours"],
                                parsed["spill_class_listed"],
                                parsed["reporting_duty_listed"],
                                parsed["soil_tph_pct"],
                                parsed["soil_samples_count"],
                                parsed["waste_manifest_id"],
                                parsed["pressure_test_psi"],
                                parsed["pressure_test_hours"],
                                parsed["rca_status"],
                                json.dumps(parsed["non_compliant_items"]),
                                rep_md
                            ))
                            all_reports_fts.append((
                                item["maintenance_id"],
                                asset_id,
                                rep_rel,
                                rep_md
                            ))

        # regulatory-events.jsonl
        reg_file = wf / "regulatory-events.jsonl"
        if reg_file.exists():
            with open(reg_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    all_reg_events.append((
                        item["event_id"],
                        asset_id,
                        item["date"],
                        item.get("agency"),
                        item.get("event_type"),
                        item.get("protocol_id"),
                        item.get("related_inspection_id"),
                        item.get("hours_to_report"),
                        item.get("detail"),
                        item.get("fine_usd"),
                        item.get("status", "open"),
                        json.dumps(item)
                    ))

        # context.jsonl
        ctx_file = wf / "context.jsonl"
        if ctx_file.exists():
            with open(ctx_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    note_id = item.get("note_id", f"CTX-{asset_id}")
                    all_context.append((
                        note_id,
                        asset_id,
                        item.get("created_at"),
                        item.get("author_user_id"),
                        item.get("note_type", "operator_note"),
                        item.get("inspection_id"),
                        item.get("text", ""),
                        item.get("valid_from"),
                        item.get("valid_to"),
                        "dataset",
                        "verified",
                        None,
                        json.dumps(item)
                    ))
                    
                    # Auto register dataset correction
                    if item.get("note_type") == "correction" and item.get("inspection_id"):
                        all_corrections.append((
                            f"CORR-{note_id}",
                            "spill_false_positive",
                            asset_id,
                            item.get("inspection_id"),
                            "spill_detected",
                            "1",
                            "0",
                            item.get("text"),
                            item.get("author_user_id"),
                            item.get("created_at"),
                            None
                        ))

    # Fast bulk insertion using transactions
    cursor.executemany("""
        INSERT OR REPLACE INTO wells 
        (asset_id, name, asset_category, well_type, area_id, team_id, in_charge_user_id, lat, lon,
         installed_on, recorded_status, last_inspection_id, last_inspection_at, last_inspector_user_id, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_wells)

    cursor.executemany("""
        INSERT OR REPLACE INTO well_equipment (equipment_id, asset_id, kind, model)
        VALUES (?, ?, ?, ?)
    """, all_equip)

    cursor.executemany("""
        INSERT OR REPLACE INTO inspections 
        (inspection_id, asset_id, inspected_at, inspected_date, inspector_user_id, method, ambient_temp_c,
         wellhead_temp_c, spill_detected, spill_area_pct, spill_est_volume_bbl, evidence_images_json, notes, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_inspections)

    cursor.executemany("""
        INSERT OR REPLACE INTO maintenance 
        (maintenance_id, asset_id, started_at, started_date, completed_at, completed_date, maintenance_type,
         equipment_kind, issue, action_taken, technician_user_id, contractor, downtime_hours,
         cost_labor_usd, cost_parts_usd, cost_total_usd, triggered_by_inspection_id, report_file, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_maintenance)

    cursor.executemany("""
        INSERT OR REPLACE INTO maintenance_reports
        (maintenance_id, asset_id, report_file, triggered_by_inspection_id, containment_hours, spill_class_listed,
         reporting_duty_listed, soil_tph_pct, soil_samples_count, waste_manifest_id, pressure_test_psi,
         pressure_test_hours, rca_status, non_compliant_items_json, content_md)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_reports)

    cursor.executemany("""
        INSERT INTO maintenance_reports_fts (maintenance_id, asset_id, report_file, content_md)
        VALUES (?, ?, ?, ?)
    """, all_reports_fts)

    cursor.executemany("""
        INSERT OR REPLACE INTO regulatory_events
        (event_id, asset_id, date, agency, event_type, protocol_id, related_inspection_id, hours_to_report, detail, fine_usd, status, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_reg_events)

    cursor.executemany("""
        INSERT OR REPLACE INTO context_notes
        (note_id, asset_id, created_at, author_user_id, note_type, inspection_id, text, valid_from, valid_to, source, verification_status, conflict_detail, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_context)

    cursor.executemany("""
        INSERT OR REPLACE INTO data_corrections
        (correction_id, target_type, asset_id, inspection_id, field_name, old_value, new_value, reason, author_user_id, created_at, conflict_warning)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_corrections)

    dataset_id = dataset_dir.name
    cursor.execute("""
        INSERT OR REPLACE INTO datasets_loaded (dataset_id, source_path, loaded_at, well_count, inspection_count)
        VALUES (?, ?, datetime('now'), ?, ?)
    """, (dataset_id, str(dataset_dir), total_wells, len(all_inspections)))

    conn.commit()
    conn.close()

    elapsed = round(time.time() - t0, 2)
    stats = {
        "dataset": dataset_id,
        "elapsed_seconds": elapsed,
        "wells": total_wells,
        "inspections": len(all_inspections),
        "maintenance": len(all_maintenance),
        "reports": len(all_reports),
        "regulatory_events": len(all_reg_events),
        "context_notes": len(all_context),
        "corrections": len(all_corrections)
    }
    return stats

if __name__ == "__main__":
    print(f"Starting ingestion from {SAMPLE_DATA_DIR}...")
    stats = ingest_dataset(SAMPLE_DATA_DIR)
    print("Ingestion Complete:")
    print(json.dumps(stats, indent=2))
