import sqlite3
import sys

def migrate():
    try:
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [c[1] for c in cursor.fetchall()]
        print(f"Current columns in 'users': {columns}")
        
        if 'insforge_id' not in columns:
            print("Adding 'insforge_id' column to 'users' table...")
            cursor.execute("ALTER TABLE users ADD COLUMN insforge_id VARCHAR(100)")
            conn.commit()
            print("Migration successful.")
        else:
            print("'insforge_id' already exists.")
            
        # Verify one more time
        cursor.execute("PRAGMA table_info(users)")
        print(f"Final columns: {[c[1] for c in cursor.fetchall()]}")
        conn.close()
    except Exception as e:
        print(f"ERROR during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()
