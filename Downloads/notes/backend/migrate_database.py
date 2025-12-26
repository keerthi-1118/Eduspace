"""
Database migration script to add extracted_content column to notes table
Run this if you have an existing database
"""
from sqlalchemy import text
from database import engine, Base
import models

def migrate_database():
    """Add extracted_content column if it doesn't exist"""
    try:
        with engine.connect() as conn:
            # Check if column exists (SQLite)
            if 'sqlite' in str(engine.url):
                result = conn.execute(text("PRAGMA table_info(notes)"))
                columns = [row[1] for row in result]
                
                if 'extracted_content' not in columns:
                    print("Adding extracted_content column to notes table...")
                    conn.execute(text("ALTER TABLE notes ADD COLUMN extracted_content TEXT"))
                    conn.commit()
                    print("✓ Migration completed successfully!")
                else:
                    print("✓ Column already exists, no migration needed")
            else:
                # PostgreSQL/MySQL
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='notes' AND column_name='extracted_content'
                """))
                
                if not result.fetchone():
                    print("Adding extracted_content column to notes table...")
                    conn.execute(text("ALTER TABLE notes ADD COLUMN extracted_content TEXT"))
                    conn.commit()
                    print("✓ Migration completed successfully!")
                else:
                    print("✓ Column already exists, no migration needed")
    except Exception as e:
        print(f"Error during migration: {e}")
        print("Note: If using SQLite, the column will be added automatically on next app start")

if __name__ == "__main__":
    migrate_database()

