#!/usr/bin/env python
"""
Email Ingestion Processor
Fetches emails with metadata and attachments, saves locally, and provides S3 upload capability.
"""
import os
import json
import requests
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from msal import ConfidentialClientApplication
from app.settings import settings

class EmailProcessor:
    def __init__(self):
        self.graph_root = "https://graph.microsoft.com/v1.0"
        self.headers = self._get_auth_headers()
        self.data_dir = Path("data/emails")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Microsoft Graph API."""
        app = ConfidentialClientApplication(
            client_id=settings.GRAPH_CLIENT_ID,
            client_credential=settings.GRAPH_CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{settings.GRAPH_TENANT_ID}"
        )
        
        token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in token:
            raise RuntimeError(f"❌ Couldn't obtain token: {token.get('error_description')}")
            
        return {
            "Authorization": f"Bearer {token['access_token']}",
            "Accept": "application/json"
        }
    
    def get_folder_id(self, user: str, path_segments: List[str]) -> str:
        """Walk a human path like ['Inbox','foo','bar'] and return folderId."""
        # First segment may be special well-known folder; get its id quickly
        seg0 = path_segments[0]
        
        # Try to get the folder as a well-known folder first
        try:
            resp = requests.get(f"{self.graph_root}/users/{user}/mailFolders/{seg0}", headers=self.headers)
            if resp.status_code == 200:
                folder = resp.json()
            else:
                # If it's not a well-known folder, try to find it as a subfolder
                folder = self._find_subfolder_by_name(user, seg0)
                if not folder:
                    raise RuntimeError(f"Cannot find folder {seg0}: {resp.text}")
        except Exception as e:
            # Try to find it as a subfolder
            folder = self._find_subfolder_by_name(user, seg0)
            if not folder:
                raise RuntimeError(f"Cannot find folder {seg0}: {str(e)}")
        
        # Walk through remaining path segments
        for name in path_segments[1:]:
            escaped_name = name.replace("'", "''")
            q = (f"{self.graph_root}/users/{user}/mailFolders/{folder['id']}/childFolders"
                 f"?$filter=displayName eq '{escaped_name}'"
                 f"&$select=id,displayName")
            resp = requests.get(q, headers=self.headers)
            data = resp.json().get("value", [])
            if not data:
                # create it and continue
                body = {"displayName": name, "isHidden": False}
                resp = requests.post(
                    f"{self.graph_root}/users/{user}/mailFolders/{folder['id']}/childFolders",
                    headers={**self.headers, "Content-Type": "application/json"},
                    data=json.dumps(body)
                )
                if resp.status_code not in (200, 201):
                    raise RuntimeError(f"Cannot create/find folder {name}: {resp.text}")
                data = [resp.json()]
            folder = data[0]
        return folder["id"]
    
    def _find_subfolder_by_name(self, user: str, folder_name: str) -> Optional[Dict]:
        """Find a subfolder by name by searching through all folders."""
        # Get all mail folders
        url = f"{self.graph_root}/users/{user}/mailFolders"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code != 200:
            return None
        
        folders = resp.json().get("value", [])
        
        # Search for the folder by name
        for folder in folders:
            if folder.get("displayName") == folder_name:
                return folder
        
        return None
    
    def is_original_inbound_email(self, email_data: Dict) -> bool:
        """Check if this is an original inbound email using robust conversation analysis."""
        # Method 1: Check if this is the first message in a conversation
        conversation_id = email_data.get('conversationId')
        if conversation_id:
            # Get all messages in this conversation to see if this is the first
            if not self._is_first_in_conversation(email_data):
                return False
        
        # Method 2: Check subject line for reply indicators (backup method)
        subject = email_data.get('subject', '').lower()
        reply_indicators = [
            're:', 're :', 're-', 're -',
            'fw:', 'fw :', 'fw-', 'fw -',
            'fwd:', 'fwd :', 'fwd-', 'fwd -',
            'reply:', 'reply :', 'reply-', 'reply -'
        ]
        
        for indicator in reply_indicators:
            if subject.startswith(indicator):
                return False
        
        # Method 3: Check sender - skip internal emails
        from_info = email_data.get('from', {})
        from_email = from_info.get('emailAddress', {}).get('address', '').lower()
        
        # Skip if it's from the same mailbox (internal emails)
        if from_email == self.current_mailbox.lower():
            return False
        
        # Skip if it's from common internal domains
        internal_domains = ['clarity-dx.com', 'yourcompany.com']  # Add your internal domains
        for domain in internal_domains:
            if domain in from_email:
                return False
        
        return True
    
    def _is_first_in_conversation(self, email_data: Dict) -> bool:
        """Check if this email is the first message in its conversation."""
        conversation_id = email_data.get('conversationId')
        message_id = email_data.get('id')
        received_time = email_data.get('receivedDateTime')
        
        if not conversation_id or not message_id or not received_time:
            return True  # If we can't determine, assume it's original
        
        try:
            # Use a simpler query without ordering to avoid "InefficientFilter" error
            url = (f"{self.graph_root}/users/{self.current_mailbox}/messages"
                   f"?$filter=conversationId eq '{conversation_id}'"
                   f"&$select=id,receivedDateTime,subject"
                   f"&$top=10")  # Limit to first 10 messages in conversation
            
            resp = requests.get(url, headers=self.headers)
            if resp.status_code != 200:
                print(f"⚠️  Could not fetch conversation: {resp.text}")
                return True  # Assume original if we can't check
            
            conversation_messages = resp.json().get("value", [])
            
            if not conversation_messages:
                return True
            
            # Find the earliest message by received time
            earliest_message = min(conversation_messages, 
                                 key=lambda x: x.get('receivedDateTime', '9999-12-31T23:59:59Z'))
            
            # Check if this message is the earliest one
            if earliest_message.get('id') == message_id:
                return True
            
            # Additional check: if this message was received before the earliest message
            earliest_time = earliest_message.get('receivedDateTime')
            if earliest_time and received_time < earliest_time:
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️  Error checking conversation order: {e}")
            return True  # Assume original if we can't check
    
    def get_conversation_analysis(self, email_data: Dict) -> Dict:
        """Get detailed analysis of a conversation for debugging."""
        conversation_id = email_data.get('conversationId')
        message_id = email_data.get('id')
        
        if not conversation_id:
            return {"error": "No conversation ID"}
        
        try:
            # Use simpler query to avoid "InefficientFilter" error
            url = (f"{self.graph_root}/users/{self.current_mailbox}/messages"
                   f"?$filter=conversationId eq '{conversation_id}'"
                   f"&$select=id,receivedDateTime,subject,from"
                   f"&$top=10")  # Limit results
            
            resp = requests.get(url, headers=self.headers)
            if resp.status_code != 200:
                return {"error": f"API error: {resp.text}"}
            
            messages = resp.json().get("value", [])
            
            # Sort by received time manually
            messages.sort(key=lambda x: x.get('receivedDateTime', '9999-12-31T23:59:59Z'))
            
            analysis = {
                "conversation_id": conversation_id,
                "total_messages": len(messages),
                "current_message_position": None,
                "messages": []
            }
            
            for i, msg in enumerate(messages):
                is_current = msg.get('id') == message_id
                if is_current:
                    analysis["current_message_position"] = i + 1
                
                analysis["messages"].append({
                    "position": i + 1,
                    "id": msg.get('id'),
                    "subject": msg.get('subject'),
                    "received": msg.get('receivedDateTime'),
                    "from": msg.get('from', {}).get('emailAddress', {}).get('address'),
                    "is_current": is_current
                })
            
            return analysis
            
        except Exception as e:
            return {"error": f"Exception: {str(e)}"}
    
    def iter_messages(self, user: str, folder_id: str, page_size: int = 50, original_only: bool = True):
        """Yield messages page-by-page, optionally filtering for original inbound emails."""
        url = (f"{self.graph_root}/users/{user}/mailFolders/{folder_id}/messages"
               f"?$select=id,subject,hasAttachments,receivedDateTime,from,toRecipients,ccRecipients,bccRecipients,body,importance,isRead,conversationId,uniqueBody&$top={page_size}")
        
        self.current_mailbox = user  # Store for filtering
        
        while url:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Message fetch failed: {resp.text}")
            data = resp.json()
            for m in data.get("value", []):
                # Apply filtering if requested
                if original_only and not self.is_original_inbound_email(m):
                    continue
                yield m
            url = data.get("@odata.nextLink")
    
    def get_attachments(self, user: str, msg_id: str) -> List[Dict]:
        """Get all attachments for a message."""
        url = f"{self.graph_root}/users/{user}/messages/{msg_id}/attachments?$select=id,name,contentType,size"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code != 200:
            print(f"⚠️  Failed to fetch attachments: {resp.text}")
            return []
        return resp.json().get("value", [])
    
    def download_attachment(self, user: str, msg_id: str, attachment: Dict) -> Optional[bytes]:
        """Download a single attachment."""
        att_id = attachment["id"]
        filename = attachment["name"]
        
        # Always download using the $value endpoint for consistency
        url = f"{self.graph_root}/users/{user}/messages/{msg_id}/attachments/{att_id}/$value"
        r = requests.get(url, headers=self.headers)
        if r.status_code != 200:
            print(f"⚠️  Cannot download {filename}: {r.text}")
            return None
        bin_data = r.content
        
        return bin_data
    
    def save_email_data(self, email_data: Dict, attachments: List[Tuple[str, bytes]]) -> str:
        """Save email metadata and attachments to local storage."""
        # Create timestamp-based directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        email_id = email_data.get('id', 'unknown')
        
        # Better filename sanitization for Windows
        subject = email_data.get('subject', 'no_subject')
        # Remove or replace problematic characters
        safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_', '.'))
        safe_subject = safe_subject.replace(' ', '_').replace('__', '_').strip('_')
        safe_subject = safe_subject[:30]  # Limit length more aggressively
        
        # Create a shorter, safer directory name
        email_dir = self.data_dir / f"{timestamp}_{email_id[:20]}_{safe_subject}"
        email_dir.mkdir(parents=True, exist_ok=True)
        
        # Save email metadata
        metadata_file = email_dir / "email_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(email_data, f, indent=2, default=str)
        
        # Save attachments
        attachments_dir = email_dir / "attachments"
        attachments_dir.mkdir(exist_ok=True)
        
        saved_attachments = []
        for filename, content in attachments:
            if content:
                # Sanitize attachment filename
                safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.'))
                safe_filename = safe_filename.replace(' ', '_')
                
                file_path = attachments_dir / safe_filename
                # Handle duplicate filenames
                counter = 1
                original_path = file_path
                while file_path.exists():
                    stem = original_path.stem
                    suffix = original_path.suffix
                    file_path = original_path.parent / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                saved_attachments.append(str(file_path.relative_to(email_dir)))
        
        # Create summary file
        summary = {
            "email_id": email_id,
            "subject": email_data.get('subject'),
            "received_datetime": email_data.get('receivedDateTime'),
            "from": email_data.get('from'),
            "to_recipients": email_data.get('toRecipients'),
            "has_attachments": email_data.get('hasAttachments'),
            "attachments_count": len(attachments),
            "saved_attachments": saved_attachments,
            "processed_at": datetime.now().isoformat()
        }
        
        summary_file = email_dir / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return str(email_dir)
    
    def move_message(self, user: str, msg_id: str, dest_folder_id: str) -> bool:
        """Move a message to a different folder."""
        url = f"{self.graph_root}/users/{user}/messages/{msg_id}/move"
        body = {"destinationId": dest_folder_id}
        resp = requests.post(
            url, 
            headers={**self.headers, "Content-Type": "application/json"},
            data=json.dumps(body)
        )
        return resp.status_code in (200, 201)
    
    def process_emails(self, 
                      mailbox: str = None, 
                      src_path: List[str] = None,
                      dest_folder: str = "archive_processed",
                      move_processed: bool = True,
                      max_emails: int = None,
                      original_only: bool = True,
                      debug_conversations: bool = False) -> Dict:
        """Main method to process emails from a folder."""
        mailbox = mailbox or settings.SHARED_MAILBOX
        src_path = src_path or [settings.MAILBOX_FOLDER]
        
        print(f"🔍 Looking for messages in {mailbox}/{'/'.join(src_path)}")
        
        # Get source and destination folder IDs
        src_id = self.get_folder_id(mailbox, src_path)
        print(f"📁 Source folder ID: {src_id}")
        
        dest_id = None
        if move_processed:
            dest_id = self.get_folder_id(mailbox, src_path + [dest_folder])
            print(f"📁 Destination folder ID: {dest_id}")
        
        processed = 0
        message_count = 0
        skipped_count = 0
        results = {
            "total_messages": 0,
            "processed_messages": 0,
            "failed_messages": 0,
            "skipped_messages": 0,
            "total_attachments": 0,
            "saved_locations": []
        }
        
        for msg in self.iter_messages(mailbox, src_id, original_only=original_only):
            if max_emails and message_count >= max_emails:
                break
                
            message_count += 1
            results["total_messages"] += 1
            
            # Check if this is an original inbound email
            if original_only and not self.is_original_inbound_email(msg):
                skipped_count += 1
                results["skipped_messages"] += 1
                print(f"⏭️  Skipping reply/forward: {msg.get('subject', '(no subject)')[:60]}")
                
                # Show conversation analysis if debug is enabled
                if debug_conversations:
                    analysis = self.get_conversation_analysis(msg)
                    if "error" not in analysis:
                        print(f"   📊 Conversation: {analysis['total_messages']} messages, this is #{analysis['current_message_position']}")
                        for m in analysis['messages'][:3]:  # Show first 3 messages
                            marker = " 👈 CURRENT" if m['is_current'] else ""
                            print(f"   {m['position']}. {m['subject'][:40]}... ({m['from']}){marker}")
                        if analysis['total_messages'] > 3:
                            print(f"   ... and {analysis['total_messages'] - 3} more messages")
                    else:
                        print(f"   ⚠️  Could not analyze conversation: {analysis['error']}")
                continue
            
            print(f"\n📧 Processing message {message_count}: {msg.get('subject', '(no subject)')}")
            print(f"   Received: {msg.get('receivedDateTime')}")
            print(f"   From: {msg.get('from', {}).get('emailAddress', {}).get('address', 'unknown')}")
            print(f"   Has Attachments: {msg.get('hasAttachments')}")
            
            # Show conversation analysis if debug is enabled
            if debug_conversations:
                analysis = self.get_conversation_analysis(msg)
                if "error" not in analysis:
                    print(f"   📊 Conversation: {analysis['total_messages']} messages, this is #{analysis['current_message_position']}")
                    if analysis['total_messages'] > 1:
                        print(f"   ✅ Original message in conversation")
                else:
                    print(f"   ⚠️  Could not analyze conversation: {analysis['error']}")
            
            try:
                # Get attachments
                attachments = self.get_attachments(mailbox, msg['id'])
                print(f"📎 Found {len(attachments)} attachments:")
                
                # Download attachments
                downloaded_attachments = []
                for att in attachments:
                    print(f"   - {att.get('name')} ({att.get('contentType')}, {att.get('size')} bytes)")
                    content = self.download_attachment(mailbox, msg['id'], att)
                    if content:
                        downloaded_attachments.append((att.get('name'), content))
                        results["total_attachments"] += 1
                
                # Save everything locally
                saved_location = self.save_email_data(msg, downloaded_attachments)
                results["saved_locations"].append(saved_location)
                
                print(f"✅ Saved to: {saved_location}")
                
                # Move message if requested
                if move_processed and dest_id:
                    moved = self.move_message(mailbox, msg['id'], dest_id)
                    state = "✅ saved & moved" if moved else "⚠️  saved, move failed"
                    print(f"{state}: {msg.get('subject','(no subject)')[:60]}")
                
                processed += 1
                results["processed_messages"] += 1
                
            except Exception as e:
                print(f"❌ Failed to process message: {e}")
                results["failed_messages"] += 1
        
        print(f"\n📊 Summary:")
        print(f"- Total messages found: {results['total_messages']}")
        print(f"- Original inbound emails: {results['processed_messages']}")
        print(f"- Skipped replies/forwards: {results['skipped_messages']}")
        print(f"- Failed to process: {results['failed_messages']}")
        print(f"- Total attachments: {results['total_attachments']}")
        print(f"- Data saved to: {self.data_dir}")
        
        return results

def main():
    """Main function to run email processing."""
    processor = EmailProcessor()
    
    # You can customize these parameters or use environment variables
    mailbox = settings.SHARED_MAILBOX
    src_path = [settings.MAILBOX_FOLDER]  # Default to Inbox
    
    # Process emails
    results = processor.process_emails(
        mailbox=mailbox,
        src_path=src_path,
        move_processed=True,
        max_emails=10,  # Limit for testing
        original_only=True,
        debug_conversations=True
    )
    
    return results

if __name__ == "__main__":
    main() 