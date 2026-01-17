#!/usr/bin/env python3
"""
SCHEMA ISOLATION VERIFICATION SCRIPT
=====================================

This script verifies that calliope tables are safely isolated in the 'calliope' schema
on shared PostgreSQL databases, ensuring no collisions with existing public schema tables.

USAGE:
    python verify_schema_isolation.py

ENVIRONMENT:
    Requires DATABASE_URL environment variable to be set.
    
WHAT IT CHECKS:
    1. PostgreSQL: Tables exist in calliope.words, calliope.config (NOT public.*)
    2. SQLite: Tables exist (no schema concept)
    3. No new tables were created in public schema
    4. Schema isolation is properly configured

EXIT CODES:
    0 = Safe (all checks passed)
    1 = Unsafe (schema isolation failed or errors detected)
    2 = Warning (minor issues detected)
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.db import verify_schema_isolation, DATABASE_URL, IS_POSTGRESQL, CALLIOPE_SCHEMA


def print_banner():
    """Print banner"""
    print("=" * 70)
    print("CALLIOPE SCHEMA ISOLATION VERIFICATION")
    print("=" * 70)
    print()


def print_result(verification: dict):
    """Print verification results in a readable format"""
    print(f"Database Type: {verification['database_type'].upper()}")
    print(f"Database URL:  {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else 'SQLite local'}")
    print()
    
    if IS_POSTGRESQL:
        print(f"Expected Schema: {CALLIOPE_SCHEMA}")
        print()
    
    # Print tables found
    if verification["tables_found"]:
        print("✓ Tables Found:")
        for table in verification["tables_found"]:
            print(f"  - {table}")
        print()
    else:
        print("✗ No tables found!")
        print()
    
    # Print public collisions (CRITICAL)
    if verification.get("public_tables_created"):
        print("✗ DANGER - Tables Found in Public Schema:")
        for table in verification["public_tables_created"]:
            print(f"  - public.{table}")
        print()
        print("⚠️  WARNING: These tables may collide with other apps on the shared database!")
        print()
    
    # Print errors
    if verification["errors"]:
        print("✗ Errors:")
        for error in verification["errors"]:
            print(f"  - {error}")
        print()
    
    # Print warnings
    if verification["warnings"]:
        print("⚠️  Warnings:")
        for warning in verification["warnings"]:
            print(f"  - {warning}")
        print()
    
    # Print status
    status_icon = {
        "ok": "✓",
        "warning": "⚠️",
        "error": "✗",
        "unknown": "?"
    }
    
    print(f"Status: {status_icon.get(verification['status'], '?')} {verification['status'].upper()}")
    
    if verification.get("message"):
        print(f"Message: {verification['message']}")
    
    print()
    
    # Print safety verdict
    print("=" * 70)
    if verification["safe"]:
        print("✓ SAFE: Schema isolation verified - safe to use in production")
        print("=" * 70)
        return 0
    elif verification["status"] == "warning":
        print("⚠️  WARNING: Review warnings before deploying to production")
        print("=" * 70)
        return 2
    else:
        print("✗ UNSAFE: Schema isolation FAILED - DO NOT use in production!")
        print("=" * 70)
        print()
        print("NEXT STEPS:")
        print("1. Check DATABASE_URL is correct")
        print("2. Ensure 'calliope' schema was created before running the app")
        print("3. Check for public schema collisions")
        print("4. Review error messages above")
        return 1


def main():
    """Main verification function"""
    print_banner()
    
    # Check environment
    if not os.getenv("DATABASE_URL"):
        print("✗ ERROR: DATABASE_URL environment variable not set")
        print()
        print("Please set DATABASE_URL and try again:")
        print("  export DATABASE_URL='your-database-url'")
        print()
        return 1
    
    # Run verification
    try:
        print("Running verification checks...")
        print()
        verification = verify_schema_isolation()
        return print_result(verification)
    
    except Exception as e:
        print(f"✗ FATAL ERROR during verification: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
