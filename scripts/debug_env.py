#!/usr/bin/env python
"""
Debug script to check environment variable loading
"""
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_env_file():
    """Check if .env file exists and show its contents."""
    print("🔍 Checking .env file...")
    
    # Check multiple possible locations
    possible_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent / ".env",
        Path.home() / ".env"
    ]
    
    env_found = False
    for env_path in possible_paths:
        if env_path.exists():
            print(f"✅ Found .env file at: {env_path}")
            env_found = True
            
            # Show first few lines (without revealing secrets)
            try:
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                    print(f"   File has {len(lines)} lines")
                    print("   First few lines:")
                    for i, line in enumerate(lines[:5]):
                        if line.strip() and not line.strip().startswith('#'):
                            # Show variable name but mask the value
                            if '=' in line:
                                var_name, var_value = line.split('=', 1)
                                masked_value = '*' * min(len(var_value.strip()), 10)
                                print(f"   {var_name}={masked_value}")
                            else:
                                print(f"   {line.strip()}")
                    if len(lines) > 5:
                        print(f"   ... and {len(lines) - 5} more lines")
            except Exception as e:
                print(f"   ❌ Error reading file: {e}")
            break
    
    if not env_found:
        print("❌ No .env file found in any of these locations:")
        for path in possible_paths:
            print(f"   - {path}")
    
    return env_found

def check_dotenv_loading():
    """Test dotenv loading."""
    print("\n📦 Testing dotenv loading...")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
        
        # Try loading from current directory
        result = load_dotenv()
        print(f"   load_dotenv() returned: {result}")
        
        # Try loading from specific path
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            result = load_dotenv(env_path, override=True)
            print(f"   load_dotenv('{env_path}') returned: {result}")
        
    except ImportError:
        print("❌ python-dotenv not installed")
        return False
    except Exception as e:
        print(f"❌ Error loading dotenv: {e}")
        return False
    
    return True

def check_environment_variables():
    """Check if environment variables are loaded."""
    print("\n🔧 Checking environment variables...")
    
    required_vars = [
        'GRAPH_TENANT_ID',
        'GRAPH_CLIENT_ID', 
        'GRAPH_CLIENT_SECRET',
        'SHARED_MAILBOX'
    ]
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked_value = '*' * min(len(value), 10)
            print(f"✅ {var}={masked_value}")
        else:
            print(f"❌ {var}=None")
            all_present = False
    
    return all_present

def check_settings_module():
    """Check if settings module loads correctly."""
    print("\n⚙️  Testing settings module...")
    
    try:
        from app.settings import settings
        print("✅ Settings module imported")
        
        # Check specific settings
        print(f"   GRAPH_TENANT_ID: {'✅ Set' if settings.GRAPH_TENANT_ID else '❌ None'}")
        print(f"   GRAPH_CLIENT_ID: {'✅ Set' if settings.GRAPH_CLIENT_ID else '❌ None'}")
        print(f"   GRAPH_CLIENT_SECRET: {'✅ Set' if settings.GRAPH_CLIENT_SECRET else '❌ None'}")
        print(f"   SHARED_MAILBOX: {'✅ Set' if settings.SHARED_MAILBOX else '❌ None'}")
        
        return True
    except Exception as e:
        print(f"❌ Error importing settings: {e}")
        return False

def main():
    """Run all debug checks."""
    print("🐛 Environment Variable Debug Tool")
    print("=" * 50)
    
    # Check 1: .env file exists
    env_exists = check_env_file()
    
    # Check 2: dotenv loading
    dotenv_works = check_dotenv_loading()
    
    # Check 3: environment variables
    env_vars_loaded = check_environment_variables()
    
    # Check 4: settings module
    settings_works = check_settings_module()
    
    print("\n" + "=" * 50)
    print("📊 Debug Summary:")
    print(f"   .env file exists: {'✅' if env_exists else '❌'}")
    print(f"   dotenv loading: {'✅' if dotenv_works else '❌'}")
    print(f"   env vars loaded: {'✅' if env_vars_loaded else '❌'}")
    print(f"   settings module: {'✅' if settings_works else '❌'}")
    
    if not env_exists:
        print("\n💡 Solution: Create a .env file in the project root")
    elif not env_vars_loaded:
        print("\n💡 Solution: Check .env file format - should be KEY=value")
    elif not settings_works:
        print("\n💡 Solution: Check for syntax errors in .env file")

if __name__ == "__main__":
    main() 