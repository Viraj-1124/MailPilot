from app.database.database import engine
from sqlalchemy import text

def migrate():
    # Try adding is_archived
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE emails ADD COLUMN is_archived BOOLEAN DEFAULT 0"))
            print("Added is_archived column.")
    except Exception as e:
        print(f"is_archived column might already exist or error: {e}")
        
    # Try adding is_deleted
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE emails ADD COLUMN is_deleted BOOLEAN DEFAULT 0"))
            print("Added is_deleted column.")
    except Exception as e:
        print(f"is_deleted column might already exist or error: {e}")

    # Try adding archived_at
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE emails ADD COLUMN archived_at DATETIME"))
            print("Added archived_at column.")
    except Exception as e:
        print(f"archived_at column might already exist or error: {e}")

    # Try adding deleted_at
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE emails ADD COLUMN deleted_at DATETIME"))
            print("Added deleted_at column.")
    except Exception as e:
        print(f"deleted_at column might already exist or error: {e}")

if __name__ == "__main__":
    migrate()
