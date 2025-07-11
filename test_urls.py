#!/usr/bin/env python
"""
Test these URL formats with your specific email and conversation IDs
"""
import urllib.parse

# Your actual IDs from the debug output
EMAIL_ID = "AAMkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZkLWFmYzJmM2YyOWZhOABGAAAAAAAiQ8W967B7TKBjgx9rVEURBwAiIsqMbYjsT5G-T7KZ11NPAAAAAAEMAAAiIsqMbYjsT5G-T7KZ11NPAAAAAAE_AAA="
CONVERSATION_ID = "AAQkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZkLWFmYzJmM2YyOWZhOAAQAGFhYWFhYWFhYWFhYWFhYWE="

def generate_test_urls():
    """Generate all possible URL formats to test."""
    
    # Clean IDs (remove any existing URL encoding)
    clean_email = urllib.parse.unquote(EMAIL_ID)
    clean_conv = urllib.parse.unquote(CONVERSATION_ID)
    
    print("🧪 URL FORMATS TO TEST")
    print("=" * 80)
    print(f"Email ID: {EMAIL_ID}")
    print(f"Conversation ID: {CONVERSATION_ID}")
    print("=" * 80)
    
    test_urls = [
        # Message URL Formats
        ("1. Modern Parameter Format (RECOMMENDED)", 
         f"https://outlook.office.com/mail/inbox?messageId={urllib.parse.quote(clean_email, safe='')}"),
        
        ("2. OWA ItemID Format", 
         f"https://outlook.office.com/owa/?ItemID={urllib.parse.quote(clean_email, safe='')}&exvsurl=1&viewmodel=ReadMessageItem"),
        
        ("3. OWA Simple ItemID", 
         f"https://outlook.office.com/owa/?ItemID={urllib.parse.quote(clean_email, safe='')}"),
        
        ("4. Your Current Format (Legacy Path)", 
         f"https://outlook.office.com/mail/inbox/id/{urllib.parse.quote(clean_email, safe='')}"),
        
        ("5. Deep Link Read Format", 
         f"https://outlook.office.com/mail/deeplink/read?messageId={urllib.parse.quote(clean_email, safe='')}"),
        
        ("6. Mail Reader Format", 
         f"https://outlook.office.com/mail/reader?messageId={urllib.parse.quote(clean_email, safe='')}"),
        
        ("7. Direct Message Access", 
         f"https://outlook.office.com/mail/id/{urllib.parse.quote(clean_email, safe='')}"),
        
        ("8. Without URL Encoding (Raw)", 
         f"https://outlook.office.com/mail/inbox?messageId={clean_email}"),
        
        # Conversation URL Formats
        ("9. Modern Conversation Parameter", 
         f"https://outlook.office.com/mail/inbox?conversationId={urllib.parse.quote(clean_conv, safe='')}"),
        
        ("10. Legacy Conversation Path", 
         f"https://outlook.office.com/mail/inbox/conversation/{urllib.parse.quote(clean_conv, safe='')}"),
        
        ("11. Conversation Deep Link", 
         f"https://outlook.office.com/mail/deeplink/conversation?conversationId={urllib.parse.quote(clean_conv, safe='')}"),
        
        ("12. Raw Conversation (No Encoding)", 
         f"https://outlook.office.com/mail/inbox?conversationId={clean_conv}"),
    ]
    
    for name, url in test_urls:
        print(f"\n{name}:")
        print(f"   {url}")
        print(f"   Length: {len(url)} chars")
    
    print("\n" + "=" * 80)
    print("🔍 TESTING INSTRUCTIONS:")
    print("1. Copy each URL and test in your browser while logged into Outlook")
    print("2. Note which ones successfully open the email/conversation")
    print("3. Look for URLs that take you directly to the message vs. just the inbox")
    print("4. Test both when the email is in Inbox and after it's moved to other folders")
    
    print("\n💡 EXPECTED RESULTS:")
    print("✅ SUCCESS: Opens the specific email or conversation thread")
    print("❌ PARTIAL: Redirects to main inbox (what you're experiencing now)")
    print("❌ FAIL: Shows error or doesn't load")
    
    print("\n🚨 COMMON ISSUES:")
    print("- URL encoding problems (= vs %3D)")
    print("- Email moved to different folder")
    print("- Organization-specific Outlook configuration")
    print("- Email ID format changed between Outlook versions")
    
    return test_urls

if __name__ == "__main__":
    urls = generate_test_urls()
    
    # Also print them as a simple list for easy copying
    print("\n" + "=" * 80)
    print("📋 QUICK COPY LIST:")
    print("=" * 80)
    for i, (name, url) in enumerate(urls, 1):
        print(f"{i}. {url}")