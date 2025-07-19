#!/usr/bin/env python
"""Database Ingestion Helper Script

Scrapes extracted.json files from email directories and ingests them into
a SQLite database for easy querying and management.
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Fix Windows console encoding
if sys.platform.startswith('win'):
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Force UTF-8 encoding for stdout
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Add repository root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_database(db_path: Path) -> sqlite3.Connection:
    """Create the database and tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create referrals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT UNIQUE NOT NULL,
            conversation_id TEXT,
            email_subject TEXT,
            email_from TEXT,
            email_received_datetime TEXT,
            referral BOOLEAN,
            employer_address TEXT,
            employer_email TEXT,
            injury_description TEXT,
            diagnosis_code TEXT,
            icd_code TEXT,
            diagnosis_description TEXT,
            intake_client_company TEXT,
            intake_client_email TEXT,
            intake_client_name TEXT,
            intake_adjuster_name TEXT,
            intake_adjuster_email TEXT,
            intake_adjuster_phone TEXT,
            intake_client_phone TEXT,
            patient_name TEXT,
            patient_gender TEXT,
            patient_id TEXT,
            order_number TEXT,
            patient_dob TEXT,
            patient_doi TEXT,
            intake_instructions TEXT,
            patient_address TEXT,
            patient_email TEXT,
            patient_phone TEXT,
            intake_preferred_provider TEXT,
            intake_requested_procedure TEXT,
            patient_instructions TEXT,
            priority TEXT,
            referring_provider_name TEXT,
            referring_provider_npi TEXT,
            referring_provider_address TEXT,
            referring_provider_email TEXT,
            referring_provider_phone TEXT,
            processed_attachments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add new columns if they don't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE referrals ADD COLUMN diagnosis_code TEXT")
        print("✅ Added diagnosis_code column")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE referrals ADD COLUMN icd_code TEXT")
        print("✅ Added icd_code column")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE referrals ADD COLUMN diagnosis_description TEXT")
        print("✅ Added diagnosis_description column")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE referrals ADD COLUMN intake_adjuster_name TEXT")
        print("✅ Added intake_adjuster_name column")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE referrals ADD COLUMN intake_adjuster_email TEXT")
        print("✅ Added intake_adjuster_email column")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE referrals ADD COLUMN intake_adjuster_phone TEXT")
        print("✅ Added intake_adjuster_phone column")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE referrals ADD COLUMN conversation_id TEXT")
        print("✅ Added conversation_id column")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Create email_metadata table for additional email info
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referral_id INTEGER,
            email_id TEXT,
            conversation_id TEXT,
            importance TEXT,
            is_read BOOLEAN,
            has_attachments BOOLEAN,
            body_content TEXT,
            body_content_type TEXT,
            to_recipients TEXT,
            cc_recipients TEXT,
            bcc_recipients TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referral_id) REFERENCES referrals (id)
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_email_id ON referrals(email_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_patient_name ON referrals(patient_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_order_number ON referrals(order_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referrals_created_at ON referrals(created_at)")
    
    conn.commit()
    return conn


def parse_array_field(value: Any) -> str:
    """Convert array fields to JSON string for storage."""
    if isinstance(value, list):
        return json.dumps(value)
    return str(value) if value is not None else None


def extract_email_id_from_path(path: Path) -> str:
    """Extract email ID from directory path."""
    return path.name


def ingest_extracted_data(conn: sqlite3.Connection, email_dir: Path) -> bool:
    """Ingest a single extracted.json file into the database."""
    extracted_file = email_dir / "extracted.json"
    metadata_file = email_dir / "email_metadata.json"
    
    if not extracted_file.exists():
        print(f"⚠️  No extracted.json found in {email_dir.name}")
        return False
    
    try:
        # Load extracted data
        with open(extracted_file, "r", encoding="utf-8") as f:
            extracted_data = json.load(f)
        
        # Load email metadata if available
        email_metadata = {}
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                email_metadata = json.load(f)
        
        email_id = extract_email_id_from_path(email_dir)
        consolidated_data = extracted_data.get("consolidated_data", {})
        
        # Prepare referral data
        referral_data = {
            "email_id": email_id,
            "conversation_id": email_metadata.get("conversationId"),
            "email_subject": extracted_data.get("email_subject"),
            "email_from": extracted_data.get("email_from"),
            "email_received_datetime": email_metadata.get("receivedDateTime"),
            "referral": consolidated_data.get("referral"),
            "employer_address": consolidated_data.get("employer_address"),
            "employer_email": consolidated_data.get("employer_email"),
            "injury_description": consolidated_data.get("injury_description"),
            "diagnosis_code": consolidated_data.get("diagnosis_code"),
            "icd_code": consolidated_data.get("icd_code"),
            "diagnosis_description": consolidated_data.get("diagnosis_description"),
            "intake_client_company": consolidated_data.get("intake_client_company"),
            "intake_client_email": consolidated_data.get("intake_client_email"),
            "intake_client_name": consolidated_data.get("intake_client_name"),
            "intake_adjuster_name": consolidated_data.get("intake_adjuster_name"),
            "intake_adjuster_email": consolidated_data.get("intake_adjuster_email"),
            "intake_adjuster_phone": consolidated_data.get("intake_adjuster_phone"),
            "intake_client_phone": consolidated_data.get("intake_client_phone"),
            "patient_name": consolidated_data.get("patient_name"),
            "patient_gender": consolidated_data.get("patient_gender"),
            "patient_id": consolidated_data.get("patient_id"),
            "order_number": consolidated_data.get("order_number"),
            "patient_dob": consolidated_data.get("patient_dob"),
            "patient_doi": consolidated_data.get("patient_doi"),
            "intake_instructions": consolidated_data.get("intake_instructions"),
            "patient_address": consolidated_data.get("patient_address"),
            "patient_email": consolidated_data.get("patient_email"),
            "patient_phone": consolidated_data.get("patient_phone"),
            "intake_preferred_provider": consolidated_data.get("intake_preferred_provider"),
            "intake_requested_procedure": parse_array_field(consolidated_data.get("intake_requested_procedure")),
            "patient_instructions": consolidated_data.get("patient_instructions"),
            "priority": consolidated_data.get("priority"),
            "referring_provider_name": consolidated_data.get("referring_provider_name"),
            "referring_provider_npi": consolidated_data.get("referring_provider_npi"),
            "referring_provider_address": consolidated_data.get("referring_provider_address"),
            "referring_provider_email": consolidated_data.get("referring_provider_email"),
            "referring_provider_phone": consolidated_data.get("referring_provider_phone"),
            "processed_attachments": parse_array_field(extracted_data.get("processed_attachments", [])),
            "updated_at": datetime.now().isoformat()
        }
        
        cursor = conn.cursor()
        
        # Check if this email already exists
        cursor.execute("SELECT id FROM referrals WHERE email_id = ?", (email_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            referral_id = existing[0]
            set_clause = ", ".join([f"{k} = ?" for k in referral_data.keys() if k != "email_id"])
            values = [v for k, v in referral_data.items() if k != "email_id"]
            values.append(email_id)
            
            cursor.execute(f"UPDATE referrals SET {set_clause} WHERE email_id = ?", values)
            print(f"🔄 Updated existing record for {email_dir.name}")
        else:
            # Insert new record
            placeholders = ", ".join(["?" for _ in referral_data])
            columns = ", ".join(referral_data.keys())
            cursor.execute(f"INSERT INTO referrals ({columns}) VALUES ({placeholders})", list(referral_data.values()))
            referral_id = cursor.lastrowid
            print(f"✅ Inserted new record for {email_dir.name}")
        
        # Store additional email metadata
        if email_metadata:
            metadata_data = {
                "referral_id": referral_id,
                "email_id": email_id,
                "conversation_id": email_metadata.get("conversationId"),
                "importance": email_metadata.get("importance"),
                "is_read": email_metadata.get("isRead"),
                "has_attachments": email_metadata.get("hasAttachments"),
                "body_content": email_metadata.get("body", {}).get("content"),
                "body_content_type": email_metadata.get("body", {}).get("contentType"),
                "to_recipients": json.dumps([r.get("emailAddress", {}).get("address") for r in email_metadata.get("toRecipients", [])]),
                "cc_recipients": json.dumps([r.get("emailAddress", {}).get("address") for r in email_metadata.get("ccRecipients", [])]),
                "bcc_recipients": json.dumps([r.get("emailAddress", {}).get("address") for r in email_metadata.get("bccRecipients", [])])
            }
            
            # Check if metadata already exists
            cursor.execute("SELECT id FROM email_metadata WHERE referral_id = ?", (referral_id,))
            existing_metadata = cursor.fetchone()
            
            if existing_metadata:
                # Update existing metadata
                set_clause = ", ".join([f"{k} = ?" for k in metadata_data.keys() if k != "referral_id"])
                values = [v for k, v in metadata_data.items() if k != "referral_id"]
                values.append(referral_id)
                cursor.execute(f"UPDATE email_metadata SET {set_clause} WHERE referral_id = ?", values)
            else:
                # Insert new metadata
                placeholders = ", ".join(["?" for _ in metadata_data])
                columns = ", ".join(metadata_data.keys())
                cursor.execute(f"INSERT INTO email_metadata ({columns}) VALUES ({placeholders})", list(metadata_data.values()))
        
        conn.commit()
        return True
        
    except Exception as exc:
        print(f"❌ Failed to ingest {email_dir.name}: {exc}")
        conn.rollback()
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest extracted data into SQLite database")
    parser.add_argument("--db-path", type=str, default="intake-crm.db", help="Path to SQLite database file")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of directories to process")
    parser.add_argument("--force", action="store_true", help="Force re-ingestion of existing records")
    args = parser.parse_args()

    db_path = Path(args.db_path)
    base_dir = Path("data/emails")
    
    if not base_dir.exists():
        print("No data/emails directory found")
        return

    print(f"🔧 Creating/connecting to database: {db_path}")
    conn = create_database(db_path)
    
    # Get all email directories
    directories = [p for p in sorted(base_dir.iterdir()) if p.is_dir()]
    if args.limit:
        directories = directories[: args.limit]

    print(f"🚀 Processing {len(directories)} email directories")
    
    success_count = 0
    for directory in directories:
        if ingest_extracted_data(conn, directory):
            success_count += 1
    
    conn.close()
    print(f"✅ Successfully processed {success_count}/{len(directories)} directories")


if __name__ == "__main__":
    main() 