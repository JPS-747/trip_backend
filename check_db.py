import sqlite3

conn = sqlite3.connect("trippen.db")
cursor = conn.cursor()

# Check trips table structure
print("=== TRIPS TABLE STRUCTURE ===")
cursor.execute("PRAGMA table_info(trips)")
cols = cursor.fetchall()
for col in cols:
    print(col)

# Check if vehicleRegNumber column exists
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='trips'")
print("\n=== CREATE TABLE STATEMENT ===")
print(cursor.fetchone()[0])

# Check sample trip data
print("\n=== SAMPLE TRIP DATA ===")
cursor.execute("SELECT * FROM trips LIMIT 1")
row = cursor.fetchone()
if row:
    keys = [col[0] for col in cols]
    for key, val in zip(keys, row):
        print(f"{key}: {val}")
else:
    print("No trips in database")

conn.close()
