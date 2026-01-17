#!/usr/bin/env python3
"""
RESTORE MISSING WORDS SCRIPT
=============================

This script restores words from a backup JSON file to the database.
It only adds words that don't already exist in the database.

SAFETY FEATURES:
- Checks if word exists before adding (no duplicates)
- Validates word data before insertion
- Respects schema isolation (calliope schema on PostgreSQL)
- Provides detailed progress reporting
- Dry-run mode available

USAGE:
    python restore_missing_words.py [--dry-run] [--backup-file PATH]

OPTIONS:
    --dry-run       : Show what would be added without actually adding
    --backup-file   : Path to backup JSON file (default: heroku_words_backup_20260116_233342.json)
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from backend.db import SessionLocal, add_word
from backend.schemas import WordCreate
from backend.models import Word


def load_backup_file(backup_path: str) -> List[Dict]:
    """Load words from backup JSON file."""
    try:
        with open(backup_path, 'r', encoding='utf-8') as f:
            words = json.load(f)
        print(f"[OK] Loaded {len(words)} words from backup file")
        return words
    except FileNotFoundError:
        print(f"[ERROR] Backup file not found: {backup_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in backup file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to load backup file: {e}")
        sys.exit(1)


def word_exists(db: Session, word_text: str) -> bool:
    """Check if a word already exists in the database."""
    existing = db.query(Word).filter(Word.word == word_text).first()
    return existing is not None


def validate_word_data(word_data: Dict) -> Optional[WordCreate]:
    """
    Validate word data and convert to WordCreate schema.
    Returns None if data is invalid.
    """
    required_fields = ['word', 'pos', 'definition', 'example_sentence', 'rarity', 'sentiment']
    
    # Check for required fields
    for field in required_fields:
        if field not in word_data or not word_data[field]:
            return None
    
    # Validate rarity
    valid_rarity = ['notty', 'luke', 'alex']
    if word_data['rarity'] not in valid_rarity:
        # Try to fix common issues
        if word_data['rarity'].lower() in valid_rarity:
            word_data['rarity'] = word_data['rarity'].lower()
        else:
            return None
    
    # Validate sentiment
    valid_sentiment = ['positive', 'negative', 'neutral', 'formal']
    if word_data['sentiment'] not in valid_sentiment:
        # Try to fix common issues
        if word_data['sentiment'].lower() in valid_sentiment:
            word_data['sentiment'] = word_data['sentiment'].lower()
        else:
            return None
    
    # Validate pos (part of speech) - should not be empty or "unknown"
    if word_data['pos'] in ['unknown', '', None]:
        # Default to 'noun' if unknown
        word_data['pos'] = 'noun'
    
    # Check for placeholder definitions
    if word_data['definition'] in ['Definition unavailable.', 'Example unavailable.', '']:
        return None
    
    try:
        return WordCreate(
            word=word_data['word'].strip(),
            pos=word_data['pos'].strip(),
            definition=word_data['definition'].strip(),
            example_sentence=word_data['example_sentence'].strip(),
            rarity=word_data['rarity'].strip(),
            sentiment=word_data['sentiment'].strip()
        )
    except Exception:
        return None


def restore_missing_words(backup_path: str, dry_run: bool = False):
    """
    Restore missing words from backup file to database.
    
    Args:
        backup_path: Path to backup JSON file
        dry_run: If True, only show what would be added without actually adding
    """
    print("=" * 70)
    print("RESTORE MISSING WORDS")
    print("=" * 70)
    print()
    
    if dry_run:
        print("[DRY RUN MODE] No changes will be made to the database")
        print()
    
    # Load backup file
    backup_words = load_backup_file(backup_path)
    
    # Connect to database
    db = SessionLocal()
    
    try:
        # Statistics
        total_words = len(backup_words)
        existing_words = 0
        invalid_words = 0
        added_words = 0
        failed_words = 0
        
        invalid_word_list = []
        failed_word_list = []
        
        print(f"Processing {total_words} words from backup...")
        print()
        
        # Process each word
        for i, word_data in enumerate(backup_words, 1):
            word_text = word_data.get('word', 'UNKNOWN')
            
            # Progress indicator every 50 words
            if i % 50 == 0:
                print(f"  Progress: {i}/{total_words} words processed...")
            
            # Check if word exists
            if word_exists(db, word_text):
                existing_words += 1
                continue
            
            # Validate word data
            word_create = validate_word_data(word_data)
            if not word_create:
                invalid_words += 1
                invalid_word_list.append(word_text)
                continue
            
            # Add word (or simulate in dry-run mode)
            if not dry_run:
                try:
                    add_word(db, word_create)
                    added_words += 1
                except Exception as e:
                    failed_words += 1
                    failed_word_list.append((word_text, str(e)))
            else:
                added_words += 1
        
        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print()
        print(f"Total words in backup:     {total_words}")
        print(f"Already exist in DB:       {existing_words}")
        print(f"Invalid/incomplete data:   {invalid_words}")
        print(f"{'Would be added' if dry_run else 'Successfully added'}:         {added_words}")
        if not dry_run:
            print(f"Failed to add:             {failed_words}")
        print()
        
        # Show invalid words if any
        if invalid_words > 0 and len(invalid_word_list) <= 20:
            print("Invalid/incomplete words (not added):")
            for word in invalid_word_list:
                print(f"  - {word}")
            print()
        elif invalid_words > 0:
            print(f"Invalid/incomplete words: {invalid_words} (too many to list)")
            print(f"First 10: {', '.join(invalid_word_list[:10])}")
            print()
        
        # Show failed words if any
        if not dry_run and failed_words > 0:
            print("Failed to add (with errors):")
            for word, error in failed_word_list[:10]:
                print(f"  - {word}: {error}")
            if len(failed_word_list) > 10:
                print(f"  ... and {len(failed_word_list) - 10} more")
            print()
        
        if dry_run:
            print("[DRY RUN] No changes were made. Run without --dry-run to add words.")
        else:
            print(f"[OK] Successfully restored {added_words} missing words to the database!")
        
    except Exception as e:
        print(f"[ERROR] Unexpected error during restore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Restore missing words from backup JSON to database'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be added without actually adding'
    )
    parser.add_argument(
        '--backup-file',
        default='heroku_words_backup_20260116_233342.json',
        help='Path to backup JSON file (default: heroku_words_backup_20260116_233342.json)'
    )
    
    args = parser.parse_args()
    
    # Check if backup file exists
    if not os.path.exists(args.backup_file):
        print(f"[ERROR] Backup file not found: {args.backup_file}")
        print()
        print("Available backup files in current directory:")
        backup_files = [f for f in os.listdir('.') if f.endswith('.json') and 'backup' in f.lower()]
        if backup_files:
            for f in backup_files:
                print(f"  - {f}")
        else:
            print("  (none found)")
        sys.exit(1)
    
    restore_missing_words(args.backup_file, args.dry_run)


if __name__ == '__main__':
    main()
