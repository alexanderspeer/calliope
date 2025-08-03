#!/usr/bin/env python3
"""
Export words from local database to JSON for backup/migration
"""
import sqlite3
import json
from datetime import datetime
import sys
import os

def export_words():
    """Export all words from local database to JSON"""
    db_path = 'backend/calliope.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return None, []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if words table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words';")
        if not cursor.fetchone():
            print("❌ Words table not found in database")
            conn.close()
            return None, []
        
        # Get all words
        cursor.execute("""
            SELECT word, pos, definition, example_sentence, rarity, sentiment, date_added
            FROM words
            ORDER BY date_added
        """)
        
        rows = cursor.fetchall()
        print(f"📊 Found {len(rows)} words in local database")
        
        words = []
        for row in rows:
            word_data = {
                "word": row[0],
                "pos": row[1], 
                "definition": row[2],
                "example_sentence": row[3],
                "rarity": row[4],
                "sentiment": row[5],
                "date_added": row[6]
            }
            words.append(word_data)
        
        conn.close()
        
        # Save to JSON file
        backup_filename = f"my_words_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(words, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(words)} words to {backup_filename}")
        print(f"📁 Backup file: {os.path.abspath(backup_filename)}")
        
        # Show some sample words
        if words:
            sample_words = [w['word'] for w in words[:5]]
            print(f"📝 Sample words: {', '.join(sample_words)}")
        
        return backup_filename, words
        
    except Exception as e:
        print(f"❌ Error exporting words: {e}")
        return None, []

if __name__ == "__main__":
    filename, words = export_words()
    if filename:
        print(f"\n🎯 Ready for migration! Use {filename} to upload to Heroku.")