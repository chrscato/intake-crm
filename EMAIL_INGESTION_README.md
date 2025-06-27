# Email Ingestion System

This system fetches emails with all metadata and attachments from Microsoft Graph API, saves them locally, and provides S3 upload functionality.

## Features

- ✅ Fetches emails with complete metadata (subject, sender, recipients, body, etc.)
- ✅ Downloads all attachments (PDFs, documents, images, etc.)
- ✅ Saves everything locally in organized directory structure
- ✅ Moves processed emails to archive folder
- ✅ Uploads to S3 with proper content types and manifests
- ✅ Uses environment variables for configuration
- ✅ Handles large attachments (>4MB)
- ✅ Provides detailed logging and error handling

## Setup

### 1. Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Microsoft Graph API Configuration
GRAPH_TENANT_ID=your_tenant_id_here
GRAPH_CLIENT_ID=your_client_id_here
GRAPH_CLIENT_SECRET=your_client_secret_here

# Email Configuration
SHARED_MAILBOX=your_email@domain.com
MAILBOX_FOLDER=Inbox

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-2
S3_BUCKET=your-s3-bucket-name

# OpenAI Configuration (for future use)
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
SQLITE_DB_PATH=./data/intake.db
```

### 2. Microsoft Graph API Setup

1. Go to [Azure Portal](https://portal.azure.com)
2. Create or select an App Registration
3. Add the following API permissions:
   - `Mail.Read`
   - `Mail.ReadWrite`
   - `Mail.ReadBasic`
4. Create a client secret
5. Note down the Tenant ID, Client ID, and Client Secret

### 3. AWS S3 Setup

1. Create an S3 bucket for storing email data
2. Create an IAM user with S3 access
3. Note down the Access Key ID and Secret Access Key

## Usage

### Quick Start

```bash
# Fetch emails from Inbox (default)
python scripts/run_email_ingestion.py

# Fetch emails from a specific folder
python scripts/run_email_ingestion.py --folder "providerbills"

# Fetch and upload to S3
python scripts/run_email_ingestion.py --action both

# Process more emails
python scripts/run_email_ingestion.py --max-emails 50

# Don't move processed emails
python scripts/run_email_ingestion.py --no-move
```

### Advanced Usage

```bash
# Process specific mailbox and folder
python scripts/run_email_ingestion.py \
  --mailbox "shared@company.com" \
  --folder "Inbox/providerbills" \
  --max-emails 100 \
  --archive-folder "processed_bills"

# Upload only (if emails already fetched)
python scripts/run_email_ingestion.py --action upload

# Custom S3 prefix
python scripts/run_email_ingestion.py \
  --action both \
  --s3-prefix "emails/2024/01/provider_bills"
```

### Programmatic Usage

```python
from app.email_ingest.email_processor import EmailProcessor
from app.email_ingest.s3_uploader import S3EmailUploader

# Fetch emails
processor = EmailProcessor()
results = processor.process_emails(
    mailbox="your@email.com",
    src_path=["Inbox", "providerbills"],
    max_emails=10
)

# Upload to S3
uploader = S3EmailUploader()
upload_results = uploader.upload_all_emails()
```

### LLM Extraction

After emails are downloaded you can run an extraction pass on the
attachments using OpenAI:

```bash
python scripts/run_llm_extraction.py              # process all directories
python scripts/run_llm_extraction.py --limit 5    # only first 5 directories
python scripts/run_llm_extraction.py --resume     # skip ones already processed
```

Each email directory will receive an `extracted.json` file containing the fields
defined in `app/processing/gpt4o_prompt.json`. See `sample.json` for an example
of the output.

## Data Structure

### Local Storage

Emails are saved in `data/emails/` with the following structure:

```
data/emails/
├── 20241201_143022_AQkA_Invoice_123/
│   ├── email_metadata.json      # Complete email metadata
│   ├── summary.json             # Processing summary
│   └── attachments/
│       ├── invoice.pdf
│       ├── receipt.docx
│       └── image.jpg
├── 20241201_143045_BQkB_Report_456/
│   ├── email_metadata.json
│   ├── summary.json
│   └── attachments/
│       └── report.xlsx
```

### S3 Storage

Files are uploaded to S3 with the following structure:

```
s3://your-bucket/
└── emails/
    └── 2024/
        └── 12/
            └── 01/
                ├── 20241201_143022_AQkA_Invoice_123/
                │   ├── email_metadata.json
                │   ├── summary.json
                │   ├── upload_manifest.json
                │   └── attachments/
                │       ├── invoice.pdf
                │       └── receipt.docx
                └── 20241201_143045_BQkB_Report_456/
                    ├── email_metadata.json
                    ├── summary.json
                    ├── upload_manifest.json
                    └── attachments/
                        └── report.xlsx
```

## File Formats

### email_metadata.json
Complete email metadata from Microsoft Graph API:
```json
{
  "id": "AAMkAGI2...",
  "subject": "Invoice #123",
  "receivedDateTime": "2024-12-01T14:30:22Z",
  "from": {
    "emailAddress": {
      "address": "sender@company.com",
      "name": "John Doe"
    }
  },
  "toRecipients": [...],
  "body": {...},
  "hasAttachments": true,
  ...
}
```

### summary.json
Processing summary:
```json
{
  "email_id": "AAMkAGI2...",
  "subject": "Invoice #123",
  "received_datetime": "2024-12-01T14:30:22Z",
  "from": {...},
  "has_attachments": true,
  "attachments_count": 2,
  "saved_attachments": [
    "attachments/invoice.pdf",
    "attachments/receipt.docx"
  ],
  "processed_at": "2024-12-01T14:30:25.123456"
}
```

### upload_manifest.json
S3 upload tracking:
```json
{
  "upload_timestamp": "2024-12-01T14:30:30Z",
  "email_directory": "data/emails/20241201_143022_AQkA_Invoice_123",
  "s3_prefix": "emails/2024/12/01/20241201_143022_AQkA_Invoice_123",
  "bucket": "your-bucket",
  "files_uploaded": 4,
  "files_failed": 0,
  "uploaded_files": [
    "email_metadata.json",
    "summary.json",
    "attachments/invoice.pdf",
    "attachments/receipt.docx"
  ]
}
```

## Error Handling

The system handles various error scenarios:

- **Authentication failures**: Clear error messages for invalid credentials
- **Network issues**: Retry logic for API calls
- **Large attachments**: Automatic handling of attachments >4MB
- **Duplicate filenames**: Automatic renaming with counters
- **S3 upload failures**: Detailed logging of failed uploads
- **Missing folders**: Automatic folder creation

## Monitoring

### Logs
The system provides detailed console output:
```
🔍 Looking for messages in user@company.com/Inbox/providerbills
📁 Source folder ID: AAMkAGI2...
📁 Destination folder ID: AAMkAGI3...

📧 Processing message 1: Invoice #123
   Received: 2024-12-01T14:30:22Z
   Has Attachments: True
📎 Found 2 attachments:
   - invoice.pdf (application/pdf, 245760 bytes)
   - receipt.docx (application/vnd.openxmlformats-officedocument.wordprocessingml.document, 123456 bytes)
✅ Saved to: data/emails/20241201_143022_AQkA_Invoice_123
✅ saved & moved: Invoice #123

📊 Summary:
- Total messages found: 1
- Successfully processed: 1
- Failed to process: 0
- Total attachments: 2
- Data saved to: data/emails
```

### Metrics
The system returns detailed metrics:
```python
{
    "total_messages": 10,
    "processed_messages": 9,
    "failed_messages": 1,
    "total_attachments": 15,
    "saved_locations": ["path1", "path2", ...]
}
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **API Permissions**: Use minimal required permissions for Microsoft Graph
3. **S3 Access**: Use IAM roles with least privilege access
4. **Data Encryption**: Consider enabling S3 encryption for sensitive data
5. **Token Management**: Tokens are automatically refreshed by the MSAL library

## Troubleshooting

### Common Issues

1. **Authentication Error**
   - Verify `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, and `GRAPH_CLIENT_SECRET`
   - Check API permissions in Azure Portal

2. **Folder Not Found**
   - Verify `MAILBOX_FOLDER` exists
   - Check mailbox permissions

3. **S3 Upload Failed**
   - Verify AWS credentials and bucket name
   - Check S3 bucket permissions

4. **Large Attachments**
   - System automatically handles attachments >4MB
   - Check network connectivity for large downloads

### Debug Mode

Add debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- [ ] Delta query support for incremental processing
- [ ] Email filtering by date range
- [ ] Parallel processing for multiple mailboxes
- [ ] Email content extraction and indexing
- [ ] Webhook support for real-time processing
- [ ] Database integration for tracking processed emails
- [ ] Email classification and routing
- [ ] Attachment virus scanning
- [ ] Email deduplication
- [ ] Performance metrics and monitoring 