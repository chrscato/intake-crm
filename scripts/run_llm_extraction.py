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
    extracted_file = path / "extracted.json"
    if resume and extracted_file.exists():
        print(f"⏩ Skipping {path.name} (already processed)")
        return False

    summary_file = path / "summary.json"
    metadata_file = path / "email_metadata.json"
    attachments_dir = path / "attachments"

    if not summary_file.exists() or not metadata_file.exists():
        print(f"⚠️  Missing summary or metadata in {path.name}, skipping")
        return False

    try:
        summary = json.loads(summary_file.read_text())
        metadata = json.loads(metadata_file.read_text())
    except Exception as exc:
        print(f"❌ Failed to load JSON in {path.name}: {exc}")
        return False

    email_text = metadata.get("body", {}).get("content", "")
    results = []

    if attachments_dir.exists():
        for attachment in sorted(attachments_dir.iterdir()):
            if attachment.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"}:
                print(f"🔍 Processing {attachment.name}")
                try:
                    file_bytes = attachment.read_bytes()
                    data = extract(file_bytes, email_text)
                    results.append({"attachment": attachment.name, "data": data})
                except Exception as exc:
                    print(f"❌ Extraction failed for {attachment.name}: {exc}")
                    results.append({"attachment": attachment.name, "error": str(exc)})

    if results:
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
