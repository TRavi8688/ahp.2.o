import sqlite3
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('SELECT ahp_id, user_id FROM patients WHERE ahp_id = "AHP-TEST-DRIVE"')
row = cursor.fetchone()
print(f"PATIENT_ROW: {row}")

if row:
    cursor.execute('SELECT email FROM users WHERE id = ?', (row[1],))
    user_row = cursor.fetchone()
    print(f"USER_ROW: {user_row}")
conn.close()
