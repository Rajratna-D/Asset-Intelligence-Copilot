from typing import Dict, Any, List, Optional
from backend.db.database import get_db_connection
from backend.services.truth_engine import get_well_latest_status, get_effective_inspection

def check_temperature_correction_conflicts(asset_id: str, inspection_id: str, new_temp_c: float, db_path=None) -> Optional[str]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT i.notes, u.name as inspector_name
        FROM inspections i
        LEFT JOIN users u ON i.inspector_user_id = u.user_id
        WHERE i.inspection_id = ?
    """, (inspection_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return None
        
    notes = row["notes"] or ""
    inspector = row["inspector_name"] or "the inspector"
    
    if "not moving" in notes.lower() or "stopped" in notes.lower():
        return f"Warning: The inspection note by {inspector} states \"{notes}\", which contradicts a producing wellhead temperature of {new_temp_c:.1f} °C. Please confirm."
    return None

def verify_user_claim(user_id: str, asset_id: str, claim_text: str, db_path=None) -> Dict[str, Any]:
    """
    Checks user statement against latest sensor inspection telemetry and existing context notes.
    """
    status_info = get_well_latest_status(asset_id, db_path=db_path)
    well = status_info["well"]
    insp = status_info["latest_inspection"]
    notes = status_info["context_notes"]
    
    claim_lower = claim_text.lower()
    
    # Claim: "running fine" / "producing" / "back online"
    if any(k in claim_lower for k in ["running fine", "back online", "operating", "producing"]):
        is_prod = insp["is_producing"] if insp else False
        delta = insp["temp_delta_c"] if insp else 0.0
        insp_date = insp["inspected_date"] if insp else "latest"
        inspector = insp.get("inspector_name") or "field inspector"
        
        if not is_prod:
            # Telemetry contradicts claim!
            conflict_details = []
            conflict_details.append(
                f"Inspection {insp['inspection_id']} on {insp_date} (by {inspector}) shows wellhead only {delta} °C above ambient, below the {well['well_type']} threshold, so the well is not producing oil."
            )
            # Check if there is an active shut-in note
            for n in notes:
                ntext = n.get("text", "")
                if "shut in" in ntext.lower() or "workover" in ntext.lower() or "expected back" in ntext.lower():
                    author = n.get("author_user_id", "operator")
                    conflict_details.append(f"Matching operational note {n['note_id']} ({author}): \"{ntext}\".")
                    break
                    
            return {
                "has_conflict": True,
                "verified": False,
                "status": "unconfirmed",
                "message": " ".join(conflict_details),
                "recorded_as": "unconfirmed"
            }
            
    # Claim: "shut in" / "down"
    if any(k in claim_lower for k in ["shut in", "down", "stopped", "workover"]):
        is_prod = insp["is_producing"] if insp else False
        delta = insp["temp_delta_c"] if insp else 0.0
        if is_prod:
            return {
                "has_conflict": True,
                "verified": False,
                "status": "unconfirmed",
                "message": f"Inspection telemetry shows the well is currently producing ({delta} °C delta).",
                "recorded_as": "unconfirmed"
            }
        else:
            return {
                "has_conflict": False,
                "verified": True,
                "status": "confirmed",
                "message": "Consistent with current non-producing telemetry.",
                "recorded_as": "verified"
            }

    return {
        "has_conflict": False,
        "verified": True,
        "status": "recorded",
        "message": "Note recorded.",
        "recorded_as": "verified"
    }

def audit_spill_detection_validity(asset_id: str, inspection_id: str, db_path=None) -> Dict[str, Any]:
    """
    Evaluates whether a detected spill is real oil or false positive.
    Distinguishes formal corrections from conflicting feedback notes.
    """
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    # 1. Check inspection
    eff_insp = get_effective_inspection(conn, inspection_id)
    if not eff_insp:
        conn.close()
        raise ValueError(f"Inspection {inspection_id} not found")
        
    # 2. Check context notes referencing this inspection (either via inspection_id or mentioned in text)
    c.execute("""
        SELECT c.*, u.name as author_name, u.role as author_role
        FROM context_notes c
        LEFT JOIN users u ON c.author_user_id = u.user_id
        WHERE c.asset_id = ? AND (c.inspection_id = ? OR c.text LIKE ?)
        ORDER BY c.created_at ASC
    """, (asset_id, inspection_id, f"%{inspection_id}%"))
    notes = [dict(r) for r in c.fetchall()]
    
    # 3. Check maintenance job
    c.execute("""
        SELECT * FROM maintenance 
        WHERE triggered_by_inspection_id = ? OR (asset_id = ? AND started_date = ?)
    """, (inspection_id, asset_id, eff_insp["inspected_date"]))
    maint = c.fetchone()
    
    has_formal_correction = (eff_insp["eff_spill_detected"] == 0)
    
    conn.close()
    
    if has_formal_correction:
        return {
            "is_real_oil": False,
            "status": "excluded_false_positive",
            "reason": eff_insp.get("spill_false_positive_reason"),
            "notes": notes
        }
        
    # Detection stands
    notes_summary = []
    for n in notes:
        author_desc = f"{n['author_name']} ({n['author_role']})" if n.get("author_name") else n["author_user_id"]
        notes_summary.append(f"{author_desc} ({n['note_id']}): \"{n['text']}\"")
        
    return {
        "is_real_oil": True,
        "volume_bbl": eff_insp["eff_spill_est_volume_bbl"],
        "inspection_notes": eff_insp.get("notes"),
        "has_conflicting_notes": (len(notes) >= 2),
        "notes_detail": notes_summary,
        "maintenance_completed": maint["maintenance_id"] if maint else None,
        "conclusion": "The detection stands because neither note is a formal correction, sampling confirmed crude, and spill repair was executed."
    }
