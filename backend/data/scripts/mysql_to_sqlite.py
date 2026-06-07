"""
Skill Genome Platform — MySQL to SQLite Migrator
=================================================
This script copies all tables, structures, and data from the local MySQL database 
to a portable SQLite database file (`skill_genome.db`). This allows serverless or 
ephemeral deployments (like Render free tier) to run the API read-only without 
needing a separate, paid cloud database instance.
"""

import os
import sys

# Add backend folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import create_engine
from app.config import get_settings
from app.database import Base
from app.models import (
    SkillCategory,
    Skill,
    SkillEmbedding,
    JobPosting,
    JobSkill,
    CareerArchetype,
    ArchetypeSkill,
    SkillCooccurrence,
    MLExperiment
)
from sqlalchemy.orm import sessionmaker

def migrate_database():
    settings = get_settings()
    
    # 1. Connect to local MySQL using current config settings
    mysql_url = settings.DATABASE_URL
    print(f"[Migration] Connecting to local MySQL at: {mysql_url}")
    try:
        mysql_engine = create_engine(mysql_url)
        MySQLSession = sessionmaker(bind=mysql_engine)
        mysql_session = MySQLSession()
        # Test connection
        mysql_session.execute(Base.metadata.tables['skills'].select().limit(1))
        print("[Migration] MySQL connection successful.")
    except Exception as e:
        print(f"[Migration] Error connecting to MySQL: {e}")
        return

    # 2. Set up SQLite file
    sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skill_genome.db"))
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    if os.path.exists(sqlite_path):
        try:
            os.remove(sqlite_path)
            print(f"[Migration] Removed existing SQLite file: {sqlite_path}")
        except Exception as e:
            print(f"[Migration] Error removing old database file: {e}")
            return
            
    sqlite_url = f"sqlite:///{sqlite_path}"
    print(f"[Migration] Creating target SQLite database: {sqlite_url}")
    sqlite_engine = create_engine(sqlite_url)
    
    # 3. Create schema in SQLite
    print("[Migration] Creating tables in SQLite...")
    Base.metadata.create_all(bind=sqlite_engine)
    
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    # 4. Migrate tables in dependency order
    models_to_migrate = [
        SkillCategory,
        Skill,
        SkillEmbedding,
        JobPosting,
        JobSkill,
        CareerArchetype,
        ArchetypeSkill,
        SkillCooccurrence,
        MLExperiment
    ]
    
    try:
        for model in models_to_migrate:
            name = model.__name__
            print(f"[Migration] Migrating {name} records...")
            
            # Read from MySQL
            records = mysql_session.query(model).all()
            print(f"[Migration] Read {len(records)} records for {name} from MySQL.")
            
            if not records:
                print(f"[Migration] No records to copy for {name}.")
                continue
                
            # Build clean list of SQLite model instances
            sqlite_objects = []
            for r in records:
                # Exclude the internal SQLAlchemy state
                attrs = {k: v for k, v in r.__dict__.items() if k != '_sa_instance_state'}
                sqlite_objects.append(model(**attrs))
                
            # Bulk save to SQLite
            sqlite_session.bulk_save_objects(sqlite_objects)
            sqlite_session.commit()
            print(f"[Migration] Successfully migrated {len(sqlite_objects)} records to SQLite for {name}.")
            
        print("\n============================================================")
        print("  Database migration completed successfully!")
        print(f"  SQLite File Path: {sqlite_path}")
        print("============================================================\n")
        
    except Exception as e:
        print(f"[Migration] Migration failed with error: {e}")
        sqlite_session.rollback()
    finally:
        mysql_session.close()
        sqlite_session.close()

if __name__ == "__main__":
    migrate_database()
