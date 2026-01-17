from sqlalchemy import Column, Integer, String, DateTime, Text, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import os

Base = declarative_base()

# Detect database type for schema isolation
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./calliope.db")
# Normalize postgres:// to postgresql:// for consistency
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Determine if we're using PostgreSQL (requires schema isolation)
IS_POSTGRESQL = "postgresql" in DATABASE_URL.lower()

# Schema name for PostgreSQL (SQLite doesn't support schemas)
CALLIOPE_SCHEMA = "calliope" if IS_POSTGRESQL else None


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, unique=True, index=True, nullable=False)
    pos = Column(String, nullable=False)
    definition = Column(Text, nullable=False)
    example_sentence = Column(Text, nullable=False)
    rarity = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)
    date_added = Column(DateTime, default=func.now())

    # Build __table_args__ dynamically based on database type
    if IS_POSTGRESQL:
        # PostgreSQL: use calliope schema with constraints
        __table_args__ = (
            CheckConstraint(
                "rarity IN ('notty', 'luke', 'alex')",
                name="check_rarity"
            ),
            CheckConstraint(
                "sentiment IN ('positive', 'negative', 'neutral', 'formal')",
                name="check_sentiment"
            ),
            {"schema": CALLIOPE_SCHEMA}  # CRITICAL: Force schema isolation
        )
    else:
        # SQLite: constraints only (no schema support)
        __table_args__ = (
            CheckConstraint(
                "rarity IN ('notty', 'luke', 'alex')",
                name="check_rarity"
            ),
            CheckConstraint(
                "sentiment IN ('positive', 'negative', 'neutral', 'formal')",
                name="check_sentiment"
            ),
        )


class Config(Base):
    __tablename__ = "config"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    
    # Build __table_args__ dynamically based on database type
    if IS_POSTGRESQL:
        # PostgreSQL: use calliope schema
        __table_args__ = {"schema": CALLIOPE_SCHEMA}  # CRITICAL: Force schema isolation
    else:
        # SQLite: no schema
        __table_args__ = {} 