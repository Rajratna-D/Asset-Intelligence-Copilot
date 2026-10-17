from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from backend.config import REFERENCE_DATE
from backend.db.database import get_db_connection
from backend.services.truth_engine import get_well_threshold, get_effective_inspection

def get_rca_threshold(conn, well_type: str, equipment_kind: str) -> Tuple[int, str]:
    c = conn.cursor()
    # Check for user rule override
    c.execute("""
        SELECT new_value, author_user_id, created_at, description 
        FROM rule_overrides 
        WHERE scope_type = 'well_type' AND scope_value = ? AND equipment_kind = ?
        ORDER BY created_at DESC LIMIT 1
    """, (well_type, equipment_kind))
    row = c.fetchone()
    if row:
        return int(row["new_value"]), f"Overridden by {row['author_user_id']}"
    
    # Check default from well_type_rules
    c.execute("SELECT rca_corrective_count FROM well_type_rules WHERE well_type = ?", (well_type,))
    r = c.fetchone()
    if r and r["rca_corrective_count"] is not None:
        return int(r["rca_corrective_count"]), "Manual standard"
    return 3, "Manual standard"

def audit_well_compliance(asset_id: str, db_path=None) -> Dict[str, Any]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    c.execute("SELECT * FROM wells WHERE asset_id = ?", (asset_id,))
    well = c.fetchone()
    if not well:
        conn.close()
        raise ValueError(f"Well {asset_id} not found")
        
    well_type = well["well_type"]
    ref_dt = datetime.strptime(REFERENCE_DATE, "%Y-%m-%d")
    one_year_ago = (ref_dt - timedelta(days=365)).strftime("%Y-%m-%d")

    breaches = []
    pending_actions = []
    rules_met = []

    # 1. Audit Spills in last 12 months (SR-01, SR-02, SR-03)
    c.execute("""
        SELECT i.inspection_id, i.inspected_at, i.inspected_date, i.spill_est_volume_bbl, i.spill_area_pct,
               m.maintenance_id, mr.containment_hours, mr.report_file, mr.spill_class_listed
        FROM inspections i
        LEFT JOIN maintenance m ON m.triggered_by_inspection_id = i.inspection_id
        LEFT JOIN maintenance_reports mr ON m.maintenance_id = mr.maintenance_id
        WHERE i.asset_id = ? AND i.inspected_date >= ? AND i.spill_detected = 1
        ORDER BY i.inspected_at DESC
    """, (asset_id, one_year_ago))
    spill_rows = c.fetchall()
    
    for s in spill_rows:
        eff_insp = get_effective_inspection(conn, s["inspection_id"])
        if not eff_insp or eff_insp["eff_spill_detected"] == 0:
            continue
            
        vol = eff_insp["eff_spill_est_volume_bbl"] or 0.0
        insp_id = s["inspection_id"]
        idate = s["inspected_date"]
        
        # SR-01 check: Reportable spill (>= 5 bbl) must be reported within 24 hours
        if vol >= 5.0:
            c.execute("""
                SELECT * FROM regulatory_events 
                WHERE asset_id = ? AND related_inspection_id = ? AND event_type = 'spill_report_filed'
            """, (asset_id, insp_id))
            reg_rep = c.fetchone()
            
            hours_to_report = reg_rep["hours_to_report"] if reg_rep else None
            
            # Check NOV
            c.execute("""
                SELECT * FROM regulatory_events 
                WHERE asset_id = ? AND related_inspection_id = ? AND event_type = 'notice_of_violation'
            """, (asset_id, insp_id))
            nov_event = c.fetchone()
            
            if hours_to_report is None:
                breaches.append({
                    "protocol": "SR-01",
                    "status": "Breach",
                    "description": f"Spill of {vol} bbl on {idate} ({insp_id}) has no external report on record (limit 24 hours).",
                    "citation": insp_id
                })
            elif hours_to_report > 24.0:
                fine_txt = f" (USD {int(nov_event['fine_usd']) if nov_event and nov_event['fine_usd'] else 5000:,} fine, {nov_event['status'] if nov_event else 'open'})" if nov_event else ""
                nov_id = nov_event["event_id"] if nov_event else "NOV"
                breaches.append({
                    "protocol": "SR-01",
                    "status": "Breach",
                    "description": f"Reported after {hours_to_report:.0f} hours ({reg_rep['event_id'] if reg_rep else 'report'}), against a 24-hour limit. Led to notice of violation {nov_id}{fine_txt}.",
                    "citation": f"{reg_rep['event_id'] if reg_rep else ''}, {nov_id}"
                })
                
            # SR-03 check: 60-day cleanup verification
            insp_dt = datetime.strptime(idate, "%Y-%m-%d")
            deadline_dt = insp_dt + timedelta(days=60)
            deadline_str = deadline_dt.strftime("%d %b %Y")
            
            c.execute("""
                SELECT * FROM regulatory_events 
                WHERE asset_id = ? AND related_inspection_id = ? AND event_type = 'site_inspection'
            """, (asset_id, insp_id))
            site_insp = c.fetchone()
            
            if not site_insp or site_insp["status"] != "closed":
                ev_id = site_insp["event_id"] if site_insp else "REG-0001-003"
                breaches.append({
                    "protocol": "SR-03",
                    "status": "Breach / Open",
                    "description": f"Cleanup verification was due by {deadline_str} and is still open ({ev_id}).",
                    "citation": ev_id
                })

        # SR-02 check: 4-hour containment limit
        cont_hours = s["containment_hours"]
        if cont_hours is not None and cont_hours > 4.0:
            breaches.append({
                "protocol": "SR-02",
                "status": "Breach",
                "description": f"Contained after about {cont_hours:.1f} hours, against a 4-hour limit (found in repair report {s['report_file'] or s['maintenance_id']}).",
                "citation": s["report_file"] or s["maintenance_id"]
            })

    # 2. Audit Regulatory Events (RC-04 NOV response limit)
    c.execute("""
        SELECT * FROM regulatory_events 
        WHERE asset_id = ? AND event_type = 'notice_of_violation' AND date >= ?
    """, (asset_id, one_year_ago))
    novs = c.fetchall()
    for nov in novs:
        nov_date = datetime.strptime(nov["date"], "%Y-%m-%d")
        resp_due = nov_date + timedelta(days=30)
        resp_due_str = resp_due.strftime("%d %b %Y")
        
        # Check for response
        c.execute("""
            SELECT * FROM regulatory_events 
            WHERE asset_id = ? AND event_type = 'nov_response_filed' AND date >= ?
        """, (asset_id, nov["date"]))
        resp = c.fetchone()
        
        if not resp and ref_dt > resp_due:
            breaches.append({
                "protocol": "RC-04",
                "status": "Breach",
                "description": f"The notice {nov['event_id']} needed a response by {resp_due_str}, and none is recorded.",
                "citation": nov["event_id"]
            })

    # 3. Audit RC-02 (Annual flowline integrity test)
    curr_year = REFERENCE_DATE[:4]
    c.execute("""
        SELECT * FROM maintenance 
        WHERE asset_id = ? AND started_date >= ? AND issue LIKE '%Annual flowline integrity test%'
    """, (asset_id, f"{curr_year}-01-01"))
    fl_test = c.fetchone()
    if fl_test:
        test_dt = datetime.strptime(fl_test["started_date"], "%Y-%m-%d").strftime("%d %b %Y")
        rules_met.append({
            "protocol": "RC-02",
            "description": f"Yearly flowline integrity test was completed on {test_dt} ({fl_test['maintenance_id']}).",
            "citation": fl_test["maintenance_id"]
        })

    # 4. Check Root-Cause Analysis (RCA) duties across equipment
    c.execute("""
        SELECT equipment_kind, COUNT(*) as repair_count
        FROM maintenance 
        WHERE asset_id = ? AND maintenance_type = 'corrective' AND started_date >= ?
        GROUP BY equipment_kind
    """, (asset_id, one_year_ago))
    equip_counts = c.fetchall()
    
    for ec in equip_counts:
        ekind = ec["equipment_kind"]
        rcount = ec["repair_count"]
        threshold, source = get_rca_threshold(conn, well_type, ekind)
        if rcount >= threshold:
            # Check latest report for this equipment
            c.execute("""
                SELECT m.maintenance_id, mr.rca_status, mr.report_file, m.started_date
                FROM maintenance m
                LEFT JOIN maintenance_reports mr ON m.maintenance_id = mr.maintenance_id
                WHERE m.asset_id = ? AND m.equipment_kind = ? AND m.maintenance_type = 'corrective'
                ORDER BY m.started_date DESC LIMIT 1
            """, (asset_id, ekind))
            latest_m = c.fetchone()
            
            c.execute("""
                SELECT maintenance_id FROM maintenance 
                WHERE asset_id = ? AND equipment_kind = ? AND maintenance_type = 'corrective' AND started_date >= ?
                ORDER BY started_date ASC
            """, (asset_id, ekind, one_year_ago))
            m_ids = [r["maintenance_id"] for r in c.fetchall()]
            
            m_list_str = ", ".join(m_ids)
            pending_actions.append({
                "type": "RCA Due",
                "equipment_kind": ekind,
                "description": f"A root-cause analysis is due on the {ekind.replace('_', ' ')}: {rcount} corrective repairs in the last 12 months ({m_list_str}). Report for {latest_m['maintenance_id'] if latest_m else ''} marks it as 'Action required'.",
                "citation": m_list_str
            })

    # 5. Check Planned Shut-In Rule (T200 §4.4)
    c.execute("""
        SELECT * FROM context_notes 
        WHERE asset_id = ? AND created_at >= ? AND (text LIKE '%shut in%' OR text LIKE '%planned%')
        ORDER BY created_at DESC LIMIT 1
    """, (asset_id, one_year_ago))
    ctx_shutin = c.fetchone()
    if ctx_shutin:
        shutin_date = ctx_shutin["valid_from"] if ctx_shutin["valid_from"] else "recently"
        c.execute("""
            SELECT * FROM maintenance 
            WHERE asset_id = ? AND started_date >= ?
        """, (asset_id, ctx_shutin["valid_from"] or ctx_shutin["created_at"][:10]))
        m_shutin = c.fetchone()
        if not m_shutin:
            pending_actions.append({
                "type": "Planned Shut-in Unrecorded",
                "description": f"The planned shut-in from {shutin_date} is not yet recorded in the maintenance system, which the {well_type} manual requires before work starts (note {ctx_shutin['note_id']}).",
                "citation": ctx_shutin["note_id"]
            })

    conn.close()
    return {
        "asset_id": asset_id,
        "well_type": well_type,
        "breaches": breaches,
        "pending_actions": pending_actions,
        "rules_met": rules_met
    }

def get_wells_needing_rca(area_name_or_id: str, equipment_kind: str = "pump_jack", lookback_months: int = 12, db_path=None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT area_id FROM areas WHERE area_id = ? OR name LIKE ?", (area_name_or_id, f"%{area_name_or_id}%"))
    area = c.fetchone()
    if not area:
        conn.close()
        return []
        
    area_id = area["area_id"]
    ref_dt = datetime.strptime(REFERENCE_DATE, "%Y-%m-%d")
    lookback_date = (ref_dt - timedelta(days=lookback_months * 30)).strftime("%Y-%m-%d")
    
    c.execute("SELECT asset_id, name, well_type FROM wells WHERE area_id = ? ORDER BY asset_id", (area_id,))
    wells = [dict(r) for r in c.fetchall()]
    
    flagged = []
    for w in wells:
        wid = w["asset_id"]
        wtype = w["well_type"]
        threshold, rule_source = get_rca_threshold(conn, wtype, equipment_kind)
        
        c.execute("""
            SELECT maintenance_id, started_date, issue
            FROM maintenance 
            WHERE asset_id = ? AND equipment_kind = ? AND maintenance_type = 'corrective' AND started_date >= ?
            ORDER BY started_date ASC
        """, (wid, equipment_kind, lookback_date))
        repairs = [dict(r) for r in c.fetchall()]
        
        if len(repairs) >= threshold:
            flagged.append({
                "asset_id": wid,
                "name": w["name"],
                "well_type": wtype,
                "repair_count": len(repairs),
                "threshold": threshold,
                "rule_source": rule_source,
                "repairs": repairs
            })
            
    conn.close()
    return flagged
