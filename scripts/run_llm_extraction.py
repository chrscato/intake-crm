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

from app.processing.openai_agent import extract


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
    results = []

    if attachments_dir.exists():
        attachments = list(attachments_dir.iterdir())
        print(f"🔧 DEBUG: Found {len(attachments)} attachments")
        
        for attachment in sorted(attachments):
            print(f"🔧 DEBUG: Checking attachment: {attachment.name}")
            print(f"🔧 DEBUG: Attachment suffix: {attachment.suffix}")
            print(f"🔧 DEBUG: Supported file type: {attachment.suffix.lower() in {'.pdf', '.png', '.jpg', '.jpeg'}}")
            
            if attachment.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"}:
                print(f"🔍 Processing {attachment.name}")
                try:
                    print(f"🔧 DEBUG: Reading file bytes...")
                    file_bytes = attachment.read_bytes()
                    print(f"🔧 DEBUG: File size: {len(file_bytes)} bytes")
                    
                    print(f"🔧 DEBUG: Calling extract function...")
                    data = extract(file_bytes, email_text, attachment.suffix)
                    print(f"🔧 DEBUG: Extract function completed successfully")
                    
                    results.append({"attachment": attachment.name, "data": data})
                    print(f"🔧 DEBUG: Added result for {attachment.name}")
                except Exception as exc:
                    print(f"🔧 DEBUG: Exception during extraction: {type(exc).__name__}: {exc}")
                    print(f"❌ Extraction failed for {attachment.name}: {exc}")
                    results.append({"attachment": attachment.name, "error": str(exc)})
            else:
                print(f"🔧 DEBUG: Skipping unsupported file: {attachment.name}")

    if results:
        print(f"🔧 DEBUG: Saving {len(results)} results to {extracted_file}")
        with open(extracted_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"✅ Saved results to {extracted_file}")
        return True

    print(f"ℹ️  No supported attachments in {path.name}")
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
