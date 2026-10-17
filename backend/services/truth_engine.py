import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from backend.config import REFERENCE_DATE
from backend.db.database import get_db_connection

def get_well_threshold(conn, well_type: str) -> float:
    c = conn.cursor()
    c.execute("SELECT min_temp_delta_c FROM well_type_rules WHERE well_type = ?", (well_type,))
    row = c.fetchone()
    if row and row["min_temp_delta_c"] is not None:
        return float(row["min_temp_delta_c"])
    return 15.0 if well_type == "T200" else 20.0

def get_effective_inspection(conn, inspection_id: str) -> Optional[Dict[str, Any]]:
    c = conn.cursor()
    c.execute("""
        SELECT i.*, w.well_type, w.recorded_status as well_recorded_status, w.name as well_name,
               u.name as inspector_name
        FROM inspections i
        JOIN wells w ON i.asset_id = w.asset_id
        LEFT JOIN users u ON i.inspector_user_id = u.user_id
        WHERE i.inspection_id = ?
    """, (inspection_id,))
    row = c.fetchone()
    if not row:
        return None
    
    data = dict(row)
    threshold = get_well_threshold(conn, data["well_type"])
    data["threshold_c"] = threshold
    
    # Check for corrections
    c.execute("""
        SELECT * FROM data_corrections 
        WHERE inspection_id = ? 
        ORDER BY created_at DESC
    """, (inspection_id,))
    corrections = [dict(r) for r in c.fetchall()]
    
    raw_wellhead = data["wellhead_temp_c"]
    eff_wellhead = raw_wellhead
    ambient = data["ambient_temp_c"]
    
    raw_spill_detected = data["spill_detected"]
    eff_spill_detected = raw_spill_detected
    
    raw_volume = data["spill_est_volume_bbl"]
    eff_volume = raw_volume
    
    temp_corrected_by = None
    volume_corrected_by = None
    spill_fp_note = None

    for corr in corrections:
        fn = corr["field_name"]
        if fn == "wellhead_temp_c":
            eff_wellhead = float(corr["new_value"])
            temp_corrected_by = corr["author_user_id"]
        elif fn == "spill_est_volume_bbl":
            eff_volume = float(corr["new_value"])
            volume_corrected_by = corr["author_user_id"]
        elif fn == "spill_detected":
            eff_spill_detected = int(corr["new_value"])
            spill_fp_note = corr["reason"]

    data["raw_wellhead_temp_c"] = raw_wellhead
    data["eff_wellhead_temp_c"] = eff_wellhead
    data["is_temp_corrected"] = (eff_wellhead != raw_wellhead)
    data["temp_corrected_by"] = temp_corrected_by

    data["raw_spill_detected"] = raw_spill_detected
    data["eff_spill_detected"] = eff_spill_detected
    data["spill_false_positive_reason"] = spill_fp_note

    data["raw_spill_est_volume_bbl"] = raw_volume
    data["eff_spill_est_volume_bbl"] = eff_volume
    data["is_volume_corrected"] = (eff_volume != raw_volume)
    data["volume_corrected_by"] = volume_corrected_by

    if eff_wellhead is not None and ambient is not None:
        delta = round(eff_wellhead - ambient, 1)
        data["temp_delta_c"] = delta
        data["is_producing"] = (delta >= threshold)
    else:
        data["temp_delta_c"] = None
        data["is_producing"] = False

    # Recorded status out-of-date check
    rec_status = (data["well_recorded_status"] or "").lower()
    is_prod = data["is_producing"]
    if is_prod and rec_status == "down":
        data["is_recorded_status_out_of_date"] = True
    elif not is_prod and rec_status == "active":
        data["is_recorded_status_out_of_date"] = True
    else:
        data["is_recorded_status_out_of_date"] = False

    return data

def get_well_latest_status(asset_id: str, db_path=None) -> Dict[str, Any]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT w.*, a.name as area_name, t.name as team_name, u.name as in_charge_name
        FROM wells w
        LEFT JOIN areas a ON w.area_id = a.area_id
        LEFT JOIN teams t ON w.team_id = t.team_id
        LEFT JOIN users u ON w.in_charge_user_id = u.user_id
        WHERE w.asset_id = ?
    """, (asset_id,))
    well = c.fetchone()
    if not well:
        conn.close()
        raise ValueError(f"Well {asset_id} not found.")

    well_dict = dict(well)
    
    # Get latest inspection
    c.execute("""
        SELECT inspection_id FROM inspections 
        WHERE asset_id = ? 
        ORDER BY inspected_at DESC LIMIT 1
    """, (asset_id,))
    insp_row = c.fetchone()
    
    eff_insp = None
    if insp_row:
        eff_insp = get_effective_inspection(conn, insp_row["inspection_id"])
    
    # Active context notes
    c.execute("""
        SELECT * FROM context_notes 
        WHERE asset_id = ? 
        ORDER BY created_at DESC
    """, (asset_id,))
    context_notes = [dict(r) for r in c.fetchall()]
    
    # Open repairs
    c.execute("""
        SELECT * FROM maintenance 
        WHERE asset_id = ? AND (completed_at IS NULL OR completed_date >= ?)
        ORDER BY started_at DESC
    """, (asset_id, REFERENCE_DATE))
    open_repairs = [dict(r) for r in c.fetchall()]

    # Data corrections on this well
    c.execute("""
        SELECT * FROM data_corrections 
        WHERE asset_id = ? 
        ORDER BY created_at DESC
    """, (asset_id,))
    corrections = [dict(r) for r in c.fetchall()]

    conn.close()
    return {
        "well": well_dict,
        "latest_inspection": eff_insp,
        "context_notes": context_notes,
        "open_repairs": open_repairs,
        "corrections": corrections
    }

def get_non_producing_wells_in_area(area_name_or_id: Optional[str] = None, db_path=None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    area_filter = ""
    params: List[Any] = []
    if area_name_or_id:
        c.execute("SELECT area_id, name FROM areas WHERE area_id = ? OR name LIKE ?", (area_name_or_id, f"%{area_name_or_id}%"))
        a = c.fetchone()
        if a:
            target_area_id = a["area_id"]
            target_area_name = a["name"]
            area_filter = "WHERE w.area_id = ?"
            params.append(target_area_id)
        else:
            conn.close()
            return []

    # Get all wells in scope
    query = f"""
        SELECT w.asset_id, w.name, w.well_type, w.area_id, w.recorded_status, a.name as area_name
        FROM wells w
        JOIN areas a ON w.area_id = a.area_id
        {area_filter}
        ORDER BY w.asset_id ASC
    """
    c.execute(query, params)
    wells = [dict(r) for r in c.fetchall()]
    
    non_producing = []
    for w in wells:
        asset_id = w["asset_id"]
        # Latest inspection
        c.execute("""
            SELECT inspection_id FROM inspections 
            WHERE asset_id = ? 
            ORDER BY inspected_at DESC LIMIT 1
        """, (asset_id,))
        insp_row = c.fetchone()
        if not insp_row:
            continue
        
        eff_insp = get_effective_inspection(conn, insp_row["inspection_id"])
        if not eff_insp:
            continue
            
        if not eff_insp["is_producing"]:
            # Find reason:
            # 1. Open maintenance
            insp_date = eff_insp["inspected_date"]
            c.execute("""
                SELECT * FROM maintenance 
                WHERE asset_id = ? 
                  AND started_date <= ? 
                  AND (completed_date IS NULL OR completed_date >= ?)
                ORDER BY started_at DESC LIMIT 1
            """, (asset_id, insp_date, insp_date))
            maint_row = c.fetchone()
            
            # 2. Context notes explaining shut-in (exclude correction notes)
            c.execute("""
                SELECT * FROM context_notes 
                WHERE asset_id = ? 
                  AND note_type != 'correction'
                  AND (
                      (valid_from IS NOT NULL AND valid_to IS NOT NULL AND valid_from <= ? AND valid_to >= ?)
                      OR (valid_from <= ? AND (valid_to IS NULL OR valid_to >= ?) AND (
                          text LIKE '%shut in%' OR text LIKE '%workover%' OR text LIKE '%down%' OR text LIKE '%maintenance%'
                      ))
                  )
                ORDER BY created_at DESC LIMIT 1
            """, (asset_id, insp_date, insp_date, insp_date, insp_date))
            ctx_row = c.fetchone()
            
            reason = "No recorded reason"
            citation = ""
            
            if maint_row:
                m = dict(maint_row)
                st_date = datetime.strptime(m["started_date"], "%Y-%m-%d").strftime("%d %b")
                issue_text = (m.get('issue') or '').lower()
                eq_kind = (m.get('equipment_kind') or '').replace('_', ' ')
                reason = f"Repair {m['maintenance_id']}, {eq_kind} {issue_text}, started {st_date}, still open"
                citation = m["maintenance_id"]
            elif ctx_row:
                ctx = dict(ctx_row)
                reason = ctx["text"]
                citation = ctx["note_id"]
            
            inspector_notes = eff_insp.get("notes") or ""
            
            non_producing.append({
                "asset_id": asset_id,
                "name": w["name"],
                "well_type": w["well_type"],
                "temp_delta_c": eff_insp["temp_delta_c"],
                "threshold_c": eff_insp["threshold_c"],
                "wellhead_temp_c": eff_insp["eff_wellhead_temp_c"],
                "ambient_temp_c": eff_insp["ambient_temp_c"],
                "recorded_status": w["recorded_status"],
                "is_recorded_status_out_of_date": eff_insp["is_recorded_status_out_of_date"],
                "reason": reason,
                "inspector_notes": inspector_notes,
                "inspection_id": eff_insp["inspection_id"],
                "inspected_date": eff_insp["inspected_date"],
                "citation": citation
            })
            
    conn.close()
    return non_producing

def get_well_temperature_series(asset_id: str, last_n_weeks: int = 13, db_path=None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT inspection_id FROM inspections 
        WHERE asset_id = ? 
        ORDER BY inspected_at DESC LIMIT ?
    """, (asset_id, last_n_weeks))
    rows = c.fetchall()
    
    series = []
    for r in reversed(rows):
        eff = get_effective_inspection(conn, r["inspection_id"])
        if eff:
            series.append({
                "inspection_id": eff["inspection_id"],
                "inspected_date": eff["inspected_date"],
                "wellhead_temp_c": eff["eff_wellhead_temp_c"],
                "ambient_temp_c": eff["ambient_temp_c"],
                "temp_delta_c": eff["temp_delta_c"],
                "threshold_c": eff["threshold_c"],
                "is_producing": eff["is_producing"]
            })
    conn.close()
    return series

def calculate_well_downtime(asset_id: str, start_date: str, end_date: str, db_path=None) -> Dict[str, Any]:
    """
    Downtime counting rule:
    Each inspection finding well not producing = 7 days downtime.
    Attribute to matching repair or context note.
    """
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT inspection_id FROM inspections 
        WHERE asset_id = ? AND inspected_date >= ? AND inspected_date <= ?
        ORDER BY inspected_at ASC
    """, (asset_id, start_date, end_date))
    rows = c.fetchall()
    
    non_producing_count = 0
    non_producing_inspections = []
    
    for r in rows:
        eff = get_effective_inspection(conn, r["inspection_id"])
        if eff and not eff["is_producing"]:
            non_producing_count += 1
            # Find cause
            idate = eff["inspected_date"]
            c.execute("""
                SELECT maintenance_id, issue, started_date, completed_date 
                FROM maintenance 
                WHERE asset_id = ? AND started_date <= ? AND (completed_date IS NULL OR completed_date >= ?)
                ORDER BY started_at DESC LIMIT 1
            """, (asset_id, idate, idate))
            maint = c.fetchone()
            
            c.execute("""
                SELECT note_id, text FROM context_notes
                WHERE asset_id = ? AND (valid_from IS NULL OR valid_from <= ?) AND (valid_to IS NULL OR valid_to >= ?)
                ORDER BY created_at DESC LIMIT 1
            """, (asset_id, idate, idate))
            ctx = c.fetchone()
            
            non_producing_inspections.append({
                "inspection_id": eff["inspection_id"],
                "inspected_date": idate,
                "wellhead_temp_c": eff["eff_wellhead_temp_c"],
                "ambient_temp_c": eff["ambient_temp_c"],
                "temp_delta_c": eff["temp_delta_c"],
                "threshold_c": eff["threshold_c"],
                "maintenance": dict(maint) if maint else None,
                "context": dict(ctx) if ctx else None
            })
            
    total_downtime_days = non_producing_count * 7
    conn.close()
    return {
        "asset_id": asset_id,
        "start_date": start_date,
        "end_date": end_date,
        "non_producing_count": non_producing_count,
        "downtime_days": total_downtime_days,
        "inspections": non_producing_inspections
    }

def calculate_area_top_downtime(area_name_or_id: str, start_date: str, end_date: str, top_k: int = 3, db_path=None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT area_id, name FROM areas WHERE area_id = ? OR name LIKE ?", (area_name_or_id, f"%{area_name_or_id}%"))
    area = c.fetchone()
    if not area:
        conn.close()
        return []
        
    area_id = area["area_id"]
    c.execute("SELECT asset_id, name, well_type FROM wells WHERE area_id = ?", (area_id,))
    wells = [dict(r) for r in c.fetchall()]
    conn.close()
    
    results = []
    for w in wells:
        dt = calculate_well_downtime(w["asset_id"], start_date, end_date, db_path)
        results.append({
            "asset_id": w["asset_id"],
            "name": w["name"],
            "well_type": w["well_type"],
            "downtime_days": dt["downtime_days"],
            "non_producing_count": dt["non_producing_count"]
        })
        
    results.sort(key=lambda x: x["downtime_days"], reverse=True)
    return results[:top_k]

def query_spills(asset_id: Optional[str] = None,
                 area_name_or_id: Optional[str] = None,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 only_reportable: bool = False,
                 only_late_containment: bool = False,
                 db_path=None) -> Dict[str, Any]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    well_ids = []
    if asset_id:
        well_ids = [asset_id]
    elif area_name_or_id:
        c.execute("SELECT area_id FROM areas WHERE area_id = ? OR name LIKE ?", (area_name_or_id, f"%{area_name_or_id}%"))
        a = c.fetchone()
        if a:
            c.execute("SELECT asset_id FROM wells WHERE area_id = ?", (a["area_id"],))
            well_ids = [r["asset_id"] for r in c.fetchall()]
    else:
        c.execute("SELECT asset_id FROM wells")
        well_ids = [r["asset_id"] for r in c.fetchall()]

    confirmed_spills = []
    excluded_false_positives = []
    total_volume_bbl = 0.0

    for wid in well_ids:
        # Check inspections with raw spill_detected = 1 or volume > 0
        q = "SELECT inspection_id FROM inspections WHERE asset_id = ? AND (spill_detected = 1 OR spill_est_volume_bbl > 0)"
        params: List[Any] = [wid]
        if start_date:
            q += " AND inspected_date >= ?"
            params.append(start_date)
        if end_date:
            q += " AND inspected_date <= ?"
            params.append(end_date)
            
        c.execute(q, params)
        for row in c.fetchall():
            eff = get_effective_inspection(conn, row["inspection_id"])
            if not eff:
                continue
                
            # If false positive (corrected spill_detected == 0)
            if eff["eff_spill_detected"] == 0:
                excluded_false_positives.append({
                    "inspection_id": eff["inspection_id"],
                    "asset_id": eff["asset_id"],
                    "inspected_date": eff["inspected_date"],
                    "reason": eff.get("spill_false_positive_reason") or "Corrected as false positive"
                })
                continue
                
            # Confirmed spill
            vol = eff["eff_spill_est_volume_bbl"] or 0.0
            if only_reportable and vol < 5.0:
                continue
                
            # Get well info
            c.execute("SELECT name, lat, lon, area_id FROM wells WHERE asset_id = ?", (eff["asset_id"],))
            w_info = dict(c.fetchone() or {})
            
            # Get repair report if any
            c.execute("""
                SELECT m.maintenance_id, mr.containment_hours, mr.spill_class_listed, mr.report_file
                FROM maintenance m
                LEFT JOIN maintenance_reports mr ON m.maintenance_id = mr.maintenance_id
                WHERE m.triggered_by_inspection_id = ? OR m.asset_id = ? AND m.started_date = ?
                LIMIT 1
            """, (eff["inspection_id"], eff["asset_id"], eff["inspected_date"]))
            m_rep = c.fetchone()
            
            containment_hours = m_rep["containment_hours"] if m_rep else None
            if only_late_containment and (containment_hours is None or containment_hours <= 4.0):
                continue
                
            total_volume_bbl += vol
            confirmed_spills.append({
                "asset_id": eff["asset_id"],
                "well_name": w_info.get("name"),
                "lat": w_info.get("lat"),
                "lon": w_info.get("lon"),
                "area_id": w_info.get("area_id"),
                "inspection_id": eff["inspection_id"],
                "inspected_date": eff["inspected_date"],
                "spill_est_volume_bbl": round(vol, 1),
                "spill_area_pct": eff.get("spill_area_pct"),
                "containment_hours": containment_hours,
                "maintenance_id": m_rep["maintenance_id"] if m_rep else None,
                "report_file": m_rep["report_file"] if m_rep else None
            })

    confirmed_spills.sort(key=lambda x: x["inspected_date"])
    conn.close()
    return {
        "spill_count": len(confirmed_spills),
        "total_volume_bbl": round(total_volume_bbl, 1),
        "spills": confirmed_spills,
        "excluded_false_positives": excluded_false_positives
    }

def get_spills_heatmap_2026(year: int = 2026, db_path=None) -> Dict[str, Any]:
    """
    Builds the exact Area Name x Month (Jan..Oct) matrix + Total column
    with corrected false positives removed.
    """
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("SELECT area_id, name FROM areas ORDER BY area_id")
    areas = [dict(r) for r in c.fetchall()]
    
    # Months 1 to 10
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    matrix = {}
    
    for a in areas:
        matrix[a["name"]] = {m: 0 for m in months}
        matrix[a["name"]]["Total"] = 0

    # Query all spills in year
    spills_res = query_spills(start_date=f"{year}-01-01", end_date=f"{year}-10-17", db_path=db_path)
    
    # Map area_id to name
    area_map = {a["area_id"]: a["name"] for a in areas}
    
    for s in spills_res["spills"]:
        aname = area_map.get(s["area_id"])
        if not aname:
            continue
        idate = s["inspected_date"]
        m_num = int(idate[5:7])
        if 1 <= m_num <= 10:
            m_name = months[m_num - 1]
            matrix[aname][m_name] += 1
            matrix[aname]["Total"] += 1

    conn.close()
    return {
        "year": year,
        "months": months,
        "matrix": matrix
    }
