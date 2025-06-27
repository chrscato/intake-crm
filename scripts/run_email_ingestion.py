#!/usr/bin/env python
"""
Email Ingestion CLI Script
Run email ingestion with various options.
"""
import sys
import argparse
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.email_ingest.email_processor import EmailProcessor
from app.email_ingest.s3_uploader import S3EmailUploader
from app.settings import settings

def parse_folder_path(folder_arg: str) -> list:
    """Parse folder argument into path segments."""
    if not folder_arg:
        return [settings.MAILBOX_FOLDER]
    
    # Split by '/' or '\' to handle paths
    if '/' in folder_arg:
        return folder_arg.split('/')
    elif '\\' in folder_arg:
        return folder_arg.split('\\')
    else:
        # If it's just a folder name, assume it's under Inbox
        return ["Inbox", folder_arg]

def main():
    parser = argparse.ArgumentParser(description="Email Ingestion Tool")
    parser.add_argument("--action", choices=["fetch", "upload", "both"], default="fetch",
                       help="Action to perform: fetch emails, upload to S3, or both")
    parser.add_argument("--mailbox", default=settings.SHARED_MAILBOX,
                       help="Mailbox to process (default: from env)")
    parser.add_argument("--folder", default=settings.MAILBOX_FOLDER,
                       help="Folder to process (default: from env). Use 'Inbox/subfolder' for nested folders.")
    parser.add_argument("--max-emails", type=int, default=10,
                       help="Maximum number of emails to process (default: 10)")
    parser.add_argument("--no-move", action="store_true",
                       help="Don't move processed emails to archive folder")
    parser.add_argument("--archive-folder", default="archive_processed",
                       help="Archive folder name (default: archive_processed)")
    parser.add_argument("--s3-prefix", default=None,
                       help="S3 prefix for uploads (default: auto-generated)")
    parser.add_argument("--include-replies", action="store_true",
                       help="Include reply emails (default: only original inbound emails)")
    parser.add_argument("--debug-conversations", action="store_true",
                       help="Show conversation analysis for debugging")
    
    args = parser.parse_args()
    
    # Parse the folder path
    src_path = parse_folder_path(args.folder)
    
    print("🚀 Email Ingestion Tool")
    print(f"   Mailbox: {args.mailbox}")
    print(f"   Folder: {'/'.join(src_path)}")
    print(f"   Action: {args.action}")
    print(f"   Filter: {'All emails' if args.include_replies else 'Original inbound only'}")
    if args.debug_conversations:
        print(f"   Debug: Conversation analysis enabled")
    print()
    
    if args.action in ["fetch", "both"]:
        print("📧 Fetching emails...")
        processor = EmailProcessor()
        
        results = processor.process_emails(
            mailbox=args.mailbox,
            src_path=src_path,
            dest_folder=args.archive_folder,
            move_processed=not args.no_move,
            max_emails=args.max_emails,
            original_only=not args.include_replies,
            debug_conversations=args.debug_conversations
        )
        
        print(f"\n✅ Email fetching completed!")
        print(f"   Processed: {results['processed_messages']} emails")
        print(f"   Attachments: {results['total_attachments']} files")
        print(f"   Saved to: {processor.data_dir}")
    
    if args.action in ["upload", "both"]:
        print("\n📤 Uploading to S3...")
        uploader = S3EmailUploader()
        
        upload_results = uploader.upload_all_emails(s3_prefix=args.s3_prefix)
        
        if "error" not in upload_results:
            print(f"\n✅ S3 upload completed!")
            print(f"   Directories: {upload_results['total_directories']}")
            print(f"   Files uploaded: {upload_results['total_files_uploaded']}")
            print(f"   Bucket: {uploader.bucket}")
        else:
            print(f"\n❌ S3 upload failed: {upload_results['error']}")
    
    print("\n🎉 All done!")

if __name__ == "__main__":
    main() 