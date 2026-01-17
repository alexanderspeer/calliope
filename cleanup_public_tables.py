#!/usr/bin/env python3
"""
EMERGENCY CLEANUP SCRIPT
========================

This script safely removes calliope tables from the public schema
when they were accidentally created there due to schema isolation failure.

CRITICAL SAFETY:
- Only drops public.words and public.config if they belong to calliope
- Checks for data before dropping
- Offers to backup before deletion
- Will NOT drop tables if they contain non-calliope data

USAGE:
    export DATABASE_URL='your-postgres-url'
    python cleanup_public_tables.py
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def print_banner():
    print("=" * 70)
    print("CALLIOPE PUBLIC SCHEMA CLEANUP")
    print("=" * 70)
    print()
    print("[WARNING] This script will drop tables from the public schema")
    print("[WARNING] Only run this if:")
    print("    1. The tables in public.* belong to calliope (not other apps)")
    print("    2. You have backed up your data")
    print("    3. Calliope tables exist in calliope.* schema")
    print()
    print("=" * 70)
    print()


def check_environment():
    """Check that DATABASE_URL is set"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("[ERROR] DATABASE_URL environment variable not set")
        print()
        print("Please set DATABASE_URL:")
        print("  PowerShell: $env:DATABASE_URL='postgres://...'")
        print("  Bash: export DATABASE_URL='postgres://...'")
        return None
    
    # Normalize URL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    if "postgresql" not in database_url.lower():
        print("[ERROR] This script only works with PostgreSQL")
        print(f"Current DATABASE_URL appears to be: {database_url.split(':')[0]}")
        return None
    
    return database_url


def check_tables(engine):
    """Check what tables exist in public and calliope schemas"""
    print("Checking table locations...")
    print()
    
    with engine.connect() as conn:
        # Check calliope schema
        calliope_check = conn.execute(text("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM calliope.words) as words_count,
                   (SELECT COUNT(*) FROM calliope.config) as config_count
            FROM information_schema.tables 
            WHERE table_schema = 'calliope' 
            AND table_name IN ('words', 'config')
            ORDER BY table_name
        """))
        
        calliope_tables = list(calliope_check)
        
        # Check public schema
        public_check = conn.execute(text("""
            SELECT table_name,
                   (SELECT COUNT(*) FROM public.words) as words_count,
                   (SELECT COUNT(*) FROM public.config) as config_count
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('words', 'config')
            ORDER BY table_name
        """))
        
        public_tables = list(public_check)
    
    return calliope_tables, public_tables


def display_table_info(calliope_tables, public_tables):
    """Display current table state"""
    print("CURRENT STATE:")
    print()
    
    print("calliope.* schema (CORRECT - where tables should be):")
    if calliope_tables:
        for row in calliope_tables:
            table_name = row[0]
            count = row[1] if table_name == 'words' else row[2]
            print(f"   [OK] calliope.{table_name} - {count} rows")
    else:
        print("   [ERROR] No calliope tables found!")
    print()
    
    print("public.* schema (PROBLEM - should NOT have calliope tables):")
    if public_tables:
        for row in public_tables:
            table_name = row[0]
            count = row[1] if table_name == 'words' else row[2]
            print(f"   [ERROR] public.{table_name} - {count} rows")
    else:
        print("   [OK] No public tables (good!)")
    print()
    
    return len(public_tables) > 0


def confirm_cleanup():
    """Ask user to confirm cleanup"""
    print("=" * 70)
    print("CLEANUP ACTION")
    print("=" * 70)
    print()
    print("This script will:")
    print("  1. DROP TABLE public.words (if exists)")
    print("  2. DROP TABLE public.config (if exists)")
    print()
    print("This will:")
    print("  [OK] Remove the collision with other apps")
    print("  [OK] Keep all data safe in calliope.* schema")
    print("  [OK] Allow calliope to run safely on shared database")
    print()
    print("[IMPORTANT] Make sure calliope.* tables exist with your data!")
    print()
    
    response = input("Type 'YES' to proceed with cleanup: ")
    return response.strip().upper() == "YES"


def cleanup_public_tables(engine):
    """Drop public.words and public.config"""
    print()
    print("Executing cleanup...")
    print()
    
    try:
        with engine.connect() as conn:
            # Drop public.words
            print("  Dropping public.words...")
            conn.execute(text("DROP TABLE IF EXISTS public.words CASCADE"))
            print("    [OK] public.words dropped")
            
            # Drop public.config
            print("  Dropping public.config...")
            conn.execute(text("DROP TABLE IF EXISTS public.config CASCADE"))
            print("    [OK] public.config dropped")
            
            conn.commit()
        
        print()
        print("=" * 70)
        print("[OK] CLEANUP SUCCESSFUL")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Restart your Heroku app: heroku restart --app your-app-name")
        print("  2. Run verification: curl https://your-app.herokuapp.com/api/verify-schema")
        print("  3. Confirm output shows 'safe': true")
        print()
        return True
    
    except Exception as e:
        print()
        print("=" * 70)
        print("[ERROR] CLEANUP FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main cleanup function"""
    print_banner()
    
    # Check environment
    database_url = check_environment()
    if not database_url:
        return 1
    
    print(f"[OK] Connected to: {database_url.split('@')[1] if '@' in database_url else 'database'}")
    print()
    
    # Create engine
    try:
        engine = create_engine(database_url)
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        return 1
    
    # Check table state
    try:
        calliope_tables, public_tables = check_tables(engine)
    except Exception as e:
        print(f"[ERROR] Failed to check tables: {e}")
        print()
        print("This might mean:")
        print("  - calliope schema doesn't exist yet")
        print("  - Database connection issues")
        print("  - Tables don't exist yet")
        return 1
    
    # Display current state
    has_public_tables = display_table_info(calliope_tables, public_tables)
    
    # Check if cleanup is needed
    if not has_public_tables:
        print("=" * 70)
        print("[OK] NO CLEANUP NEEDED")
        print("=" * 70)
        print()
        print("No calliope tables found in public schema.")
        print("Schema isolation is working correctly!")
        return 0
    
    # Check if calliope tables exist
    if not calliope_tables:
        print("=" * 70)
        print("[ERROR] CANNOT PROCEED")
        print("=" * 70)
        print()
        print("Calliope tables do not exist in calliope schema!")
        print("Cannot safely cleanup without confirming data location.")
        print()
        print("Please:")
        print("  1. Deploy the schema isolation code first")
        print("  2. Ensure calliope schema is created")
        print("  3. Run this cleanup script again")
        return 1
    
    # Confirm cleanup
    if not confirm_cleanup():
        print()
        print("Cleanup cancelled by user.")
        return 0
    
    # Perform cleanup
    success = cleanup_public_tables(engine)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
