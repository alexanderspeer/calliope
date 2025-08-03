#!/usr/bin/env python3
"""
Migrate local words to Heroku database via API
"""
import json
import requests
import time
import sys
from typing import List, Dict

# Heroku app URL
HEROKU_APP_URL = "https://calliope-ccdc166d3d1e.herokuapp.com"

def load_backup_file(filename: str) -> List[Dict]:
    """Load words from backup JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            words = json.load(f)
        print(f"📂 Loaded {len(words)} words from {filename}")
        return words
    except FileNotFoundError:
        print(f"❌ Backup file not found: {filename}")
        return []
    except Exception as e:
        print(f"❌ Error loading backup: {e}")
        return []

def check_heroku_connection() -> bool:
    """Test if Heroku app is accessible"""
    try:
        response = requests.get(f"{HEROKU_APP_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Heroku app is accessible")
            return True
        else:
            print(f"❌ Heroku app returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Heroku app: {e}")
        return False

def add_word_to_heroku(word_data: Dict) -> bool:
    """Add a single word to Heroku database via API"""
    try:
        # Prepare the API request
        api_url = f"{HEROKU_APP_URL}/api/add-word"
        payload = {
            "word": word_data["word"]
        }
        
        response = requests.post(api_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ Added: {word_data['word']}")
                return True
            else:
                if "already exists" in result.get("message", "").lower():
                    print(f"⚠️  Skipped (exists): {word_data['word']}")
                    return True  # Count as success since word is there
                else:
                    print(f"❌ Failed to add {word_data['word']}: {result.get('message', 'Unknown error')}")
                    return False
        else:
            print(f"❌ API error for {word_data['word']}: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception adding {word_data['word']}: {e}")
        return False

def migrate_words(backup_filename: str) -> None:
    """Main migration function"""
    print("🚀 Starting migration to Heroku...")
    print("=" * 50)
    
    # Load backup file
    words = load_backup_file(backup_filename)
    if not words:
        print("❌ No words to migrate!")
        return
    
    # Check Heroku connection
    if not check_heroku_connection():
        print("❌ Cannot connect to Heroku. Please check the app is running.")
        return
    
    print(f"\n📤 Starting migration of {len(words)} words...")
    print("=" * 50)
    
    # Migrate words
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, word_data in enumerate(words, 1):
        print(f"[{i}/{len(words)}] ", end="")
        
        success = add_word_to_heroku(word_data)
        if success:
            success_count += 1
        else:
            failed_count += 1
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.5)
        
        # Progress update every 10 words
        if i % 10 == 0:
            print(f"\n📊 Progress: {i}/{len(words)} processed ({success_count} success, {failed_count} failed)")
    
    print("\n" + "=" * 50)
    print("🎯 Migration Summary:")
    print(f"   ✅ Successfully added: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📊 Total processed: {len(words)}")
    
    if failed_count == 0:
        print("\n🎉 Migration completed successfully!")
        print(f"🌐 Check your words at: {HEROKU_APP_URL}/static/index.html")
    else:
        print(f"\n⚠️  Migration completed with {failed_count} failures.")
        print("You may want to retry failed words manually.")

if __name__ == "__main__":
    # Use the most recent backup file
    import glob
    backup_files = glob.glob("my_words_backup_*.json")
    
    if not backup_files:
        print("❌ No backup files found! Run export_words.py first.")
        sys.exit(1)
    
    # Use the most recent backup
    latest_backup = max(backup_files)
    print(f"📁 Using backup file: {latest_backup}")
    
    migrate_words(latest_backup)