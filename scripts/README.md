# Intake CRM Helper Scripts

This directory contains helper scripts for the Intake CRM system.

## Scripts Overview

### 1. `run_llm_extraction.py` - Main Extraction Script
Extracts structured data from email attachments using OpenAI's GPT-4o-mini.

**Usage:**
```bash
# Basic extraction
python scripts/run_llm_extraction.py

# Extract with limit
python scripts/run_llm_extraction.py --limit 5

# Resume from where left off
python scripts/run_llm_extraction.py --resume

# Extract and ingest to database
python scripts/run_llm_extraction.py --ingest-db

# Extract, ingest, and archive
python scripts/run_llm_extraction.py --ingest-db --archive
```

**Features:**
- ✅ Consolidated extraction (all attachments processed together)
- ✅ Dynamic prompt generation from `app/processing/sample.json`
- ✅ Automatic field mapping
- ✅ Error handling and debugging output

### 2. `ingest_to_db.py` - Database Ingestion Script
Ingests extracted data into SQLite database for easy querying.

**Usage:**
```bash
# Ingest all extracted data
python scripts/ingest_to_db.py

# Ingest with custom database path
python scripts/ingest_to_db.py --db-path my-database.db

# Ingest with limit
python scripts/ingest_to_db.py --limit 10
```

**Database Schema:**
- **`referrals`** - Main table with all extracted referral data
- **`email_metadata`** - Additional email information
- **Indexes** - Optimized for common queries

### 3. `archive_processed_emails.py` - Archive Helper Script
Moves processed email directories to archive folder.

**Usage:**
```bash
# Archive processed emails
python scripts/archive_processed_emails.py

# Dry run (see what would be archived)
python scripts/archive_processed_emails.py --dry-run

# Custom archive directory
python scripts/archive_processed_emails.py --archive-dir data/archive
```

### 4. `upload_docs_to_s3.py` - S3 Document Upload Script
Uploads email documents (metadata, summaries, attachments) from local directories to S3 bucket.

**Usage:**
```bash
# Upload all email directories
python scripts/upload_docs_to_s3.py

# Upload with limit
python scripts/upload_docs_to_s3.py --limit 10

# Only upload directories with attachments
python scripts/upload_docs_to_s3.py --has-attachments

# Only upload directories with extracted data
python scripts/upload_docs_to_s3.py --has-extracted

# Upload by date range
python scripts/upload_docs_to_s3.py --date-from 2024-01-01 --date-to 2024-01-31

# Custom S3 prefix
python scripts/upload_docs_to_s3.py --s3-prefix "referrals/{email_id}"

# Dry run (see what would be uploaded)
python scripts/upload_docs_to_s3.py --dry-run
```

**Features:**
- ✅ Flexible filtering (attachments, extracted data, date ranges)
- ✅ Custom S3 prefix templates
- ✅ Dry run mode for testing
- ✅ Detailed progress reporting
- ✅ Error handling and retry logic

### 5. `query_db.py` - Database Query Helper
Simple utility to explore and query the database.

**Usage:**
```bash
# Show database overview
python scripts/query_db.py

# List recent referrals
python scripts/query_db.py --list-referrals

# Show counts by status
python scripts/query_db.py --count

# Custom query
python scripts/query_db.py --query "SELECT patient_name, priority FROM referrals WHERE referral = 1"
```

## Complete Workflow

### 1. Extract Data
```bash
python scripts/run_llm_extraction.py --limit 5
```

### 2. Ingest to Database
```bash
python scripts/ingest_to_db.py
```

### 3. Query Data
```bash
python scripts/query_db.py --list-referrals
```

### 4. Upload to S3 (Optional)
```bash
python scripts/upload_docs_to_s3.py --has-extracted
```

### 5. Archive Processed Emails
```bash
python scripts/archive_processed_emails.py
```

### Or Do It All At Once
```bash
python scripts/run_llm_extraction.py --ingest-db --archive
```

## Database Schema

### Referrals Table
| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER | Primary key |
| email_id | TEXT | Unique email identifier |
| email_subject | TEXT | Email subject line |
| email_from | TEXT | Sender email address |
| referral | BOOLEAN | Whether this is a referral request |
| patient_name | TEXT | Patient's full name |
| patient_dob | TEXT | Date of birth |
| patient_doi | TEXT | Date of injury |
| priority | TEXT | Urgency level (Urgent, Routine, etc.) |
| intake_requested_procedure | TEXT | JSON array of requested procedures |
| ... | ... | All other extracted fields |

### Email Metadata Table
| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER | Primary key |
| referral_id | INTEGER | Foreign key to referrals |
| conversation_id | TEXT | Email conversation ID |
| body_content | TEXT | Full email body |
| to_recipients | TEXT | JSON array of recipients |
| ... | ... | Other email metadata |

## Configuration

### Dynamic Field Mapping
The extraction system uses `app/processing/sample.json` as the source of truth for field mapping. To add new fields:

1. Update `app/processing/sample.json` with the new field structure
2. The prompt will automatically adapt to include the new fields
3. The database schema will need to be updated manually (or drop and recreate the database)

### Database Location
- Default: `intake-crm.db` in the project root
- Can be customized with `--db-path` argument

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Check your API key in settings
   - Verify you have sufficient credits
   - Check rate limits

2. **Database Errors**
   - Ensure SQLite is installed
   - Check file permissions
   - Verify database path is writable

3. **File Not Found Errors**
   - Ensure `data/emails` directory exists
   - Check that email directories contain required files

### Debug Mode
All scripts include detailed debug output. Look for lines starting with `🔧 DEBUG:` for troubleshooting information.

## Performance Tips

1. **Batch Processing**: Use `--limit` to process emails in batches
2. **Resume Capability**: Use `--resume` to continue from where you left off
3. **Database Indexes**: Already optimized for common queries
4. **Archive Regularly**: Keep the main directory clean by archiving processed emails 