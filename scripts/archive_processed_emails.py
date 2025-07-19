#!/usr/bin/env python
"""Archive Processed Emails Helper Script

Moves email directories that have been processed (have extracted.json) to
an archive directory for cleanup and organization.
"""
import argparse
import shutil
import sys
from pathlib import Path

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


def archive_processed_emails(archive_dir: Path, dry_run: bool = False) -> int:
    """Archive email directories that have been processed.
    
    Args:
        archive_dir: Directory to move processed emails to
        dry_run: If True, only show what would be moved without actually moving
    
    Returns:
        Number of directories archived
    """
    base_dir = Path("data/emails")
    if not base_dir.exists():
        print("No data/emails directory found")
        return 0
    
    # Create archive directory if it doesn't exist
    if not dry_run:
        archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all email directories
    email_dirs = [p for p in base_dir.iterdir() if p.is_dir()]
    
    archived_count = 0
    for email_dir in email_dirs:
        extracted_file = email_dir / "extracted.json"
        
        # Check if this directory has been processed
        if extracted_file.exists():
            archive_path = archive_dir / email_dir.name
            
            if dry_run:
                print(f"📋 Would archive: {email_dir.name}")
            else:
                try:
                    # Move the entire directory
                    shutil.move(str(email_dir), str(archive_path))
                    print(f"📦 Archived: {email_dir.name}")
                    archived_count += 1
                except Exception as exc:
                    print(f"❌ Failed to archive {email_dir.name}: {exc}")
        else:
            if dry_run:
                print(f"⏳ Not processed yet: {email_dir.name}")
    
    return archived_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Archive processed email directories")
    parser.add_argument("--archive-dir", type=str, default="data/emails/archive", 
                       help="Directory to archive processed emails to")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be archived without actually moving files")
    args = parser.parse_args()

    archive_dir = Path(args.archive_dir)
    
    if args.dry_run:
        print("🔍 DRY RUN - No files will be moved")
    
    print(f"🚀 Starting archive process...")
    archived_count = archive_processed_emails(archive_dir, args.dry_run)
    
    if args.dry_run:
        print(f"📋 Would archive {archived_count} directories")
    else:
        print(f"✅ Successfully archived {archived_count} directories to {archive_dir}")


if __name__ == "__main__":
    main() 