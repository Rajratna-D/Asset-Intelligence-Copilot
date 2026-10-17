import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.db.database import get_db_connection

logger = logging.getLogger(__name__)

def log_security_event(
    event_type: str,
    severity: str,
    user_id: str,
    session_id: str,
    details: Dict[str, Any],
    db_path=None
) -> Optional[str]:
    """
    Logs security incidents, guardrail interventions, and audited state changes
    to the immutable security audit table.
    """
    try:
        conn = get_db_connection(db_path)
        c = conn.cursor()
        event_id = f"SEC-{uuid.uuid4().hex[:10]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        c.execute("""
            INSERT INTO security_audit_logs 
            (event_id, timestamp, user_id, session_id, event_type, severity, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            timestamp,
            user_id,
            session_id,
            event_type,
            severity,
            json.dumps(details)
        ))
        conn.commit()
        conn.close()
        logger.info(f"Security event recorded: {event_type} [{severity}] by {user_id}")
        return event_id
    except Exception as e:
        logger.error(f"Failed to record security event: {e}")
        return None

def get_recent_security_events(limit: int = 50, db_path=None) -> List[Dict[str, Any]]:
    """
    Retrieves recent security incidents and audit events for compliance review.
    """
    try:
        conn = get_db_connection(db_path)
        c = conn.cursor()
        c.execute("""
            SELECT event_id, timestamp, user_id, session_id, event_type, severity, details_json
            FROM security_audit_logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in c.fetchall()]
        for r in rows:
            try:
                r["details"] = json.loads(r["details_json"])
            except Exception:
                r["details"] = {}
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Failed to fetch security events: {e}")
        return []

def get_security_summary_stats(db_path=None) -> Dict[str, Any]:
    """
    Aggregates security stats: total blocked attacks, injection breakdowns, audited operations.
    """
    try:
        conn = get_db_connection(db_path)
        c = conn.cursor()
        c.execute("""
            SELECT event_type, COUNT(*) as count 
            FROM security_audit_logs 
            GROUP BY event_type
        """)
        breakdown = {r["event_type"]: r["count"] for r in c.fetchall()}
        
        c.execute("SELECT COUNT(*) as total FROM security_audit_logs")
        total = c.fetchone()["total"]
        
        conn.close()
        return {
            "total_security_events": total,
            "event_breakdown": breakdown,
            "status": "active_monitoring"
        }
    except Exception:
        return {
            "total_security_events": 0,
            "event_breakdown": {},
            "status": "active_monitoring"
        }
