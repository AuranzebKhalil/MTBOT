import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from typing import List

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.storage.models import (
    Base, User, Trade, BotState, SignalLog, RiskEvent, 
    ExecutionLog, LatencyLog, TradeAnnotation, TradeEvent, 
    NewsWindow, SupportTicket, SupportMessage, BlockedZone
)

def migrate_data():
    """
    Migrates all current data from local SQLite to Supabase PostgreSQL.
    """
    # 1. Setup Source (SQLite)
    sqlite_url = f"sqlite:///./{settings.SQLITE_DB_PATH}"
    print(f"📡 Connecting to Source: {sqlite_url}")
    source_engine = create_engine(sqlite_url)
    SourceSession = sessionmaker(bind=source_engine)
    source_db = SourceSession()

    # 2. Setup Destination (Supabase)
    if not settings.SUPABASE_PROJECT_ID or not settings.SUPABASE_PASSWORD:
        if not settings.POSTGRES_URL:
            print("❌ ERROR: Supabase credentials not found in .env")
            print("Please set SUPABASE_PROJECT_ID and SUPABASE_PASSWORD and try again.")
            return

    dest_url = settings.DATABASE_URL
    if dest_url.startswith("sqlite"):
        print("❌ ERROR: DATABASE_URL is still pointing to SQLite.")
        print("Ensure SUPABASE_PROJECT_ID and SUPABASE_PASSWORD are set correctly in .env.")
        return

    print(f"🚀 Connecting to Destination: {dest_url}")
    dest_engine = create_engine(dest_url)
    
    # Create tables in destination
    print("🏗️ Creating tables in Supabase...")
    Base.metadata.create_all(bind=dest_engine)
    
    DestSession = sessionmaker(bind=dest_engine)
    dest_db = DestSession()

    # Tables to migrate in Order (to preserve FKs)
    models = [
        User, BotState, NewsWindow, LatencyLog, BlockedZone, 
        Trade, RiskEvent, SupportTicket, SupportMessage, 
        ExecutionLog, TradeAnnotation, TradeEvent, SignalLog
    ]

    try:
        for model in models:
            table_name = model.__tablename__
            print(f"📦 Migrating {table_name}...")
            
            # Fetch all from source
            items = source_db.query(model).all()
            if not items:
                print(f"   ℹ️ No data found in {table_name}. Skipping.")
                continue

            # Clear existing data in destination to avoid duplicates 
            # (Optional: remove if you want to perform a merge)
            # dest_db.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"))
            
            # Transfer
            count = 0
            for item in items:
                # Expunge from source so it can be added to dest
                source_db.expunge(item)
                # Create a clean state for the destination session
                from sqlalchemy.orm import make_transient
                make_transient(item)
                
                # Manual fix for PostgreSQL JSON fields if they are strings in SQLite
                # (SQLAlchemy usually handles this, but just in case)
                
                dest_db.add(item)
                count += 1
            
            dest_db.commit()
            print(f"   ✅ Migrated {count} records from {table_name}")

        print("\n✨ Migration Successful! Your data is now on Supabase.")
        print("You can now restart your bot to continue with the cloud database.")

    except Exception as e:
        print(f"❌ Migration Error: {e}")
        dest_db.rollback()
    finally:
        source_db.close()
        dest_db.close()

if __name__ == "__main__":
    confirm = input("⚠️ This will copy all local SQLite data to Supabase. Continue? (y/n): ")
    if confirm.lower() == 'y':
        migrate_data()
    else:
        print("Migration cancelled.")
