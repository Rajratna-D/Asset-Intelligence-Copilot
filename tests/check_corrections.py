from backend.db.database import get_db_connection

conn = get_db_connection()
c = conn.cursor()
c.execute("SELECT note_id, asset_id, inspection_id, text FROM context_notes WHERE note_type = 'correction'")
for r in c.fetchall():
    print(f"{r['note_id']} | {r['asset_id']} | {r['inspection_id']} | {r['text']}")
