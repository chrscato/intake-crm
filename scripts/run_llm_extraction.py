#!/usr/bin/env python
"""LLM Extraction CLI

Iterate over downloaded email directories and extract structured data from
attachments using the OpenAI agent.
"""
import argparse
import json
import sys
from pathlib import Path

# Add repository root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.processing.openai_agent import extract_consolidated


def process_directory(path: Path, resume: bool) -> bool:
    """Run extraction for a single email directory.

    Returns True if extraction completed, False otherwise.
    """
    print(f"🔧 DEBUG: Processing directory: {path.name}")
    
    extracted_file = path / "extracted.json"
    if resume and extracted_file.exists():
        print(f"⏩ Skipping {path.name} (already processed)")
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
                
                # Save the consolidated result
                result = {
                    "consolidated_data": consolidated_data,
                    "processed_attachments": supported_attachments,
                    "email_subject": metadata.get("subject", ""),
                    "email_from": metadata.get("from", {}).get("emailAddress", {}).get("address", "")
                }
                
                print(f"🔧 DEBUG: Saving consolidated result to {extracted_file}")
                with open(extracted_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                print(f"✅ Saved consolidated results to {extracted_file}")
                return True
                
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
    parser = argparse.ArgumentParser(description="Run LLM extraction on attachments")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of directories to process")
    parser.add_argument("--resume", action="store_true", help="Skip directories that already contain extracted.json")
    args = parser.parse_args()

    base_dir = Path("data/emails")
    if not base_dir.exists():
        print("No data/emails directory found")
        return

    directories = [p for p in sorted(base_dir.iterdir()) if p.is_dir()]
    if args.limit:
        directories = directories[: args.limit]

    print(f"🚀 Running extraction on {len(directories)} directories")
    for directory in directories:
        process_directory(directory, args.resume)


if __name__ == "__main__":
    main()
