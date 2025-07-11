#!/usr/bin/env python
"""
Outlook Integration for Email Thread Linking
Provides robust conversation search and folder-aware URL generation.
"""
import requests
import logging
from typing import Dict, Optional, Tuple
from app.settings import settings
from msal import ConfidentialClientApplication

logger = logging.getLogger(__name__)

class OutlookIntegration:
    def __init__(self):
        self.graph_root = "https://graph.microsoft.com/v1.0"
        self.token = None
        self.headers = self._get_auth_headers()

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Microsoft Graph API."""
        try:
            app = ConfidentialClientApplication(
                client_id=settings.GRAPH_CLIENT_ID,
                client_credential=settings.GRAPH_CLIENT_SECRET,
                authority=f"https://login.microsoftonline.com/{settings.GRAPH_TENANT_ID}"
            )
            
            token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            if "access_token" not in token:
                raise RuntimeError(f"Could not obtain token: {token.get('error_description')}")
                
            self.token = token["access_token"]
            return {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json"
            }
        except Exception as e:
            logger.error(f"Failed to get auth headers: {e}")
            raise

    def find_conversation_location(self, conversation_id: str, user_email: str = None) -> Tuple[bool, str, Dict]:
        """
        Find the current location of a conversation using known folder information.
        
        Returns:
            Tuple of (success, url, metadata)
        """
        if not conversation_id:
            return False, "", {"error": "No conversation ID provided"}
        
        user_email = user_email or settings.SHARED_MAILBOX
        
        try:
            # First, try to get the folder ID for the known mailbox folder
            folder_id = self._get_known_folder_id(user_email, settings.MAILBOX_FOLDER)
            
            if folder_id:
                # Use the known folder ID to create a precise URL
                folder_url = f"https://outlook.office.com/owa/?fid={folder_id}&conversationId={conversation_id}"
                metadata = {
                    "folder_id": folder_id,
                    "folder_name": settings.MAILBOX_FOLDER,
                    "url_type": "known_folder"
                }
                return True, folder_url, metadata
            
            # If we can't get the folder ID, fall back to simple conversation search
            logger.warning(f"Could not get folder ID for {settings.MAILBOX_FOLDER}, using fallback")
            fallback_url = f"https://outlook.office.com/owa/?conversationId={conversation_id}"
            metadata = {
                "error": "Could not resolve folder ID",
                "url_type": "fallback"
            }
            return True, fallback_url, metadata
                
        except Exception as e:
            logger.error(f"Error finding conversation location: {e}")
            return False, "", {"error": str(e), "status": 500}

    def _get_known_folder_id(self, user_email: str, folder_name: str) -> str:
        """Get the folder ID for a known folder name."""
        try:
            # Try to get the folder as a well-known folder first
            url = f"{self.graph_root}/users/{user_email}/mailFolders/{folder_name}"
            resp = requests.get(url, headers=self.headers)
            
            if resp.status_code == 200:
                folder = resp.json()
                return folder.get("id")
            
            # If it's not a well-known folder, try to find it as a subfolder
            return self._find_subfolder_by_name(user_email, folder_name)
            
        except Exception as e:
            logger.error(f"Error getting folder ID for {folder_name}: {e}")
            return None

    def _find_subfolder_by_name(self, user_email: str, folder_name: str) -> str:
        """Find a subfolder by name by searching through all folders."""
        try:
            # Get all mail folders
            url = f"{self.graph_root}/users/{user_email}/mailFolders"
            resp = requests.get(url, headers=self.headers)
            
            if resp.status_code != 200:
                return None
            
            folders = resp.json().get("value", [])
            
            # Search for the folder by name
            for folder in folders:
                if folder.get("displayName") == folder_name:
                    return folder.get("id")
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding subfolder {folder_name}: {e}")
            return None

    def validate_message_exists(self, user_email: str, message_id: str) -> Tuple[bool, str]:
        """Validate that a specific message still exists."""
        try:
            url = f"{self.graph_root}/users/{user_email}/messages/{message_id}"
            resp = requests.get(url, headers=self.headers)
            
            if resp.status_code == 404:
                return False, "Message not found"
            if resp.status_code == 401:
                return False, "Authentication failed"
            if resp.status_code != 200:
                return False, f"API error: {resp.status_code}"
            
            return True, "Message exists"
            
        except Exception as e:
            logger.error(f"Error validating message: {e}")
            return False, str(e)

    def get_conversation_summary(self, conversation_id: str, user_email: str = None) -> Dict:
        """Get summary information about a conversation."""
        user_email = user_email or settings.SHARED_MAILBOX
        
        try:
            # Get folder ID first
            folder_id = self._get_known_folder_id(user_email, settings.MAILBOX_FOLDER)
            
            if not folder_id:
                return {"error": "Could not resolve folder ID"}
            
            # Search within the known folder to avoid InefficientFilter
            url = (f"{self.graph_root}/users/{user_email}/mailFolders/{folder_id}/messages"
                   f"?$filter=conversationId eq '{conversation_id}'"
                   f"&$top=10")
            
            resp = requests.get(url, headers=self.headers)
            
            if resp.status_code != 200:
                return {"error": f"API error: {resp.status_code}"}
            
            data = resp.json()
            messages = data.get("value", [])
            
            if not messages:
                return {"error": "Conversation not found in known folder"}
            
            # Get conversation summary
            first_message = messages[0]
            last_message = messages[-1]
            
            return {
                "total_messages": len(messages),
                "folder_name": settings.MAILBOX_FOLDER,
                "first_message": {
                    "subject": first_message.get("subject"),
                    "received": first_message.get("receivedDateTime"),
                    "from": first_message.get("from", {}).get("emailAddress", {}).get("address")
                },
                "last_message": {
                    "subject": last_message.get("subject"),
                    "received": last_message.get("receivedDateTime"),
                    "from": last_message.get("from", {}).get("emailAddress", {}).get("address")
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {"error": str(e)} 