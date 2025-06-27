#!/usr/bin/env python
"""
Test script for Email Ingestion System
Verifies configuration and basic functionality.
"""
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_environment():
    """Test environment variables are set."""
    print("🔧 Testing Environment Configuration...")
    
    try:
        from app.settings import settings
        
        required_vars = [
            ('GRAPH_TENANT_ID', settings.GRAPH_TENANT_ID),
            ('GRAPH_CLIENT_ID', settings.GRAPH_CLIENT_ID),
            ('GRAPH_CLIENT_SECRET', settings.GRAPH_CLIENT_SECRET),
            ('SHARED_MAILBOX', settings.SHARED_MAILBOX)
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            print("   Please check your .env file")
            return False
        else:
            print("✅ All required environment variables are set")
            return True
            
    except Exception as e:
        print(f"❌ Error checking environment: {e}")
        return False

def test_imports():
    """Test that all modules can be imported."""
    print("\n📦 Testing Module Imports...")
    
    try:
        from app.settings import settings
        print("✅ Settings module imported")
    except Exception as e:
        print(f"❌ Failed to import settings: {e}")
        return False
    
    try:
        from app.email_ingest.email_processor import EmailProcessor
        print("✅ EmailProcessor imported")
    except Exception as e:
        print(f"❌ Failed to import EmailProcessor: {e}")
        return False
    
    try:
        from app.email_ingest.s3_uploader import S3EmailUploader
        print("✅ S3EmailUploader imported")
    except Exception as e:
        print(f"❌ Failed to import S3EmailUploader: {e}")
        return False
    
    return True

def test_authentication():
    """Test Microsoft Graph authentication."""
    print("\n🔐 Testing Microsoft Graph Authentication...")
    
    try:
        from app.email_ingest.email_processor import EmailProcessor
        processor = EmailProcessor()
        print("✅ Authentication successful")
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("   Please check your Microsoft Graph API credentials")
        return False

def test_s3_configuration():
    """Test S3 configuration (if AWS credentials are provided)."""
    print("\n☁️  Testing S3 Configuration...")
    
    try:
        from app.settings import settings
        aws_vars = [settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, settings.S3_BUCKET]
        missing_aws = [i for i, var in enumerate(['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET']) if not aws_vars[i]]
        
        if missing_aws:
            print(f"⚠️  S3 not configured (missing: {', '.join([['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET'][i] for i in missing_aws])})")
            print("   S3 upload functionality will not be available")
            return True  # Not a critical failure
        
        from app.email_ingest.s3_uploader import S3EmailUploader
        uploader = S3EmailUploader()
        print("✅ S3 configuration successful")
        return True
    except Exception as e:
        print(f"❌ S3 configuration failed: {e}")
        return False

def test_directory_structure():
    """Test that required directories exist or can be created."""
    print("\n📁 Testing Directory Structure...")
    
    data_dir = Path("data")
    emails_dir = data_dir / "emails"
    
    try:
        emails_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Data directory ready: {emails_dir}")
        return True
    except Exception as e:
        print(f"❌ Failed to create data directory: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Email Ingestion System Test Suite")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_imports,
        test_authentication,
        test_s3_configuration,
        test_directory_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Run: python scripts/run_email_ingestion.py")
        print("2. Check the EMAIL_INGESTION_README.md for detailed usage")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 