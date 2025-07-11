#!/usr/bin/env python
"""Test script for Outlook integration functionality"""

import sys
from pathlib import Path

# Add repository root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_outlook_integration():
    """Test the Outlook integration functionality"""
    
    try:
        from app.email_ingest.outlook_integration import OutlookIntegration
        
        print("🔍 Testing Outlook Integration")
        print("=" * 50)
        
        # Test conversation ID
        conversation_id = "AAQkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZkLWFmYzJmM2YyOWZhOAAQAGFhYWFhYWFhYWFhYWFhYWE="
        
        print(f"Testing conversation ID: {conversation_id}")
        print()
        
        # Initialize Outlook integration
        outlook = OutlookIntegration()
        print("✅ Outlook integration initialized")
        
        # Test conversation location search
        print("\n🔍 Searching for conversation location...")
        success, url, metadata = outlook.find_conversation_location(conversation_id)
        
        if success:
            print(f"✅ Conversation found!")
            print(f"URL: {url}")
            print(f"URL Type: {metadata.get('url_type', 'unknown')}")
            print(f"Folder ID: {metadata.get('folder_id', 'N/A')}")
            print(f"Subject: {metadata.get('subject', 'N/A')}")
        else:
            print(f"❌ Conversation search failed: {metadata.get('error')}")
            print(f"Status: {metadata.get('status', 'unknown')}")
        
        # Test conversation summary
        print("\n📊 Getting conversation summary...")
        summary = outlook.get_conversation_summary(conversation_id)
        
        if "error" not in summary:
            print(f"✅ Conversation summary retrieved!")
            print(f"Total messages: {summary.get('total_messages', 0)}")
            print(f"First message subject: {summary.get('first_message', {}).get('subject', 'N/A')}")
            print(f"Last message subject: {summary.get('last_message', {}).get('subject', 'N/A')}")
        else:
            print(f"❌ Summary failed: {summary.get('error')}")
        
        print("\n🎉 Outlook integration test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_outlook_integration() 