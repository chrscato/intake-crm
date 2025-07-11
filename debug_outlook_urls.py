#!/usr/bin/env python
"""Debug script to test Outlook URL generation"""

import urllib.parse

def get_outlook_web_url(email_id):
    """Generate Outlook web URL for the specific email."""
    if not email_id:
        return ""
    # URL encode the email_id to handle special characters
    encoded_id = urllib.parse.quote(email_id, safe='')
    return f"https://outlook.office.com/mail/inbox/id/{encoded_id}"

def get_outlook_conversation_url(conversation_id):
    """Generate Outlook web URL for the conversation thread."""
    if not conversation_id:
        return ""
    # URL encode the conversation_id to handle special characters
    encoded_id = urllib.parse.quote(conversation_id, safe='')
    return f"https://outlook.office.com/mail/inbox/conversation/{encoded_id}"

def test_url_generation():
    """Test URL generation with sample data"""
    
    # Sample email IDs from your system
    email_id = "AAMkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZkLWFmYzJmM2YyOWZhOABGAAAAAAAiQ8W967B7TKBjgx9rVEURBwAiIsqMbYjsT5G-T7KZ11NPAAAAAAEMAAAiIsqMbYjsT5G-T7KZ11NPAAAAAAE_AAA="
    conversation_id = "AAQkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZkLWFmYzJmM2YyOWZhOAAQAGFhYWFhYWFhYWFhYWFhYWE="
    
    print("🔍 Testing Outlook URL Generation")
    print("=" * 50)
    
    print(f"Email ID: {email_id}")
    print(f"Conversation ID: {conversation_id}")
    print()
    
    print("📧 Email URL (encoded):")
    email_url = get_outlook_web_url(email_id)
    print(email_url)
    print()
    
    print("💬 Conversation URL (encoded):")
    conversation_url = get_outlook_conversation_url(conversation_id)
    print(conversation_url)
    print()
    
    print("🔗 Alternative URL formats to try:")
    print(f"1. Graph API: https://graph.microsoft.com/v1.0/me/messages/{email_id}")
    print(f"2. OWA: https://outlook.office.com/owa/?ItemID={email_id}")
    print(f"3. Read: https://outlook.office.com/mail/inbox/id/{email_id}/read")
    print(f"4. Deep Link: https://outlook.office.com/mail/deeplink/compose?messageId={email_id}")
    print(f"5. Simple: https://outlook.office.com/mail/inbox/id/{email_id}")
    print()
    
    print("🔧 URL Encoding Test:")
    print(f"Original email_id: {email_id}")
    print(f"URL encoded: {urllib.parse.quote(email_id, safe='')}")
    print(f"Double encoded: {urllib.parse.quote(urllib.parse.quote(email_id, safe=''), safe='')}")

if __name__ == "__main__":
    test_url_generation() 