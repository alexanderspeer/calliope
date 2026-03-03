#!/usr/bin/env python3
"""
Quick script to check word count in the database.
Shows which database you're connected to and how many words are in it.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.db import SessionLocal, DATABASE_URL
from backend.models import Word

print("=" * 70)
print("DATABASE CONNECTION CHECK")
print("=" * 70)
print()
print(f"DATABASE_URL: {DATABASE_URL[:60]}...")
print()

if "sqlite" in DATABASE_URL.lower():
    print("[INFO] Connected to LOCAL SQLite database")
elif "postgresql" in DATABASE_URL.lower():
    print("[INFO] Connected to HEROKU PostgreSQL database")
    # Extract host for verification
    try:
        host = DATABASE_URL.split('@')[1].split(':')[0] if '@' in DATABASE_URL else 'unknown'
        print(f"       Host: {host}")
    except:
        pass
else:
    print("[WARNING] Unknown database type")

print()

db = SessionLocal()
try:
    word_count = db.query(Word).count()
    print(f"Total words in database: {word_count}")
    print()
    
    # Show first 5 words as sample
    print("Sample words (first 5):")
    sample_words = db.query(Word).limit(5).all()
    for word in sample_words:
        print(f"  - {word.word} ({word.pos})")
    
except Exception as e:
    print(f"[ERROR] Failed to query database: {e}")
finally:
    db.close()

print()
print("=" * 70)
