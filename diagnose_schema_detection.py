#!/usr/bin/env python3
"""
Schema Detection Diagnostic Script
===================================

Checks if schema detection is working correctly in backend/models.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("SCHEMA DETECTION DIAGNOSTIC")
print("=" * 70)
print()

# Check environment
print("1. Environment Variables:")
database_url = os.getenv("DATABASE_URL", "NOT SET")
print(f"   DATABASE_URL: {database_url[:50]}..." if len(database_url) > 50 else f"   DATABASE_URL: {database_url}")
print()

# Import and check models
print("2. Loading backend/models.py...")
try:
    from backend.models import IS_POSTGRESQL, CALLIOPE_SCHEMA, Word, Config, DATABASE_URL as MODEL_URL
    print("   [OK] Models loaded successfully")
    print()
    
    print("3. Schema Detection Results:")
    print(f"   DATABASE_URL in models: {MODEL_URL[:50]}..." if len(MODEL_URL) > 50 else f"   DATABASE_URL in models: {MODEL_URL}")
    print(f"   IS_POSTGRESQL: {IS_POSTGRESQL}")
    print(f"   CALLIOPE_SCHEMA: {CALLIOPE_SCHEMA}")
    print()
    
    print("4. Model __table_args__ Configuration:")
    print(f"   Word.__table_args__: {Word.__table_args__}")
    print(f"   Config.__table_args__: {Config.__table_args__}")
    print()
    
    # Check if schema is set
    if IS_POSTGRESQL:
        word_has_schema = any(isinstance(arg, dict) and arg.get('schema') == 'calliope' for arg in Word.__table_args__ if isinstance(arg, dict))
        config_has_schema = isinstance(Config.__table_args__, dict) and Config.__table_args__.get('schema') == 'calliope'
        
        print("5. Schema Assignment Verification:")
        print(f"   Word model has calliope schema: {word_has_schema}")
        print(f"   Config model has calliope schema: {config_has_schema}")
        print()
        
        if word_has_schema and config_has_schema:
            print("=" * 70)
            print("[OK] SCHEMA DETECTION WORKING CORRECTLY")
            print("=" * 70)
            print()
            print("Models are configured to use calliope schema.")
            print("Tables should be created in calliope schema on next deployment.")
        else:
            print("=" * 70)
            print("[ERROR] SCHEMA DETECTION FAILED")
            print("=" * 70)
            print()
            print("Models are NOT configured with calliope schema!")
            print("This will cause tables to be created in public schema.")
    else:
        print("5. SQLite Mode:")
        print("   Schema isolation not needed for SQLite")
        print("   Tables will be created without schema prefix")
    
except Exception as e:
    print(f"   [ERROR] Failed to load models: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
