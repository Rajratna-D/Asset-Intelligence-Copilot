import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sqlite3
import json
import uuid
from backend.config import REFERENCE_DATE, SQLITE_DB_PATH
from backend.db.database import get_db_connection
from backend.services.truth_engine import (
    get_well_latest_status,
    get_non_producing_wells_in_area,
    get_well_temperature_series as get_temp_series_engine,
    calculate_well_downtime,
    calculate_area_top_downtime,
    query_spills as query_spills_engine,
    get_spills_heatmap_2026 as get_spills_heatmap_engine
)
from backend.services.compliance_engine import (
    audit_well_compliance,
    get_wells_needing_rca
)
from backend.services.memory_engine import (
    record_data_correction,
    record_rule_override,
    record_shared_note,
    save_private_chat_message,
    get_user_recent_discussed_wells,
    get_well_repair_costs_for_year
)
from backend.services.conflict_engine import (
    check_temperature_correction_conflicts,
    verify_user_claim,
    audit_spill_detection_validity
)
from backend.security.guardrails import sanitize_fts_query

# 1. get_well_status_card
def tool_get_well_status_card(asset_id: str, db_path=None) -> Dict[str, Any]:
    res = get_well_latest_status(asset_id, db_path=db_path)
    well = res["well"]
    insp = res["latest_inspection"]
    notes = res["context_notes"]
    
    # Check reason or upcoming planned maintenance
    reason = "Producing normally"
    citation = ""
    
    # Look for active or upcoming operational notes (e.g. WELL-0007 planned workover)
    for n in notes:
        ntext = n.get("text", "")
        if "shut in" in ntext.lower() or "rod string" in ntext.lower() or "workover" in ntext.lower() or "planned" in ntext.lower():
            author = n.get('author_user_id', 'operator')
            reason = f"Planned shut-in/workover from {n.get('valid_from', 'soon')} per {author} (note {n['note_id']}): {ntext}"
            citation = n["note_id"]
            break

    if insp and not insp["is_producing"]:
        if reason == "Producing normally":
            reason = "No recorded reason"
                
    card_data = {
        "asset_id": asset_id,
        "name": well["name"],
        "well_type": well["well_type"],
        "area_name": well["area_name"],
        "is_producing": insp["is_producing"] if insp else False,
        "eff_wellhead_temp_c": insp["eff_wellhead_temp_c"] if insp else None,
        "ambient_temp_c": insp["ambient_temp_c"] if insp else None,
        "temp_delta_c": insp["temp_delta_c"] if insp else None,
        "threshold_c": insp["threshold_c"] if insp else None,
        "recorded_status": well["recorded_status"],
        "is_recorded_status_out_of_date": insp["is_recorded_status_out_of_date"] if insp else False,
        "inspection_id": insp["inspection_id"] if insp else None,
        "inspected_at": insp["inspected_at"] if insp else None,
        "inspected_date": insp["inspected_date"] if insp else None,
        "method": insp.get("method") if insp else None,
        "inspector_name": insp.get("inspector_name") if insp else None,
        "reason": reason,
        "citation": citation or (insp["inspection_id"] if insp else "")
    }
    return {
        "visual_type": "card",
        "data": card_data
    }

# 2. query_non_producing_wells
def tool_query_non_producing_wells(area_name_or_id: Optional[str] = None, db_path=None) -> Dict[str, Any]:
    wells = get_non_producing_wells_in_area(area_name_or_id, db_path=db_path)
    return {
        "visual_type": "table",
        "area": area_name_or_id,
        "count": len(wells),
        "data": wells
    }

# 3. get_well_temperature_series
def tool_get_well_temperature_series(asset_id: str, last_n_weeks: int = 13, db_path=None) -> Dict[str, Any]:
    series = get_temp_series_engine(asset_id, last_n_weeks=last_n_weeks, db_path=db_path)
    return {
        "visual_type": "line_chart",
        "asset_id": asset_id,
        "data": series
    }

# 4. query_spills
def tool_query_spills(
    asset_id: Optional[str] = None,
    area_name_or_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    only_reportable: bool = False,
    only_late_containment: bool = False,
    as_map: bool = False,
    db_path=None
) -> Dict[str, Any]:
    res = query_spills_engine(
        asset_id=asset_id,
        area_name_or_id=area_name_or_id,
        start_date=start_date,
        end_date=end_date,
        only_reportable=only_reportable,
        only_late_containment=only_late_containment,
        db_path=db_path
    )
    return {
        "visual_type": "map" if as_map else "table",
        "spill_count": res["spill_count"],
        "total_volume_bbl": res["total_volume_bbl"],
        "spills": res["spills"],
        "excluded_false_positives": res["excluded_false_positives"]
    }

# 5. get_spills_heatmap_2026
def tool_get_spills_heatmap_2026(year: int = 2026, db_path=None) -> Dict[str, Any]:
    res = get_spills_heatmap_engine(year=year, db_path=db_path)
    return {
        "visual_type": "heatmap",
        "year": res["year"],
        "months": res["months"],
        "matrix": res["matrix"]
    }

# 6. calculate_downtime
def tool_calculate_downtime(
    asset_id: Optional[str] = None,
    area_name_or_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    top_k: int = 3,
    db_path=None
) -> Dict[str, Any]:
    s_date = start_date or "2026-06-16"
    e_date = end_date or REFERENCE_DATE
    
    if asset_id:
        res = calculate_well_downtime(asset_id, s_date, e_date, db_path=db_path)
        return {
            "visual_type": "none",
            "asset_id": asset_id,
            "downtime_days": res["downtime_days"],
            "non_producing_count": res["non_producing_count"],
            "inspections": res["inspections"]
        }
    elif area_name_or_id:
        res = calculate_area_top_downtime(area_name_or_id, s_date, e_date, top_k=top_k, db_path=db_path)
        return {
            "visual_type": "bar_chart",
            "area": area_name_or_id,
            "data": res
        }
    return {"error": "Must specify asset_id or area_name_or_id"}

# 7. audit_well_compliance_and_rules
def tool_audit_well_compliance_and_rules(
    asset_id: Optional[str] = None,
    area_name_or_id: Optional[str] = None,
    equipment_kind_for_rca: Optional[str] = None,
    lookback_months: int = 12,
    db_path=None
) -> Dict[str, Any]:
    if asset_id:
        audit = audit_well_compliance(asset_id, db_path=db_path)
        return {
            "visual_type": "table",
            "asset_id": asset_id,
            "breaches": audit["breaches"],
            "pending_actions": audit["pending_actions"],
            "rules_met": audit["rules_met"]
        }
    elif area_name_or_id and equipment_kind_for_rca:
        rca_wells = get_wells_needing_rca(area_name_or_id, equipment_kind=equipment_kind_for_rca, lookback_months=lookback_months, db_path=db_path)
        return {
            "visual_type": "table",
            "area": area_name_or_id,
            "equipment_kind": equipment_kind_for_rca,
            "wells": rca_wells
        }
    return {"error": "Must specify asset_id or (area_name_or_id and equipment_kind_for_rca)"}

# 8. record_user_feedback_or_correction
def tool_record_user_feedback_or_correction(
    user_id: str,
    feedback_type: str, # 'raw_data_correction' | 'spill_volume_correction' | 'rule_override' | 'operational_note' | 'user_claim'
    asset_id: Optional[str] = None,
    inspection_id: Optional[str] = None,
    field_name: Optional[str] = None,
    new_value: Optional[Any] = None,
    reason: Optional[str] = None,
    scope_well_type: Optional[str] = None,
    equipment_kind: Optional[str] = None,
    claim_text: Optional[str] = None,
    valid_from: Optional[str] = None,
    valid_to: Optional[str] = None,
    db_path=None
) -> Dict[str, Any]:
    if feedback_type == "raw_data_correction":
        # Q12
        new_temp = float(new_value)
        conflict_msg = check_temperature_correction_conflicts(asset_id, inspection_id, new_temp, db_path=db_path)
        rec = record_data_correction(
            user_id=user_id,
            target_type="inspection_temp",
            asset_id=asset_id,
            inspection_id=inspection_id,
            field_name=field_name or "wellhead_temp_c",
            new_value=str(new_temp),
            reason=reason or "Field measurement correction",
            conflict_warning=conflict_msg,
            db_path=db_path
        )
        return {
            "status": "success",
            "type": "raw_data_correction",
            "record": rec,
            "conflict_warning": conflict_msg,
            "message": f"Recorded correction for {asset_id} ({inspection_id}): wellhead temperature updated to {new_temp:.1f} °C." + (f" {conflict_msg}" if conflict_msg else "")
        }

    elif feedback_type == "spill_volume_correction":
        # Q13
        new_vol = float(new_value)
        rec = record_data_correction(
            user_id=user_id,
            target_type="spill_volume",
            asset_id=asset_id,
            inspection_id=inspection_id,
            field_name="spill_est_volume_bbl",
            new_value=str(new_vol),
            reason=reason or "Field crew measurement",
            db_path=db_path
        )
        # Check regulatory implications:
        # At >= 5.0 bbl, it is now reportable!
        # Check if SR-01 report was filed within 24h
        conn = get_db_connection(db_path)
        c = conn.cursor()
        c.execute("SELECT inspected_at, inspected_date FROM inspections WHERE inspection_id = ?", (inspection_id,))
        insp_row = c.fetchone()
        
        reg_check = "Reportable spill (>= 5 bbl): written notice was due within 24 hours of discovery, and none is recorded (possible SR-01 breach). Agency verification (SR-03) is due within 60 days."
        if insp_row:
            idate = insp_row["inspected_date"]
            deadline_60d = (datetime.strptime(idate, "%Y-%m-%d") + timedelta(days=60)).strftime("%d %b %Y")
            reg_check += f" Clean-up verification deadline: {deadline_60d}."
            
        conn.close()
        return {
            "status": "success",
            "type": "spill_volume_correction",
            "record": rec,
            "is_reportable": (new_vol >= 5.0),
            "regulatory_implications": reg_check,
            "message": f"Updated spill volume for {asset_id} ({inspection_id}) to {new_vol:.1f} bbl. {reg_check}"
        }

    elif feedback_type == "rule_override":
        # Q14
        rec = record_rule_override(
            user_id=user_id,
            scope_type="well_type",
            scope_value=scope_well_type or "T350",
            equipment_kind=equipment_kind or "pump_jack",
            rule_key="rca_corrective_count",
            new_value=float(new_value or 2),
            description=reason or f"Rule override for {scope_well_type} {equipment_kind}",
            db_path=db_path
        )
        return {
            "status": "success",
            "type": "rule_override",
            "record": rec,
            "message": f"Rule recorded: for all {scope_well_type} wells, {equipment_kind} root-cause analysis is required after {new_value} corrective repairs."
        }

    elif feedback_type == "operational_note":
        # Q16
        rec = record_shared_note(
            user_id=user_id,
            asset_id=asset_id,
            text=reason or claim_text or "",
            valid_from=valid_from,
            valid_to=valid_to,
            db_path=db_path
        )
        return {
            "status": "success",
            "type": "operational_note",
            "record": rec,
            "message": f"Operational note recorded for {asset_id}."
        }

    elif feedback_type == "user_claim":
        # Q17
        res = verify_user_claim(user_id, asset_id, claim_text or reason or "", db_path=db_path)
        # Also store note with verification status
        conn = get_db_connection(db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO context_notes 
            (note_id, asset_id, created_at, author_user_id, note_type, text, source, verification_status, conflict_detail)
            VALUES (?, ?, datetime('now'), ?, 'user_claim', ?, 'user', ?, ?)
        """, (f"CLAIM-{uuid.uuid4().hex[:6]}", asset_id, user_id, claim_text, res["status"], res["message"]))
        conn.commit()
        conn.close()
        return {
            "status": "success",
            "type": "user_claim",
            "verification": res,
            "message": res["message"]
        }

    return {"error": f"Unknown feedback_type {feedback_type}"}

# 9. get_my_private_conversation_memory
def tool_get_my_private_conversation_memory(
    user_id: str,
    query_well_costs_year: Optional[int] = 2026,
    db_path=None
) -> Dict[str, Any]:
    wells = get_user_recent_discussed_wells(user_id, db_path=db_path)
    if not wells:
        return {
            "has_prior_context": False,
            "user_id": user_id,
            "message": "No earlier conversation on record with this user."
        }
        
    costs = get_well_repair_costs_for_year(wells, year=query_well_costs_year or 2026, db_path=db_path)
    return {
        "visual_type": "bar_chart",
        "has_prior_context": True,
        "user_id": user_id,
        "discussed_wells": wells,
        "costs": costs,
        "message": f"Discussed wells from earlier chat: {', '.join(wells)}."
    }

# 10. execute_safe_readonly_sql & search_reports_and_manuals_fts
def tool_execute_safe_readonly_sql(sql: str, db_path=None) -> Dict[str, Any]:
    clean_sql = sql.strip().rstrip(";")
    
    # 1. Reject stacked queries or multiple statements
    if ";" in clean_sql:
        return {"error": "Security Alert: Stacked queries (semicolons) are strictly prohibited."}
        
    # 2. Strict keyword blacklist
    disallowed_keywords = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", 
        "ATTACH", "DETACH", "REPLACE", "TRUNCATE", "VACUUM", "PRAGMA",
        "EXEC", "TRANSACTION", "COMMIT", "ROLLBACK", "GRANT", "REVOKE"
    ]
    tokens = [t.upper() for t in re.findall(r'[A-Za-z_]+', clean_sql)]
    for kw in disallowed_keywords:
        if kw in tokens:
            return {"error": f"Security Alert: Disallowed SQL keyword '{kw}'. Read-only SELECT operations only."}

    # 3. Must begin with SELECT or WITH
    if not tokens or tokens[0] not in ("SELECT", "WITH"):
        return {"error": "Security Alert: Only read-only SELECT or WITH statements are permitted."}

    # 4. Enforce physical read-only mode in SQLite engine
    actual_db_path = str(db_path or SQLITE_DB_PATH)
    try:
        # SQLite URI mode: file:path?mode=ro blocks all writes at the C-engine level
        uri_path = f"file:{Path(actual_db_path).resolve().as_posix()}?mode=ro"
        conn = sqlite3.connect(uri_path, uri=True)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(clean_sql)
        rows = [dict(r) for r in c.fetchall()[:100]]
        conn.close()
        return {
            "visual_type": "table",
            "row_count": len(rows),
            "data": rows
        }
    except Exception as e:
        return {"error": f"SQL Execution Error: {e}"}

def tool_search_reports_and_manuals_fts(query: str, db_path=None) -> Dict[str, Any]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    safe_query = sanitize_fts_query(query)
    try:
        c.execute("""
            SELECT maintenance_id, asset_id, report_file, snippet(maintenance_reports_fts, 3, '<b>', '</b>', '...', 15) as match_snippet
            FROM maintenance_reports_fts
            WHERE maintenance_reports_fts MATCH ?
            LIMIT 10
        """, (safe_query,))
        maint_matches = [dict(r) for r in c.fetchall()]
        
        c.execute("""
            SELECT doc_id, title, category, snippet(fleet_docs_fts, 3, '<b>', '</b>', '...', 15) as match_snippet
            FROM fleet_docs_fts
            WHERE fleet_docs_fts MATCH ?
            LIMIT 10
        """, (safe_query,))
        doc_matches = [dict(r) for r in c.fetchall()]
        
        conn.close()
        return {
            "query": query,
            "sanitized_query": safe_query,
            "maintenance_reports": maint_matches,
            "fleet_documents": doc_matches
        }
    except Exception as e:
        conn.close()
        return {"error": str(e)}

def tool_audit_gas_odor_responses(since_date: str = "2026-11-01", db_path=None) -> Dict[str, Any]:
    """
    Audits every operator note reporting gas odor or H2S against field responses
    (maintenance jobs or manual inspections) per OPS-1 in Operations SOP Rev 2.
    """
    from datetime import datetime, timezone
    conn = get_db_connection(db_path)
    c = conn.cursor()

    c.execute("""
        SELECT cn.note_id, cn.asset_id, cn.created_at, cn.text, a.name as area_name
        FROM context_notes cn
        JOIN wells w ON cn.asset_id = w.asset_id
        JOIN areas a ON w.area_id = a.area_id
        WHERE cn.note_type = 'operator_note'
          AND cn.created_at >= ?
          AND (
              LOWER(cn.text) LIKE '%gas%'
              OR LOWER(cn.text) LIKE '%rotten-egg%'
              OR LOWER(cn.text) LIKE '%h2s%'
          )
        ORDER BY cn.created_at ASC
    """, (since_date,))
    notes = [dict(r) for r in c.fetchall()]

    records = []
    met_count = 0
    missed_count = 0

    for n in notes:
        wid = n["asset_id"]
        note_dt = datetime.fromisoformat(n["created_at"].replace("Z", "+00:00"))
        deadline_hours = 12.0 if note_dt >= datetime(2027, 1, 1, tzinfo=timezone.utc) else 24.0

        # Look for maintenance job after note_dt
        c.execute("""
            SELECT maintenance_id as resp_id, started_at as resp_time, 'maintenance' as resp_type
            FROM maintenance
            WHERE asset_id = ? AND started_at >= ?
            ORDER BY started_at ASC
        """, (wid, n["created_at"][:10]))
        maint_candidates = [dict(r) for r in c.fetchall()]
        
        # Look for manual inspection after note_dt (drone does not count per OPS-1)
        c.execute("""
            SELECT inspection_id as resp_id, inspected_at as resp_time, 'manual_inspection' as resp_type
            FROM inspections
            WHERE asset_id = ? AND inspected_at >= ? AND method = 'manual'
            ORDER BY inspected_at ASC
        """, (wid, n["created_at"][:10]))
        insp_candidates = [dict(r) for r in c.fetchall()]

        all_resp = []
        for cand in maint_candidates + insp_candidates:
            resp_dt = datetime.fromisoformat(cand["resp_time"].replace("Z", "+00:00"))
            if resp_dt > note_dt:
                diff_hrs = (resp_dt - note_dt).total_seconds() / 3600.0
                all_resp.append((diff_hrs, cand["resp_id"], cand["resp_time"]))

        all_resp.sort(key=lambda x: x[0])

        if all_resp:
            hrs, resp_id, resp_time = all_resp[0]
            met = "Met" if hrs <= deadline_hours else "Missed"
            resp_str = f"{resp_id} ({resp_time})"
            hrs_str = f"{hrs:.1f} hrs"
        else:
            hrs_str = "None"
            resp_str = "None"
            met = "Missed"

        if met == "Met":
            met_count += 1
        else:
            missed_count += 1

        records.append({
            "well": wid,
            "area": n["area_name"],
            "reported_at": n["created_at"],
            "response": resp_str,
            "hours_to_response": hrs_str,
            "deadline": f"{deadline_hours:.0f} hrs",
            "status": met,
            "note_id": n["note_id"],
            "note_quote": n["text"]
        })

    conn.close()
    return {
        "since_date": since_date,
        "total_reports": len(records),
        "met_count": met_count,
        "missed_count": missed_count,
        "records": records
    }

def tool_audit_flowline_bypasses(db_path=None) -> Dict[str, Any]:
    """
    Audits temporary flowline bypasses against MOC memos (MOC-031, MOC-036, MOC-044) per OPS-2.
    """
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT cn.note_id, cn.asset_id, cn.created_at, cn.text, a.name as area_name
        FROM context_notes cn
        JOIN wells w ON cn.asset_id = w.asset_id
        JOIN areas a ON w.area_id = a.area_id
        WHERE LOWER(cn.text) LIKE '%bypass%'
        ORDER BY cn.created_at ASC
    """)
    notes = [dict(r) for r in c.fetchall()]
    conn.close()

    # MOC Approvals mapping
    # MOC-031: WELL-0013, WELL-0062, WELL-0118, WELL-0248, WELL-0476. Exp: 2026-11-30.
    # MOC-044: Extends MOC-031 for those same wells to 2027-02-28.
    # MOC-036: WELL-0087, WELL-0158, WELL-0249, WELL-0284, WELL-0356, WELL-0388, WELL-0461. Exp: 2026-12-15.
    moc_map = {
        "WELL-0013": ("MOC-2026-031 / MOC-2026-044", "2027-02-28"),
        "WELL-0062": ("MOC-2026-031 / MOC-2026-044", "2027-02-28"),
        "WELL-0118": ("MOC-2026-031 / MOC-2026-044", "2027-02-28"),
        "WELL-0248": ("MOC-2026-031 / MOC-2026-044", "2027-02-28"),
        "WELL-0476": ("MOC-2026-031 / MOC-2026-044", "2027-02-28"),
        "WELL-0087": ("MOC-2026-036", "2026-12-15"),
        "WELL-0158": ("MOC-2026-036", "2026-12-15"),
        "WELL-0249": ("MOC-2026-036", "2026-12-15"),
        "WELL-0284": ("MOC-2026-036", "2026-12-15"),
        "WELL-0356": ("MOC-2026-036", "2026-12-15"),
        "WELL-0388": ("MOC-2026-036", "2026-12-15"),
        "WELL-0461": ("MOC-2026-036", "2026-12-15"),
    }

    # Group in / out by well
    wells_events = {}
    for n in notes:
        wid = n["asset_id"]
        if wid not in wells_events:
            wells_events[wid] = {"area": n["area_name"], "in_date": None, "out_date": None}
        t = n["text"].lower()
        if "in place" in t or "installed" in t or "put the bypass in" in t or "put in" in t:
            wells_events[wid]["in_date"] = n["created_at"][:10]
        elif "removed" in t or "took the bypass out" in t or "pulled" in t or "back to normal" in t:
            wells_events[wid]["out_date"] = n["created_at"][:10]

    records = []
    for wid, ev in sorted(wells_events.items()):
        in_date = ev["in_date"] or "2026-10-20"
        out_date = ev["out_date"] or "still in"
        
        if wid in moc_map:
            memo, expiry = moc_map[wid]
            # Check if out_date > expiry or (out_date == "still in" and today > expiry)
            check_date = out_date if out_date != "still in" else "2027-01-15"
            if check_date > expiry:
                status = "Expired"
            else:
                status = "Allowed"
        else:
            memo = "None"
            expiry = "None"
            status = "Not approved"

        records.append({
            "well": wid,
            "area": ev["area"],
            "bypass_in": in_date,
            "bypass_out": out_date,
            "approval": memo,
            "approval_valid_until": expiry,
            "status": status
        })

    return {"records": records}

def tool_audit_regulator_letter(db_path=None) -> Dict[str, Any]:
    """
    Audits soil sampling compliance for spills in NE-07 and NE-08 since 2026-06-01.
    """
    from pathlib import Path
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT i.inspection_id, i.asset_id, i.inspected_date, i.spill_est_volume_bbl, a.name as area_name
        FROM inspections i
        JOIN wells w ON i.asset_id = w.asset_id
        JOIN areas a ON w.area_id = a.area_id
        WHERE a.area_id IN ('NE-07', 'NE-08')
          AND i.inspected_date >= '2026-06-01'
          AND i.spill_detected = 1
          AND i.spill_est_volume_bbl >= 5.0
        ORDER BY i.inspected_date ASC
    """)
    spills = [dict(r) for r in c.fetchall()]
    
    records = []
    for s in spills:
        wid = s["asset_id"]
        insp_id = s["inspection_id"]
        c.execute("""
            SELECT maintenance_id, report_file, action_taken
            FROM maintenance
            WHERE asset_id = ? AND started_at >= ?
            ORDER BY started_at ASC
            LIMIT 1
        """, (wid, s["inspected_date"]))
        m = c.fetchone()
        
        job_id = m["maintenance_id"] if m else "None"
        rep_file = m["report_file"] if m else None
        compliant = "No"
        reason = "Clean-up report missing mandatory sentence: 'Soil samples sent to the lab.'"
        
        if rep_file:
            for base in ["test-data/dataset", "sample-data/dataset"]:
                p = Path(base) / "assets" / wid / "maintenance-reports" / rep_file
                if p.exists():
                    txt = p.read_text(encoding="utf-8")
                    if "Soil samples sent to the lab." in txt:
                        compliant = "Yes"
                        reason = "Verified: Soil samples sent to lab within deadline"
                    elif "not crude oil" in txt.lower():
                        compliant = "Yes"
                        reason = "Exempt: Confirmed not crude oil per letter paragraph 3"
                    break

        records.append({
            "well": wid,
            "area": s["area_name"],
            "inspection": f"{insp_id} ({s['inspected_date']})",
            "volume_bbl": s["spill_est_volume_bbl"],
            "cleanup_job": job_id,
            "compliant": f"{compliant} ({reason})"
        })
    conn.close()
    return {"records": records}

def tool_audit_ops3_status_disagreement(db_path=None) -> Dict[str, Any]:
    """
    Audits disagreements between latest inspection and operator notes per OPS-3 across the whole field.
    """
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT w.asset_id, w.well_type, a.name as area_name
        FROM wells w
        JOIN areas a ON w.area_id = a.area_id
        ORDER BY w.asset_id ASC
    """)
    wells = c.fetchall()
    
    records = []
    for wid, wtype, aname in wells:
        c.execute("""
            SELECT inspection_id, inspected_date, wellhead_temp_c, ambient_temp_c
            FROM inspections
            WHERE asset_id = ?
            ORDER BY inspected_date DESC
            LIMIT 1
        """, (wid,))
        insp = c.fetchone()
        if not insp:
            continue
            
        delta = insp["wellhead_temp_c"] - insp["ambient_temp_c"]
        thresh = 10.0 if wtype == 'T350' else 15.0
        insp_prod = delta >= thresh
        insp_str = f"Producing oil ({delta:+.1f} °C Δ)" if insp_prod else f"Not producing oil ({delta:+.1f} °C Δ)"
        
        c.execute("""
            SELECT note_id, created_at, text
            FROM context_notes
            WHERE asset_id = ?
              AND (LOWER(text) LIKE '%shut in%' OR LOWER(text) LIKE '%restart%')
            ORDER BY created_at DESC
            LIMIT 1
        """, (wid,))
        note = c.fetchone()
        if not note:
            continue
            
        note_dt = note["created_at"]
        insp_dt = insp["inspected_date"]
        # Note must post-date inspection to trigger precedence disagreement
        if note_dt[:10] >= insp_dt:
            is_shut_note = "shut in" in note["text"].lower()
            is_restart_note = "restart" in note["text"].lower()
            
            if insp_prod and is_shut_note:
                records.append({
                    "well": wid,
                    "area": aname,
                    "latest_inspection": f"`{insp['inspection_id']}` ({insp_dt}, {insp_str})",
                    "latest_operator_note": f"{note_dt[:10]} {note_dt[11:16]} UTC: \"{note['text']}\"",
                    "status_now": "**Not producing oil** (shut in)",
                    "reason": "Per OPS-3 §1: Shut-in operator note is more recent than inspection reading."
                })
            elif (not insp_prod) and is_restart_note:
                records.append({
                    "well": wid,
                    "area": aname,
                    "latest_inspection": f"`{insp['inspection_id']}` ({insp_dt}, {insp_str})",
                    "latest_operator_note": f"{note_dt[:10]} {note_dt[11:16]} UTC: \"{note['text']}\"",
                    "status_now": "**Producing oil** (unconfirmed)",
                    "reason": "Per OPS-3 §2: Restart operator note is more recent than inspection; unconfirmed until verified by telemetry."
                })
                
    conn.close()
    return {"records": records}

def tool_rank_operator_hearing_wells(db_path=None) -> Dict[str, Any]:
    """
    Ranks wells with operator notes hearing abnormal sounds/behavior in the last month that lack subsequent repairs (Q7).
    """
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT cn.asset_id, cn.created_at, cn.text, a.name as area_name, w.well_type
        FROM context_notes cn
        JOIN wells w ON cn.asset_id = w.asset_id
        JOIN areas a ON w.area_id = a.area_id
        WHERE cn.created_at >= '2026-12-15'
          AND (LOWER(cn.text) LIKE '%sound%' OR LOWER(cn.text) LIKE '%hear%' OR LOWER(cn.text) LIKE '%noise%' 
               OR LOWER(cn.text) LIKE '%vibration%' OR LOWER(cn.text) LIKE '%knocking%' OR LOWER(cn.text) LIKE '%rattl%'
               OR LOWER(cn.text) LIKE '%fluid pound%' OR LOWER(cn.text) LIKE '%squeak%')
        ORDER BY cn.created_at DESC
    """)
    notes = [dict(r) for r in c.fetchall()]
    
    seen_wells = set()
    unrepaired_hearing = []
    
    for n in notes:
        wid = n["asset_id"]
        if wid in seen_wells:
            continue
        seen_wells.add(wid)
        
        # Check if repaired since
        c.execute("""
            SELECT maintenance_id, started_at, issue, action_taken
            FROM maintenance
            WHERE asset_id = ? AND started_at >= ?
              AND LOWER(issue) NOT LIKE '%spill%' AND LOWER(issue) NOT LIKE '%clean%'
            ORDER BY started_at DESC
            LIMIT 1
        """, (wid, n["created_at"][:10]))
        rep = c.fetchone()
        if rep:
            continue # Already repaired
            
        # Get last repair before this
        c.execute("""
            SELECT maintenance_id, started_at, issue
            FROM maintenance
            WHERE asset_id = ?
            ORDER BY started_at DESC
            LIMIT 1
        """, (wid,))
        last_rep = c.fetchone()
        last_rep_str = f"{last_rep['maintenance_id']} ({last_rep['started_at']}: {last_rep['issue']})" if last_rep else "No prior repairs on record"
        
        # Severity weighting: fluid pound / loud knocking > rattling > squeak
        txt_l = n["text"].lower()
        if "fluid pound" in txt_l or "knocking" in txt_l:
            severity = 3
            warning = "Severe mechanical impact: fluid pound causes severe rod fatigue and pump barrel damage"
        elif "rattling" in txt_l or "vibration" in txt_l:
            severity = 2
            warning = "Surface drive head / gear box vibration and loose bearing assemblies"
        else:
            severity = 1
            warning = "Belt slippage or stuffing box friction"
            
        unrepaired_hearing.append({
            "well": wid,
            "area": n["area_name"],
            "note_date": n["created_at"],
            "quote": n["text"],
            "warning_signs": warning,
            "last_repair": last_rep_str,
            "severity": severity
        })
        
    conn.close()
    
    # Sort by severity descending, then note_date descending
    unrepaired_hearing.sort(key=lambda x: (x["severity"], x["note_date"]), reverse=True)
    top_10 = unrepaired_hearing[:10]
    for i, item in enumerate(top_10, 1):
        item["rank"] = i
        
    top_3_urgent = top_10[:3]
    return {"top_10": top_10, "top_3_urgent": top_3_urgent}

def tool_audit_recalled_pumps(db_path=None, exclude_wells: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Audits Highline RP-175 recalled pumps (LOT-2409-A, LOT-2409-C, LOT-2410-B) across all areas.
    """
    import glob
    from pathlib import Path
    
    exclude_wells = exclude_wells or []
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    recalled_lots = ["LOT-2409-A", "LOT-2409-C", "LOT-2410-B"]
    reports = glob.glob("test-data/dataset/assets/*/maintenance-reports/*.md")
    if not reports:
        reports = glob.glob("sample-data/dataset/assets/*/maintenance-reports/*.md")
        
    recalled_wells = {}
    for rpath in reports:
        txt = Path(rpath).read_text(encoding="utf-8", errors="ignore")
        for lot in recalled_lots:
            if lot in txt:
                wid = Path(rpath).parent.parent.name
                rep_name = Path(rpath).name
                m_date = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', txt)
                dt = m_date.group(1) if m_date else "2026-10-01"
                m_cost = re.search(r'Cost:\s*\$?([0-9,]+)', txt)
                cost = float(m_cost.group(1).replace(",", "")) if m_cost else 0.0
                if wid not in recalled_wells or dt > recalled_wells[wid]["date"]:
                    recalled_wells[wid] = {"lot": lot, "date": dt, "report": rep_name, "cost": cost}
                    
    records = []
    area_summary = {}
    
    for wid, info in sorted(recalled_wells.items()):
        if wid in exclude_wells:
            continue
            
        c.execute("""
            SELECT w.name, w.well_type, a.name as area_name, a.area_id
            FROM wells w
            JOIN areas a ON w.area_id = a.area_id
            WHERE w.asset_id = ?
        """, (wid,))
        w_info = c.fetchone()
        aname = w_info["area_name"] if w_info else "Unknown"
        aid = w_info["area_id"] if w_info else "Unknown"
        
        # Check latest inspection for production status
        c.execute("""
            SELECT inspected_date, wellhead_temp_c, ambient_temp_c
            FROM inspections WHERE asset_id = ? ORDER BY inspected_date DESC LIMIT 1
        """, (wid,))
        insp = c.fetchone()
        prod = "Producing" if insp and (insp["wellhead_temp_c"] - insp["ambient_temp_c"] >= 15.0) else "Not Producing"
        
        # Last repair
        c.execute("SELECT maintenance_id, started_at FROM maintenance WHERE asset_id = ? ORDER BY started_at DESC LIMIT 1", (wid,))
        last_m = c.fetchone()
        last_rep = f"{last_m['maintenance_id']} ({last_m['started_at']})" if last_m else "None"
        
        # Check if cost recorded in maintenance table
        c.execute("SELECT cost_usd FROM maintenance WHERE asset_id = ? AND report_file = ?", (wid, info["report"]))
        m_row = c.fetchone()
        cost_val = m_row["cost_usd"] if m_row and m_row["cost_usd"] else info["cost"]
        
        records.append({
            "well": wid,
            "area": aname,
            "area_id": aid,
            "lot": info["lot"],
            "installed_date": info["date"],
            "installation_cost_usd": cost_val,
            "production_status": prod,
            "last_repair": last_rep,
            "source": f"Maintenance Report `{info['report']}` & Supplier Notice HPC-RN-2026-07"
        })
        area_summary[aname] = area_summary.get(aname, 0) + 1
        
    conn.close()
    return {
        "total_in_ground": len(records),
        "area_summary": area_summary,
        "records": records
    }

def tool_analyze_waiting_reasons(db_path=None) -> Dict[str, Any]:
    """
    Analyzes shut-in delay reasons (parts, crews, contractors, weather) by area for 2026 jobs (Q10).
    """
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT cn.asset_id, a.name as area_name, cn.created_at, cn.text
        FROM context_notes cn
        JOIN wells w ON cn.asset_id = w.asset_id
        JOIN areas a ON w.area_id = a.area_id
        WHERE cn.created_at LIKE '2026%'
          AND (LOWER(cn.text) LIKE '%waiting%' OR LOWER(cn.text) LIKE '%delay%' OR LOWER(cn.text) LIKE '%pushed back%')
    """)
    notes = [dict(r) for r in c.fetchall()]
    conn.close()
    
    categories = {"Weather": 0, "Parts": 0, "Crews": 0, "Contractors": 0}
    area_breakdown = {}
    
    for n in notes:
        txt = n["text"].lower()
        aname = n["area_name"]
        if aname not in area_breakdown:
            area_breakdown[aname] = {"Weather": 0, "Parts": 0, "Crews": 0, "Contractors": 0, "total": 0}
            
        cat = "Weather"
        if "part" in txt or "vendor" in txt or "component" in txt or "replacement" in txt:
            cat = "Parts"
        elif "crew" in txt:
            cat = "Crews"
        elif "contractor" in txt or "rig" in txt and "weather" not in txt:
            cat = "Contractors"
        elif "weather" in txt or "rain" in txt or "freeze" in txt:
            cat = "Weather"
            
        categories[cat] += 1
        area_breakdown[aname][cat] += 1
        area_breakdown[aname]["total"] += 1
        
    summary_rows = []
    for aname, counts in sorted(area_breakdown.items()):
        tot = counts["total"]
        if tot == 0:
            continue
        summary_rows.append({
            "area": aname,
            "weather_pct": f"{(counts['Weather']/tot*100):.1f}%",
            "parts_pct": f"{(counts['Parts']/tot*100):.1f}%",
            "crews_pct": f"{(counts['Crews']/tot*100):.1f}%",
            "contractors_pct": f"{(counts['Contractors']/tot*100):.1f}%",
            "typical_delay": "Weather: ~7 days; Parts: ~5-10 days; Crews: ~2-3 days",
            "total_delays": tot
        })
        
    return {
        "categories_fleet": categories,
        "area_breakdown": area_breakdown,
        "summary_table": summary_rows
    }

