#!/usr/bin/env python3
"""
Quick restore script - re-upload words to Heroku after dyno restart
"""
import json
import requests
import time

# Use the latest backup
BACKUP_FILE = "my_words_backup_20250801_232502.json"
HEROKU_APP_URL = "https://calliope-ccdc166d3d1e.herokuapp.com"

def quick_restore():
    """Restore words from backup to Heroku"""
    print("🚀 Quick Restore - Re-uploading your words to Heroku...")
    
    # Load backup
    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        words = json.load(f)
    
    print(f"📂 Loaded {len(words)} words from backup")
    
    # Quick batch upload (only new words that aren't in starting words)
    success_count = 0
    
    # Skip the first 205 words (these are likely the starting words)
    # and focus on the user's added words
    user_words = words[205:]  # Focus on the user's additions
    
    print(f"🎯 Uploading {len(user_words)} user-added words...")
    
    for i, word_data in enumerate(user_words, 1):
        try:
            response = requests.post(
                f"{HEROKU_APP_URL}/api/add-word",
                json={"word": word_data["word"]},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") or "already exists" in result.get("message", ""):
                    success_count += 1
                    print(f"✅ [{i}/{len(user_words)}] {word_data['word']}")
                else:
                    print(f"⚠️  [{i}/{len(user_words)}] {word_data['word']} - {result.get('message', 'Failed')}")
            
            time.sleep(0.3)  # Small delay
            
        except Exception as e:
            print(f"❌ [{i}/{len(user_words)}] {word_data['word']} - Error: {e}")
    
    print(f"\n🎉 Restore complete! {success_count}/{len(user_words)} words restored.")
    print(f"🌐 Check your app: {HEROKU_APP_URL}/static/index.html")

if __name__ == "__main__":
    quick_restore()