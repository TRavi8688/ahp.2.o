import sqlite3
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])
for t in tables:
    print(f"\n--- {t[0]} ---")
    cols = [desc[0] for desc in cursor.execute(f"SELECT * FROM {t[0]} LIMIT 1").description or []]
    print("Columns:", cols)
    rows = cursor.execute(f"SELECT * FROM {t[0]} LIMIT 3").fetchall()
    for row in rows:
        print(row)
    if not rows:
        print("(empty)")
conn.close()
