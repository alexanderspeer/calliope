import os
import json
from pathlib import Path
from sqlalchemy import create_engine, func, or_, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from backend.models import Base, Word, Config
from backend.schemas import WordCreate, DatabaseFilter, FlashcardFilter
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import random


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./calliope.db")

# Fix Heroku PostgreSQL URL format (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Detect database type for schema isolation
IS_POSTGRESQL = "postgresql" in DATABASE_URL.lower()
CALLIOPE_SCHEMA = "calliope"

# Handle SQLite vs PostgreSQL connection args
if "sqlite" in DATABASE_URL:
    # SQLite connection args
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL connection args (no special args needed)
    connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_exists():
    """
    CRITICAL SAFETY FUNCTION: Create calliope schema on PostgreSQL before table creation.
    This prevents tables from being created in the public schema on shared databases.
    
    - PostgreSQL: Creates 'calliope' schema if it doesn't exist (idempotent, safe)
    - SQLite: No-op (SQLite doesn't support schemas)
    
    This function must be called BEFORE create_tables() on PostgreSQL.
    """
    if not IS_POSTGRESQL:
        # SQLite doesn't support schemas - skip
        print("[SCHEMA] SQLite detected - no schema isolation needed")
        return
    
    try:
        # Use raw SQL to create schema (SQLAlchemy doesn't have schema creation API)
        with engine.connect() as connection:
            # CREATE SCHEMA IF NOT EXISTS is idempotent and safe
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {CALLIOPE_SCHEMA}"))
            connection.commit()
        print(f"[SCHEMA] ✓ PostgreSQL schema '{CALLIOPE_SCHEMA}' ensured (safe on shared DB)")
    except Exception as e:
        print(f"[SCHEMA] ✗ Error creating schema: {e}")
        raise


def create_tables():
    """
    Create database tables in the appropriate location:
    - PostgreSQL: calliope.words, calliope.config (via __table_args__ in models)
    - SQLite: words, config (default schema)
    
    SAFETY: This function assumes ensure_schema_exists() was called first on PostgreSQL.
    """
    if IS_POSTGRESQL:
        print(f"[TABLES] Creating tables in PostgreSQL schema: {CALLIOPE_SCHEMA}")
    else:
        print("[TABLES] Creating tables in SQLite")
    
    Base.metadata.create_all(bind=engine)
    
    if IS_POSTGRESQL:
        print(f"[TABLES] ✓ Tables created in schema '{CALLIOPE_SCHEMA}' (isolated from public)")
    else:
        print("[TABLES] ✓ Tables created in SQLite")


def init_database():
    """
    Initialize database with starting words if empty.
    
    SAFETY GUARANTEES:
    1. On PostgreSQL: Ensures calliope schema exists BEFORE table creation
    2. Checks only calliope.words (or words in SQLite) for emptiness
    3. Seeds only if OUR tables are empty (ignores public.words on shared DB)
    4. Never touches public schema
    """
    # CRITICAL: Create schema first on PostgreSQL (before tables)
    ensure_schema_exists()
    
    # Now create tables (will be in calliope schema on PostgreSQL)
    create_tables()
    
    db = SessionLocal()
    
    try:
        # Check if database is empty
        word_count = db.query(Word).count()
        if word_count == 0:
            # Load starting words
            starting_words_path = Path("starting_words.json")
            if starting_words_path.exists():
                with open(starting_words_path, 'r', encoding='utf-8') as f:
                    words_data = json.load(f)
                
                for word_data in words_data:
                    word = Word(
                        word=word_data["word"],
                        pos=word_data["pos"],
                        definition=word_data["definition"],
                        example_sentence=word_data["example_sentence"],
                        rarity=word_data["rarity"],
                        sentiment=word_data["sentiment"],
                        date_added=datetime.fromisoformat(word_data["date_added"].replace('Z', '+00:00'))
                    )
                    db.add(word)
                
                db.commit()
                print(f"Loaded {len(words_data)} starting words into database")
            
            # Initialize config for Word of the Day
            set_config_value(db, "wotd_date", datetime.now().strftime("%Y-%m-%d"))
            set_config_value(db, "wotd_index", "0")
            
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
    finally:
        db.close()


def get_word_by_name(db: Session, word: str) -> Optional[Word]:
    """Get word by name (exact match, case insensitive)"""
    return db.query(Word).filter(Word.word.ilike(word)).first()


def add_word(db: Session, word_data: WordCreate) -> Word:
    """Add new word to database"""
    db_word = Word(**word_data.dict())
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    return db_word


def get_words_by_filter(db: Session, filter_params: DatabaseFilter) -> List[Word]:
    """Get words with filtering"""
    query = db.query(Word)
    
    if filter_params.pos:
        query = query.filter(Word.pos.ilike(f"%{filter_params.pos}%"))
    if filter_params.rarity:
        query = query.filter(Word.rarity == filter_params.rarity)
    if filter_params.sentiment:
        query = query.filter(Word.sentiment == filter_params.sentiment)
    
    return query.order_by(Word.date_added.desc()).offset(filter_params.offset).limit(filter_params.limit).all()


def get_words_by_filter_with_count(db: Session, filter_params: DatabaseFilter) -> Dict:
    """Get words with filtering and return total count for pagination"""
    query = db.query(Word)
    
    if filter_params.pos:
        query = query.filter(Word.pos.ilike(f"%{filter_params.pos}%"))
    if filter_params.rarity:
        query = query.filter(Word.rarity == filter_params.rarity)
    if filter_params.sentiment:
        query = query.filter(Word.sentiment == filter_params.sentiment)
    if filter_params.search:
        search_term = f"%{filter_params.search}%"
        query = query.filter(
            or_(
                Word.word.ilike(search_term),
                Word.definition.ilike(search_term),
                Word.example_sentence.ilike(search_term)
            )
        )
    
    # Get total count before applying limit/offset
    total_count = query.count()
    
    # Get the actual words with pagination
    words = query.order_by(Word.date_added.desc()).offset(filter_params.offset).limit(filter_params.limit).all()
    
    return {
        "words": words,
        "total_count": total_count,
        "current_page": (filter_params.offset // filter_params.limit) + 1 if filter_params.limit > 0 else 1,
        "total_pages": (total_count + filter_params.limit - 1) // filter_params.limit if filter_params.limit > 0 else 1,
        "items_per_page": filter_params.limit,
        "has_next": filter_params.offset + filter_params.limit < total_count,
        "has_previous": filter_params.offset > 0
    }


def get_words_for_flashcards(db: Session, filter_params: FlashcardFilter) -> List[Word]:
    """Get words for flashcards with filtering"""
    query = db.query(Word)
    
    if filter_params.pos:
        query = query.filter(Word.pos.ilike(f"%{filter_params.pos}%"))
    if filter_params.rarity:
        query = query.filter(Word.rarity == filter_params.rarity)
    if filter_params.sentiment:
        query = query.filter(Word.sentiment == filter_params.sentiment)
    
    # If we have a specific small limit (like last 10, 20, 30, etc.), order by most recent
    # Otherwise, randomize for variety
    if filter_params.limit and filter_params.limit <= 100:
        query = query.order_by(Word.date_added.desc())
    else:
        query = query.order_by(func.random())
    
    return query.offset(filter_params.offset).limit(filter_params.limit).all()


def get_words_by_pos(db: Session, pos: str) -> List[Word]:
    """Get words by part of speech"""
    return db.query(Word).filter(Word.pos.ilike(f"%{pos}%")).all()


def get_all_words(db: Session) -> List[Word]:
    """Get all words"""
    return db.query(Word).all()


def get_random_word(db: Session) -> Optional[Word]:
    """Get random word"""
    return db.query(Word).order_by(func.random()).first()


def get_config_value(db: Session, key: str) -> Optional[str]:
    """Get config value"""
    config = db.query(Config).filter(Config.key == key).first()
    return config.value if config else None


def set_config_value(db: Session, key: str, value: str):
    """Set config value"""
    config = db.query(Config).filter(Config.key == key).first()
    if config:
        config.value = value
    else:
        config = Config(key=key, value=value)
        db.add(config)
    db.commit()


def get_word_of_the_day(db: Session) -> Dict:
    """Get word of the day with cycling logic"""
    today = datetime.now().strftime("%Y-%m-%d")
    last_wotd_date = get_config_value(db, "wotd_date")
    wotd_index = int(get_config_value(db, "wotd_index") or 0)
    
    is_new_day = last_wotd_date != today
    
    if is_new_day:
        # Get total word count
        total_words = db.query(Word).count()
        
        if total_words == 0:
            return None
        
        # Cycle through all words
        if wotd_index >= total_words:
            wotd_index = 0
        
        # Get the word at current index
        word = db.query(Word).offset(wotd_index).first()
        
        # Update config
        set_config_value(db, "wotd_date", today)
        set_config_value(db, "wotd_index", str(wotd_index + 1))
        
        return {"word": word, "is_new_day": True}
    else:
        # Return previous word (index - 1)
        if wotd_index > 0:
            word = db.query(Word).offset(wotd_index - 1).first()
        else:
            word = db.query(Word).first()
        
        return {"word": word, "is_new_day": False}


def search_words_by_similarity(db: Session, word: str, limit: int = 10) -> List[Word]:
    """Search for words similar to input word (for thesaurus)"""
    # Simple similarity search - can be enhanced with more sophisticated matching
    return db.query(Word).filter(
        Word.word.ilike(f"%{word}%") | 
        Word.definition.ilike(f"%{word}%")
    ).limit(limit).all()


def get_word_count(db: Session) -> int:
    """Get total word count"""
    return db.query(Word).count()


def get_words_for_prediction(db: Session, context: str, limit: int = 5) -> List[Word]:
    """Get words suitable for prediction based on context"""
    # Simple implementation - can be enhanced with more sophisticated matching
    return db.query(Word).filter(
        Word.definition.ilike(f"%{context}%") | 
        Word.word.ilike(f"%{context}%")
    ).limit(limit).all()


def update_word(db: Session, word_id: int, word_data: WordCreate) -> Optional[Word]:
    """Update an existing word in the database"""
    db_word = db.query(Word).filter(Word.id == word_id).first()
    if not db_word:
        return None
    
    # Update all fields
    for key, value in word_data.dict().items():
        setattr(db_word, key, value)
    
    db.commit()
    db.refresh(db_word)
    return db_word


def delete_word(db: Session, word_id: int) -> bool:
    """Delete a word from the database"""
    db_word = db.query(Word).filter(Word.id == word_id).first()
    if not db_word:
        return False
    
    db.delete(db_word)
    db.commit()
    return True


def get_word_by_id(db: Session, word_id: int) -> Optional[Word]:
    """Get word by ID"""
    return db.query(Word).filter(Word.id == word_id).first()


def get_words_added_today(db: Session) -> int:
    """Get count of words added today"""
    today = datetime.utcnow().date()
    return db.query(Word).filter(
        func.date(Word.date_added) == today
    ).count()


def get_current_streak(db: Session) -> int:
    """Calculate current streak of consecutive days with word additions"""
    today = datetime.utcnow().date()
    current_date = today
    streak = 0
    
    while True:
        # Check if any words were added on this date
        words_on_date = db.query(Word).filter(
            func.date(Word.date_added) == current_date
        ).count()
        
        if words_on_date > 0:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak


def verify_schema_isolation() -> Dict:
    """
    SAFETY VERIFICATION: Verify that calliope tables are in the correct schema.
    
    This function checks:
    1. PostgreSQL: Tables exist in 'calliope' schema (NOT in public)
    2. SQLite: Tables exist (no schema concept)
    3. No new tables were created in public schema
    
    Returns a dict with verification results.
    Should be called after deployment to verify safety.
    """
    verification_results = {
        "database_type": "postgresql" if IS_POSTGRESQL else "sqlite",
        "status": "unknown",
        "errors": [],
        "warnings": [],
        "tables_found": [],
        "public_tables_created": [],
        "safe": False
    }
    
    if not IS_POSTGRESQL:
        # SQLite verification - just check tables exist
        try:
            with engine.connect() as connection:
                result = connection.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('words', 'config')"
                ))
                tables = [row[0] for row in result]
                verification_results["tables_found"] = tables
                verification_results["status"] = "ok"
                verification_results["safe"] = len(tables) >= 2
                if verification_results["safe"]:
                    verification_results["message"] = "SQLite tables verified"
                else:
                    verification_results["errors"].append("Missing expected tables")
        except Exception as e:
            verification_results["status"] = "error"
            verification_results["errors"].append(str(e))
        
        return verification_results
    
    # PostgreSQL verification - check schema isolation
    try:
        with engine.connect() as connection:
            # Check if calliope schema exists
            schema_check = connection.execute(text(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"
            ), {"schema": CALLIOPE_SCHEMA})
            
            if not schema_check.fetchone():
                verification_results["status"] = "error"
                verification_results["errors"].append(f"Schema '{CALLIOPE_SCHEMA}' does not exist!")
                verification_results["safe"] = False
                return verification_results
            
            # Check tables in calliope schema
            calliope_tables = connection.execute(text(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema 
                AND table_name IN ('words', 'config')
                ORDER BY table_name
                """
            ), {"schema": CALLIOPE_SCHEMA})
            
            calliope_table_list = [row[0] for row in calliope_tables]
            verification_results["tables_found"] = [f"{CALLIOPE_SCHEMA}.{t}" for t in calliope_table_list]
            
            # Check if any calliope tables were created in public (BAD!)
            public_collision = connection.execute(text(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('words', 'config')
                AND table_name IN (
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = :schema
                )
                ORDER BY table_name
                """
            ), {"schema": CALLIOPE_SCHEMA})
            
            public_collision_list = [row[0] for row in public_collision]
            verification_results["public_tables_created"] = public_collision_list
            
            # Determine safety
            expected_tables = {"words", "config"}
            found_tables = set(calliope_table_list)
            
            if found_tables == expected_tables and len(public_collision_list) == 0:
                verification_results["status"] = "ok"
                verification_results["safe"] = True
                verification_results["message"] = f"✓ All tables in '{CALLIOPE_SCHEMA}' schema, public schema untouched"
            else:
                verification_results["status"] = "warning"
                if found_tables != expected_tables:
                    missing = expected_tables - found_tables
                    if missing:
                        verification_results["warnings"].append(f"Missing tables in calliope: {missing}")
                if public_collision_list:
                    verification_results["errors"].append(
                        f"DANGER: Tables found in public schema: {public_collision_list}. "
                        "This may collide with other apps!"
                    )
                    verification_results["safe"] = False
                else:
                    verification_results["safe"] = True
    
    except Exception as e:
        verification_results["status"] = "error"
        verification_results["errors"].append(f"Verification failed: {str(e)}")
        verification_results["safe"] = False
    
    return verification_results 