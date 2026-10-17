import sqlite3
from pathlib import Path
from typing import Optional
from backend.config import SQLITE_DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def ensure_schema(conn: sqlite3.Connection):
    """
    Ensures security audit and operational tables are always provisioned.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS security_audit_logs (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            details_json TEXT NOT NULL
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON security_audit_logs(timestamp DESC);")

def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target_path = str(db_path or SQLITE_DB_PATH)
    conn = sqlite3.connect(target_path, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    ensure_schema(conn)
    return conn

def init_db(db_path: Optional[Path] = None, schema_path: Optional[Path] = None) -> None:
    conn = get_db_connection(db_path)
    script_path = schema_path or SCHEMA_PATH
    with open(script_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {SQLITE_DB_PATH}")
