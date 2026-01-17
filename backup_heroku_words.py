#!/usr/bin/env python3
"""
Backup words from Heroku Postgres database to JSON file
This script connects to the Heroku database using DATABASE_URL environment variable
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add backend to path so we can import the models
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Word


def backup_heroku_words():
    """Backup all words from Heroku Postgres database to JSON"""
    
    # Get DATABASE_URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("Error: DATABASE_URL environment variable is not set")
        print("\nTo backup from Heroku, you need to set DATABASE_URL.")
        print("\nOption 1: Set it manually from Heroku:")
        print("  heroku config:get DATABASE_URL")
        print("  Then set: $env:DATABASE_URL='your-heroku-db-url'")
        print("\nOption 2: Use heroku CLI to set it automatically:")
        print("  heroku config:get DATABASE_URL --app your-app-name")
        return None, []
    
    # Fix Heroku PostgreSQL URL format if needed (postgres:// -> postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Determine if it's Heroku Postgres
    is_heroku = "postgresql" in database_url.lower() or "postgres" in database_url.lower()
    
    if is_heroku:
        print(f"Connecting to Heroku Postgres database...")
    else:
        print(f"Connecting to database at: {database_url.split('@')[0]}@...")
    
    try:
        # Create engine and session
        if "sqlite" in database_url:
            connect_args = {"check_same_thread": False}
        else:
            connect_args = {}
        
        engine = create_engine(database_url, connect_args=connect_args)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Get all words from database
        print("Fetching words from database...")
        words = db.query(Word).order_by(Word.date_added).all()
        
        print(f"Found {len(words)} words in database")
        
        if len(words) == 0:
            print("Warning: No words found in database!")
            db.close()
            return None, []
        
        # Convert words to dictionary format
        words_data = []
        for word in words:
            word_dict = {
                "word": word.word,
                "pos": word.pos,
                "definition": word.definition,
                "example_sentence": word.example_sentence,
                "rarity": word.rarity,
                "sentiment": word.sentiment,
                "date_added": word.date_added.isoformat() if word.date_added else None
            }
            words_data.append(word_dict)
        
        db.close()
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"heroku_words_backup_{timestamp}.json"
        
        # Save to JSON file
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(words_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully exported {len(words_data)} words to {backup_filename}")
        print(f"Backup file location: {os.path.abspath(backup_filename)}")
        
        # Show sample words
        if words_data:
            sample_words = [w['word'] for w in words_data[:10]]
            print(f"\nSample words exported: {', '.join(sample_words)}")
        
        # Show statistics
        rarity_counts = {}
        sentiment_counts = {}
        for word in words_data:
            rarity_counts[word['rarity']] = rarity_counts.get(word['rarity'], 0) + 1
            sentiment_counts[word['sentiment']] = sentiment_counts.get(word['sentiment'], 0) + 1
        
        print(f"\nStatistics:")
        print(f"  Total words: {len(words_data)}")
        print(f"  Rarity distribution: {rarity_counts}")
        print(f"  Sentiment distribution: {sentiment_counts}")
        
        return backup_filename, words_data
        
    except Exception as e:
        print(f"Error backing up words: {e}")
        import traceback
        traceback.print_exc()
        return None, []


if __name__ == "__main__":
    print("=" * 60)
    print("Heroku Words Backup Tool")
    print("=" * 60)
    print()
    
    filename, words = backup_heroku_words()
    
    if filename:
        print()
        print("=" * 60)
        print("Backup completed successfully!")
        print("=" * 60)
        print(f"\nYour words are safely backed up in: {filename}")
        print("\nYou can now safely work on your app without worrying about data loss.")
        print("To restore this backup later, you can use the restore script or import the JSON.")
    else:
        print()
        print("=" * 60)
        print("Backup failed!")
        print("=" * 60)
        sys.exit(1)
