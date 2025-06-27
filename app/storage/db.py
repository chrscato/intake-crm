import sqlite3, json
from app.settings import settings
con = sqlite3.connect(settings.SQLITE_DB_PATH)
con.execute("""
CREATE TABLE IF NOT EXISTS referrals(
  email_id TEXT PRIMARY KEY,
  raw_s3_key TEXT,
  extracted_json TEXT,
  corrected_json TEXT,
  processed INTEGER DEFAULT 0
)
""")
con.commit()

def add_stub(msg):
    con.execute("INSERT OR IGNORE INTO referrals(email_id, raw_s3_key) VALUES (?,?)",
                (msg['id'], ''))
    con.commit()
