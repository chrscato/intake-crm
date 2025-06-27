#!/usr/bin/env python
"""
S3 Uploader for Email Data
Uploads locally saved email data and attachments to S3.
"""
import os
import json
import boto3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from app.settings import settings

class S3EmailUploader:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.S3_BUCKET
        self.data_dir = Path("data/emails")
        
    def upload_file(self, local_path: Path, s3_key: str) -> bool:
        """Upload a single file to S3."""
        try:
            self.s3_client.upload_file(
                str(local_path),
                self.bucket,
                s3_key,
                ExtraArgs={'ContentType': self._get_content_type(local_path)}
            )
            return True
        except Exception as e:
            print(f"❌ Failed to upload {local_path}: {e}")
            return False
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get appropriate content type for file."""
        suffix = file_path.suffix.lower()
        content_types = {
            '.json': 'application/json',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.csv': 'text/csv'
        }
        return content_types.get(suffix, 'application/octet-stream')
    
    def upload_email_directory(self, email_dir: Path, s3_prefix: str = None) -> Dict:
        """Upload an entire email directory to S3."""
        if not email_dir.exists():
            raise FileNotFoundError(f"Email directory not found: {email_dir}")
        
        # Generate S3 prefix if not provided
        if not s3_prefix:
            timestamp = datetime.now().strftime("%Y/%m/%d")
            email_name = email_dir.name
            s3_prefix = f"emails/{timestamp}/{email_name}"
        
        results = {
            "email_dir": str(email_dir),
            "s3_prefix": s3_prefix,
            "files_uploaded": 0,
            "files_failed": 0,
            "uploaded_files": [],
            "failed_files": []
        }
        
        print(f"📤 Uploading email directory: {email_dir}")
        print(f"   S3 prefix: {s3_prefix}")
        
        # Upload all files in the directory recursively
        for file_path in email_dir.rglob("*"):
            if file_path.is_file():
                # Calculate relative path from email directory
                relative_path = file_path.relative_to(email_dir)
                s3_key = f"{s3_prefix}/{relative_path}"
                
                if self.upload_file(file_path, s3_key):
                    results["files_uploaded"] += 1
                    results["uploaded_files"].append(str(relative_path))
                    print(f"   ✅ {relative_path}")
                else:
                    results["files_failed"] += 1
                    results["failed_files"].append(str(relative_path))
                    print(f"   ❌ {relative_path}")
        
        # Create upload manifest
        manifest = {
            "upload_timestamp": datetime.now().isoformat(),
            "email_directory": str(email_dir),
            "s3_prefix": s3_prefix,
            "bucket": self.bucket,
            "files_uploaded": results["files_uploaded"],
            "files_failed": results["files_failed"],
            "uploaded_files": results["uploaded_files"],
            "failed_files": results["failed_files"]
        }
        
        # Upload manifest to S3
        manifest_key = f"{s3_prefix}/upload_manifest.json"
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=manifest_key,
                Body=json.dumps(manifest, indent=2),
                ContentType='application/json'
            )
            print(f"   📋 Upload manifest: {manifest_key}")
        except Exception as e:
            print(f"   ⚠️  Failed to upload manifest: {e}")
        
        return results
    
    def upload_all_emails(self, s3_prefix: str = None) -> Dict:
        """Upload all email directories to S3."""
        if not self.data_dir.exists():
            print(f"❌ Data directory not found: {self.data_dir}")
            return {"error": "Data directory not found"}
        
        email_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]
        if not email_dirs:
            print(f"❌ No email directories found in {self.data_dir}")
            return {"error": "No email directories found"}
        
        print(f"📤 Found {len(email_dirs)} email directories to upload")
        
        total_results = {
            "total_directories": len(email_dirs),
            "successful_uploads": 0,
            "failed_uploads": 0,
            "total_files_uploaded": 0,
            "total_files_failed": 0,
            "directory_results": []
        }
        
        for email_dir in email_dirs:
            try:
                result = self.upload_email_directory(email_dir, s3_prefix)
                total_results["directory_results"].append(result)
                total_results["total_files_uploaded"] += result["files_uploaded"]
                total_results["total_files_failed"] += result["files_failed"]
                
                if result["files_failed"] == 0:
                    total_results["successful_uploads"] += 1
                else:
                    total_results["failed_uploads"] += 1
                    
            except Exception as e:
                print(f"❌ Failed to upload directory {email_dir}: {e}")
                total_results["failed_uploads"] += 1
                total_results["directory_results"].append({
                    "email_dir": str(email_dir),
                    "error": str(e)
                })
        
        print(f"\n📊 Upload Summary:")
        print(f"- Total directories: {total_results['total_directories']}")
        print(f"- Successful uploads: {total_results['successful_uploads']}")
        print(f"- Failed uploads: {total_results['failed_uploads']}")
        print(f"- Total files uploaded: {total_results['total_files_uploaded']}")
        print(f"- Total files failed: {total_results['total_files_failed']}")
        
        return total_results
    
    def list_uploaded_emails(self, s3_prefix: str = "emails/") -> List[Dict]:
        """List all uploaded emails in S3."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=s3_prefix,
                Delimiter='/'
            )
            
            emails = []
            for obj in response.get('Contents', []):
                if obj['Key'].endswith('summary.json'):
                    # Get the summary file content
                    try:
                        response = self.s3_client.get_object(
                            Bucket=self.bucket,
                            Key=obj['Key']
                        )
                        summary = json.loads(response['Body'].read())
                        emails.append({
                            's3_key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat(),
                            'summary': summary
                        })
                    except Exception as e:
                        print(f"⚠️  Failed to read summary for {obj['Key']}: {e}")
            
            return emails
            
        except Exception as e:
            print(f"❌ Failed to list uploaded emails: {e}")
            return []
    
    def download_email_from_s3(self, s3_prefix: str, local_dir: Path = None) -> bool:
        """Download an email directory from S3 to local storage."""
        if not local_dir:
            local_dir = Path("data/downloaded_emails") / s3_prefix.split('/')[-1]
        
        local_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # List all objects with the prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=s3_prefix
            )
            
            for obj in response.get('Contents', []):
                # Calculate local file path
                relative_key = obj['Key'].replace(s3_prefix, '').lstrip('/')
                local_file = local_dir / relative_key
                local_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Download file
                self.s3_client.download_file(
                    self.bucket,
                    obj['Key'],
                    str(local_file)
                )
                print(f"   📥 {relative_key}")
            
            print(f"✅ Downloaded email to: {local_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to download email: {e}")
            return False

def main():
    """Main function to run S3 upload."""
    uploader = S3EmailUploader()
    
    # Upload all emails
    results = uploader.upload_all_emails()
    
    # List uploaded emails
    print(f"\n📋 Listing uploaded emails:")
    emails = uploader.list_uploaded_emails()
    for email in emails[:5]:  # Show first 5
        summary = email['summary']
        print(f"   - {summary.get('subject', 'No subject')} ({summary.get('email_id')})")
    
    return results

if __name__ == "__main__":
    main() 