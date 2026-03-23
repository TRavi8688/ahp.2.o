
import sqlite3
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute("SELECT count(*) FROM medical_records WHERE patient_id = (SELECT id FROM patients WHERE ahp_id = 'AHP-TEST-DRIVE')")
count = cursor.fetchone()[0]
print(f"Medical Records for AHP-TEST-DRIVE: {count}")
conn.close()
