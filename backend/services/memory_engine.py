import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.config import REFERENCE_DATE
from backend.db.database import get_db_connection

def record_data_correction(
    user_id: str,
    target_type: str,
    asset_id: str,
    inspection_id: Optional[str],
    field_name: str,
    new_value: str,
    reason: str,
    conflict_warning: Optional[str] = None,
    db_path=None
) -> Dict[str, Any]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    # Whitelist allowed inspection fields to strictly prevent SQL injection
    ALLOWED_INSPECTION_FIELDS = {
        "wellhead_temp_c", "ambient_temp_c", "spill_detected",
        "spill_est_volume_bbl", "inspector_notes", "optical_gas_imaging"
    }

    # Get old value if available
    old_value = None
    if inspection_id:
        if field_name not in ALLOWED_INSPECTION_FIELDS:
            raise ValueError(f"Security Alert: Disallowed field name '{field_name}'. Potential SQL injection rejected.")
        c.execute(f"SELECT {field_name} FROM inspections WHERE inspection_id = ?", (inspection_id,))
        row = c.fetchone()
        if row and row[field_name] is not None:
            old_value = str(row[field_name])
            
    corr_id = f"CORR-{uuid.uuid4().hex[:8]}"
    created_at = f"{REFERENCE_DATE}T10:00:00Z"
    
    c.execute("""
        INSERT INTO data_corrections 
        (correction_id, target_type, asset_id, inspection_id, field_name, old_value, new_value, reason, author_user_id, created_at, conflict_warning)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (corr_id, target_type, asset_id, inspection_id, field_name, old_value, str(new_value), reason, user_id, created_at, conflict_warning))
    
    conn.commit()
    conn.close()
    return {
        "correction_id": corr_id,
        "asset_id": asset_id,
        "inspection_id": inspection_id,
        "field_name": field_name,
        "old_value": old_value,
        "new_value": str(new_value),
        "author_user_id": user_id,
        "reason": reason,
        "conflict_warning": conflict_warning
    }

def record_rule_override(
    user_id: str,
    scope_type: str,
    scope_value: str,
    equipment_kind: Optional[str],
    rule_key: str,
    new_value: float,
    description: str,
    db_path=None
) -> Dict[str, Any]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    # Get old value
    old_value = 3.0
    c.execute("SELECT rca_corrective_count FROM well_type_rules WHERE well_type = ?", (scope_value,))
    r = c.fetchone()
    if r and r["rca_corrective_count"] is not None:
        old_value = float(r["rca_corrective_count"])
        
    override_id = f"RULE-{uuid.uuid4().hex[:8]}"
    created_at = f"{REFERENCE_DATE}T10:00:00Z"
    
    c.execute("""
        INSERT INTO rule_overrides
        (override_id, scope_type, scope_value, equipment_kind, rule_key, old_value, new_value, author_user_id, created_at, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (override_id, scope_type, scope_value, equipment_kind, rule_key, old_value, float(new_value), user_id, created_at, description))
    
    conn.commit()
    conn.close()
    return {
        "override_id": override_id,
        "scope_type": scope_type,
        "scope_value": scope_value,
        "equipment_kind": equipment_kind,
        "rule_key": rule_key,
        "old_value": old_value,
        "new_value": float(new_value),
        "author_user_id": user_id,
        "description": description
    }

def record_shared_note(
    user_id: str,
    asset_id: str,
    text: str,
    valid_from: Optional[str] = None,
    valid_to: Optional[str] = None,
    note_type: str = "operator_note",
    db_path=None
) -> Dict[str, Any]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    note_id = f"CTX-{uuid.uuid4().hex[:8]}"
    created_at = f"{REFERENCE_DATE}T08:00:00Z"
    
    c.execute("""
        INSERT INTO context_notes
        (note_id, asset_id, created_at, author_user_id, note_type, inspection_id, text, valid_from, valid_to, source, verification_status)
        VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?, 'user', 'verified')
    """, (note_id, asset_id, created_at, user_id, note_type, text, valid_from, valid_to))
    
    conn.commit()
    conn.close()
    return {
        "note_id": note_id,
        "asset_id": asset_id,
        "author_user_id": user_id,
        "text": text,
        "valid_from": valid_from,
        "valid_to": valid_to
    }

def save_private_chat_message(
    session_id: str,
    user_id: str,
    role: str,
    content: str,
    entities_discussed: Optional[List[str]] = None,
    visual: Optional[Dict[str, Any]] = None,
    citations: Optional[List[str]] = None,
    db_path=None
) -> str:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    # Ensure session exists
    c.execute("SELECT session_id FROM private_chat_sessions WHERE session_id = ?", (session_id,))
    if not c.fetchone():
        c.execute("""
            INSERT INTO private_chat_sessions (session_id, user_id, title, created_at, updated_at)
            VALUES (?, ?, 'Chat Session', datetime('now'), datetime('now'))
        """, (session_id, user_id))
        
    msg_id = f"MSG-{uuid.uuid4().hex[:8]}"
    entities_json = json.dumps(entities_discussed or [])
    visual_json = json.dumps(visual) if visual else None
    citations_json = json.dumps(citations or [])
    
    c.execute("""
        INSERT INTO private_chat_messages
        (message_id, session_id, user_id, role, content, entities_discussed_json, visual_json, citations_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (msg_id, session_id, user_id, role, content, entities_json, visual_json, citations_json))
    
    conn.commit()
    conn.close()
    return msg_id

def get_user_recent_discussed_wells(user_id: str, exclude_session_id: Optional[str] = None, db_path=None) -> List[str]:
    """
    Retrieves the list of wells discussed in prior sessions strictly for the given user_id.
    """
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    query = """
        SELECT entities_discussed_json 
        FROM private_chat_messages 
        WHERE user_id = ? 
    """
    params = [user_id]
    if exclude_session_id:
        query += " AND session_id != ?"
        params.append(exclude_session_id)
        
    query += " ORDER BY created_at DESC"
    
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    
    discussed_wells = []
    for r in rows:
        val = r["entities_discussed_json"]
        if val:
            try:
                items = json.loads(val)
                for item in items:
                    if item.startswith("WELL-") and item not in discussed_wells:
                        discussed_wells.append(item)
            except Exception:
                pass
    return discussed_wells

def get_well_repair_costs_for_year(well_ids: List[str], year: int = 2026, db_path=None) -> Dict[str, Any]:
    conn = get_db_connection(db_path)
    c = conn.cursor()
    
    costs = {}
    total = 0.0
    for wid in well_ids:
        c.execute("""
            SELECT SUM(cost_total_usd) as total_cost
            FROM maintenance 
            WHERE asset_id = ? AND started_date >= ? AND started_date <= ?
        """, (wid, f"{year}-01-01", f"{year}-12-31"))
        row = c.fetchone()
        cost_val = round(float(row["total_cost"] or 0.0), 0)
        costs[wid] = int(cost_val)
        total += cost_val
        
    conn.close()
    return {
        "year": year,
        "well_costs": costs,
        "total_cost": int(total)
    }
