#!/usr/bin/env python
"""
S3 Document Upload Helper Script

Uploads email documents (metadata, summaries, attachments) from local data/emails/
directories to S3 bucket with various organization options.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.email_ingest.s3_uploader import S3EmailUploader
from app.settings import settings


def list_email_directories(base_dir: Path, limit: Optional[int] = None) -> List[Path]:
    """List email directories, optionally limited by count."""
    if not base_dir.exists():
        print(f"❌ Email directory not found: {base_dir}")
        return []
    
    directories = [d for d in sorted(base_dir.iterdir()) if d.is_dir()]
    
    if limit:
        directories = directories[:limit]
    
    return directories


def filter_directories(directories: List[Path], 
                      has_attachments: bool = None,
                      has_extracted: bool = None,
                      date_from: str = None,
                      date_to: str = None) -> List[Path]:
    """Filter directories based on criteria."""
    filtered = []
    
    for directory in directories:
        # Check if directory has attachments
        if has_attachments is not None:
            attachments_dir = directory / "attachments"
            has_attachments_dir = attachments_dir.exists() and any(attachments_dir.iterdir())
            if has_attachments != has_attachments_dir:
                continue
        
        # Check if directory has extracted.json
        if has_extracted is not None:
            extracted_file = directory / "extracted.json"
            if has_extracted != extracted_file.exists():
                continue
        
        # Check date range (based on directory name timestamp)
        if date_from or date_to:
            try:
                # Extract timestamp from directory name (format: YYYYMMDD_HHMMSS_...)
                timestamp_str = directory.name.split('_')[0] + '_' + directory.name.split('_')[1]
                dir_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                if date_from:
                    from_date = datetime.strptime(date_from, '%Y-%m-%d')
                    if dir_date.date() < from_date.date():
                        continue
                
                if date_to:
                    to_date = datetime.strptime(date_to, '%Y-%m-%d')
                    if dir_date.date() > to_date.date():
                        continue
                        
            except (ValueError, IndexError):
                # If we can't parse the date, skip this directory
                continue
        
        filtered.append(directory)
    
    return filtered


def generate_s3_prefix(directory: Path, prefix_template: str = None) -> str:
    """Generate S3 prefix for a directory."""
    if prefix_template:
        # Replace placeholders in template
        email_name = directory.name
        return prefix_template.format(
            email_name=email_name,
            email_id=email_name
        )
    else:
        # Default prefix structure: bucket/data/{email_id}/
        return f"data/{directory.name}"


def main():
    parser = argparse.ArgumentParser(description="Upload email documents to S3")
    parser.add_argument("--limit", type=int, default=None,
                       help="Limit number of directories to process")
    parser.add_argument("--has-attachments", action="store_true", default=None,
                       help="Only process directories with attachments")
    parser.add_argument("--no-attachments", action="store_true",
                       help="Only process directories without attachments")
    parser.add_argument("--has-extracted", action="store_true", default=None,
                       help="Only process directories with extracted.json")
    parser.add_argument("--no-extracted", action="store_true",
                       help="Only process directories without extracted.json")
    parser.add_argument("--date-from", type=str,
                       help="Only process directories from this date (YYYY-MM-DD)")
    parser.add_argument("--date-to", type=str,
                       help="Only process directories up to this date (YYYY-MM-DD)")
    parser.add_argument("--s3-prefix", type=str,
                       help="Custom S3 prefix template (use {email_name} or {email_id})")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be uploaded without actually uploading")
    parser.add_argument("--force", action="store_true",
                       help="Force re-upload even if files already exist in S3")
    parser.add_argument("--data-dir", type=str, default="data/emails",
                       help="Base directory containing email data (default: data/emails)")
    
    args = parser.parse_args()
    
    # Handle mutually exclusive arguments
    if args.has_attachments and args.no_attachments:
        print("❌ Cannot specify both --has-attachments and --no-attachments")
        return 1
    
    if args.has_extracted and args.no_extracted:
        print("❌ Cannot specify both --has-extracted and --no-extracted")
        return 1
    
    # Set boolean values
    has_attachments = None
    if args.has_attachments:
        has_attachments = True
    elif args.no_attachments:
        has_attachments = False
    
    has_extracted = None
    if args.has_extracted:
        has_extracted = True
    elif args.no_extracted:
        has_extracted = False
    
    # Initialize S3 uploader
    try:
        uploader = S3EmailUploader()
        print(f"🔗 Connected to S3 bucket: {uploader.bucket}")
    except Exception as e:
        print(f"❌ Failed to connect to S3: {e}")
        return 1
    
    # Set data directory
    data_dir = Path(args.data_dir)
    uploader.data_dir = data_dir
    
    # List and filter directories
    print(f"📁 Scanning directory: {data_dir}")
    directories = list_email_directories(data_dir, args.limit)
    
    if not directories:
        print("❌ No email directories found")
        return 1
    
    print(f"📋 Found {len(directories)} directories")
    
    # Apply filters
    filtered_directories = filter_directories(
        directories,
        has_attachments=has_attachments,
        has_extracted=has_extracted,
        date_from=args.date_from,
        date_to=args.date_to
    )
    
    if not filtered_directories:
        print("❌ No directories match the specified filters")
        return 1
    
    print(f"📤 Will process {len(filtered_directories)} directories")
    
    # Show what will be processed
    if args.dry_run:
        print("\n🔍 DRY RUN - Would upload the following directories:")
        for directory in filtered_directories:
            s3_prefix = generate_s3_prefix(directory, args.s3_prefix)
            print(f"   📁 {directory.name}")
            print(f"      S3: {s3_prefix}")
            
            # Show files that would be uploaded
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(directory)
                    print(f"      📄 {relative_path}")
        print(f"\n✅ Dry run completed - {len(filtered_directories)} directories would be uploaded")
        return 0
    
    # Perform actual uploads
    print(f"\n🚀 Starting upload of {len(filtered_directories)} directories...")
    
    success_count = 0
    failed_count = 0
    
    for i, directory in enumerate(filtered_directories, 1):
        print(f"\n📤 [{i}/{len(filtered_directories)}] Uploading: {directory.name}")
        
        try:
            # Generate S3 prefix
            s3_prefix = generate_s3_prefix(directory, args.s3_prefix)
            
            # Upload directory
            result = uploader.upload_email_directory(directory, s3_prefix)
            
            if result["files_failed"] == 0:
                print(f"✅ Successfully uploaded {result['files_uploaded']} files")
                success_count += 1
            else:
                print(f"⚠️  Uploaded {result['files_uploaded']} files, {result['files_failed']} failed")
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Failed to upload {directory.name}: {e}")
            failed_count += 1
    
    # Summary
    print(f"\n📊 Upload Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📁 Total: {len(filtered_directories)}")
    
    if success_count > 0:
        print(f"\n🎉 Successfully uploaded {success_count} directories to S3!")
        print(f"   Bucket: {uploader.bucket}")
        print(f"   Structure: {uploader.bucket}/data/{{email_id}}/")
    
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main()) 