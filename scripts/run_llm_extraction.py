#!/usr/bin/env python
"""LLM Extraction CLI

Iterate over downloaded email directories and extract structured data from
attachments using the OpenAI agent, writing directly to database columns.
"""
import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Add repository root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.processing.openai_agent import extract_consolidated


def get_database_connection(db_path: str) -> sqlite3.Connection:
    """Get database connection and ensure table exists."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure referrals table exists with all required columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT UNIQUE NOT NULL,
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
    
    conn.commit()
    return conn


def update_referral_in_database(conn: sqlite3.Connection, email_id: str, consolidated_data: dict, 
                               processed_attachments: list, email_subject: str, email_from: str) -> bool:
    """Update referral record in database with extracted data."""
    try:
        cursor = conn.cursor()
        
        # Check if referral exists
        cursor.execute("SELECT id FROM referrals WHERE email_id = ?", (email_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute("""
                UPDATE referrals SET 
                    email_subject = ?, email_from = ?,
                    patient_name = ?, patient_dob = ?, patient_doi = ?,
                    patient_gender = ?, patient_id = ?, patient_address = ?,
                    patient_email = ?, patient_phone = ?,
                    order_number = ?, priority = ?, 
                    injury_description = ?, diagnosis_code = ?, icd_code = ?,
                    diagnosis_description = ?, intake_client_company = ?,
                    intake_client_email = ?, intake_client_name = ?,
                    intake_client_phone = ?, intake_adjuster_name = ?,
                    intake_adjuster_email = ?, intake_adjuster_phone = ?,
                    intake_preferred_provider = ?, intake_requested_procedure = ?,
                    intake_instructions = ?, patient_instructions = ?,
                    referring_provider_name = ?, referring_provider_npi = ?,
                    referring_provider_address = ?, referring_provider_email = ?,
                    referring_provider_phone = ?, employer_address = ?,
                    employer_email = ?, processed_attachments = ?,
                    updated_at = ?
                WHERE email_id = ?
            """, (
                email_subject, email_from,
                consolidated_data.get('patient_name'),
                consolidated_data.get('patient_dob'), 
                consolidated_data.get('patient_doi'),
                consolidated_data.get('patient_gender'),
                consolidated_data.get('patient_id'),
                consolidated_data.get('patient_address'),
                consolidated_data.get('patient_email'),
                consolidated_data.get('patient_phone'),
                consolidated_data.get('order_number'),
                consolidated_data.get('priority'),
                consolidated_data.get('injury_description'),
                consolidated_data.get('diagnosis_code'),
                consolidated_data.get('icd_code'),
                consolidated_data.get('diagnosis_description'),
                consolidated_data.get('intake_client_company'),
                consolidated_data.get('intake_client_email'),
                consolidated_data.get('intake_client_name'),
                consolidated_data.get('intake_client_phone'),
                consolidated_data.get('intake_adjuster_name'),
                consolidated_data.get('intake_adjuster_email'),
                consolidated_data.get('intake_adjuster_phone'),
                consolidated_data.get('intake_preferred_provider'),
                consolidated_data.get('intake_requested_procedure'),
                consolidated_data.get('intake_instructions'),
                consolidated_data.get('patient_instructions'),
                consolidated_data.get('referring_provider_name'),
                consolidated_data.get('referring_provider_npi'),
                consolidated_data.get('referring_provider_address'),
                consolidated_data.get('referring_provider_email'),
                consolidated_data.get('referring_provider_phone'),
                consolidated_data.get('employer_address'),
                consolidated_data.get('employer_email'),
                json.dumps(processed_attachments),
                datetime.now().isoformat(),
                email_id
            ))
            print(f"🔄 Updated existing referral for {email_id}")
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO referrals (
                    email_id, email_subject, email_from,
                    patient_name, patient_dob, patient_doi,
                    patient_gender, patient_id, patient_address,
                    patient_email, patient_phone,
                    order_number, priority, 
                    injury_description, diagnosis_code, icd_code,
                    diagnosis_description, intake_client_company,
                    intake_client_email, intake_client_name,
                    intake_client_phone, intake_adjuster_name,
                    intake_adjuster_email, intake_adjuster_phone,
                    intake_preferred_provider, intake_requested_procedure,
                    intake_instructions, patient_instructions,
                    referring_provider_name, referring_provider_npi,
                    referring_provider_address, referring_provider_email,
                    referring_provider_phone, employer_address,
                    employer_email, processed_attachments
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_id, email_subject, email_from,
                consolidated_data.get('patient_name'),
                consolidated_data.get('patient_dob'), 
                consolidated_data.get('patient_doi'),
                consolidated_data.get('patient_gender'),
                consolidated_data.get('patient_id'),
                consolidated_data.get('patient_address'),
                consolidated_data.get('patient_email'),
                consolidated_data.get('patient_phone'),
                consolidated_data.get('order_number'),
                consolidated_data.get('priority'),
                consolidated_data.get('injury_description'),
                consolidated_data.get('diagnosis_code'),
                consolidated_data.get('icd_code'),
                consolidated_data.get('diagnosis_description'),
                consolidated_data.get('intake_client_company'),
                consolidated_data.get('intake_client_email'),
                consolidated_data.get('intake_client_name'),
                consolidated_data.get('intake_client_phone'),
                consolidated_data.get('intake_adjuster_name'),
                consolidated_data.get('intake_adjuster_email'),
                consolidated_data.get('intake_adjuster_phone'),
                consolidated_data.get('intake_preferred_provider'),
                consolidated_data.get('intake_requested_procedure'),
                consolidated_data.get('intake_instructions'),
                consolidated_data.get('patient_instructions'),
                consolidated_data.get('referring_provider_name'),
                consolidated_data.get('referring_provider_npi'),
                consolidated_data.get('referring_provider_address'),
                consolidated_data.get('referring_provider_email'),
                consolidated_data.get('referring_provider_phone'),
                consolidated_data.get('employer_address'),
                consolidated_data.get('employer_email'),
                json.dumps(processed_attachments)
            ))
            print(f"✅ Created new referral for {email_id}")
        
        conn.commit()
        return True
        
    except Exception as exc:
        print(f"❌ Database update failed for {email_id}: {exc}")
        conn.rollback()
        return False


def process_directory(path: Path, resume: bool, db_conn: sqlite3.Connection) -> bool:
    """Run extraction for a single email directory and write directly to database.

    Returns True if extraction completed, False otherwise.
    """
    print(f"🔧 DEBUG: Processing directory: {path.name}")
    
    # Check if already processed (optional - for resume functionality)
    if resume:
        cursor = db_conn.cursor()
        cursor.execute("SELECT id FROM referrals WHERE email_id = ?", (path.name,))
        if cursor.fetchone():
            print(f"⏩ Skipping {path.name} (already in database)")
            return False

    summary_file = path / "summary.json"
    metadata_file = path / "email_metadata.json"
    attachments_dir = path / "attachments"

    print(f"🔧 DEBUG: Checking required files...")
    print(f"🔧 DEBUG: Summary file exists: {summary_file.exists()}")
    print(f"🔧 DEBUG: Metadata file exists: {metadata_file.exists()}")
    print(f"🔧 DEBUG: Attachments dir exists: {attachments_dir.exists()}")

    if not summary_file.exists() or not metadata_file.exists():
        print(f"⚠️  Missing summary or metadata in {path.name}, skipping")
        return False

    try:
        print(f"🔧 DEBUG: Loading JSON files...")
        summary = json.loads(summary_file.read_text())
        metadata = json.loads(metadata_file.read_text())
        print(f"🔧 DEBUG: JSON files loaded successfully")
    except Exception as exc:
        print(f"❌ Failed to load JSON in {path.name}: {exc}")
        return False

    email_text = metadata.get("body", {}).get("content", "")
    email_subject = metadata.get("subject", "")
    email_from = metadata.get("from", {}).get("emailAddress", {}).get("address", "")
    print(f"🔧 DEBUG: Email text length: {len(email_text)} characters")

    if attachments_dir.exists():
        attachments = list(attachments_dir.iterdir())
        print(f"🔧 DEBUG: Found {len(attachments)} attachments")
        
        # Collect all supported attachments
        supported_attachments = []
        file_bytes_list = []
        file_extensions = []
        
        for attachment in sorted(attachments):
            print(f"🔧 DEBUG: Checking attachment: {attachment.name}")
            print(f"🔧 DEBUG: Attachment suffix: {attachment.suffix}")
            print(f"🔧 DEBUG: Supported file type: {attachment.suffix.lower() in {'.pdf', '.png', '.jpg', '.jpeg'}}")
            
            if attachment.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"}:
                supported_attachments.append(attachment.name)
                print(f"🔍 Adding {attachment.name} to consolidated processing")
                try:
                    print(f"🔧 DEBUG: Reading file bytes...")
                    file_bytes = attachment.read_bytes()
                    print(f"🔧 DEBUG: File size: {len(file_bytes)} bytes")
                    
                    file_bytes_list.append(file_bytes)
                    file_extensions.append(attachment.suffix)
                    print(f"🔧 DEBUG: Added {attachment.name} to processing list")
                except Exception as exc:
                    print(f"❌ Failed to read {attachment.name}: {exc}")
                    return False
            else:
                print(f"🔧 DEBUG: Skipping unsupported file: {attachment.name}")

        if file_bytes_list:
            print(f"🔧 DEBUG: Processing {len(file_bytes_list)} attachments together")
            try:
                print(f"🔧 DEBUG: Calling consolidated extract function...")
                consolidated_data = extract_consolidated(file_bytes_list, email_text, file_extensions)
                print(f"🔧 DEBUG: Consolidated extraction completed successfully")
                
                # Write directly to database instead of creating JSON file
                success = update_referral_in_database(
                    db_conn, path.name, consolidated_data, 
                    supported_attachments, email_subject, email_from
                )
                
                if success:
                    print(f"✅ Successfully updated database for {path.name}")
                    return True
                else:
                    print(f"❌ Failed to update database for {path.name}")
                    return False
                
            except Exception as exc:
                print(f"🔧 DEBUG: Exception during consolidated extraction: {type(exc).__name__}: {exc}")
                print(f"❌ Consolidated extraction failed: {exc}")
                return False
        else:
            print(f"ℹ️  No supported attachments in {path.name}")
            return False
    else:
        print(f"ℹ️  No attachments directory in {path.name}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM extraction on attachments and write to database")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of directories to process")
    parser.add_argument("--resume", action="store_true", help="Skip directories that already exist in database")
    parser.add_argument("--archive", action="store_true", help="Archive processed emails after extraction")
    parser.add_argument("--db-path", type=str, default="intake-crm.db", help="Database path")
    args = parser.parse_args()

    base_dir = Path("data/emails")
    if not base_dir.exists():
        print("No data/emails directory found")
        return

    # Get database connection
    print(f"🔗 Connecting to database: {args.db_path}")
    try:
        db_conn = get_database_connection(args.db_path)
        print(f"✅ Database connection established")
    except Exception as exc:
        print(f"❌ Failed to connect to database: {exc}")
        return

    directories = [p for p in sorted(base_dir.iterdir()) if p.is_dir()]
    if args.limit:
        directories = directories[: args.limit]

    print(f"🚀 Running extraction on {len(directories)} directories")
    success_count = 0
    
    try:
        for directory in directories:
            if process_directory(directory, args.resume, db_conn):
                success_count += 1
        
        print(f"✅ Successfully processed {success_count}/{len(directories)} directories")
        
    finally:
        db_conn.close()
        print(f"🔗 Database connection closed")
    
    if args.archive:
        print("\n📦 Archiving processed emails...")
        try:
            subprocess.run([
                sys.executable, "scripts/archive_processed_emails.py"
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Archiving failed: {e}")


if __name__ == "__main__":
    main()
