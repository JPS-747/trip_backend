#!/usr/bin/env python
from db import get_db

with get_db() as db:
    schema = db.execute("PRAGMA table_info(vehicles)").fetchall()

    print("Vehicles table schema:")
    print("-" * 60)
    for row in schema:
        col_idx, col_name, col_type, not_null, default, pk = row
        print(f"{col_name:20} {col_type:10} default={default}")

    cols = [row[1] for row in schema]
    print("-" * 60)
    if "currentOdometer" in cols:
        print("✓ Migration successful: currentOdometer column exists")
    else:
        print("✗ Migration failed: currentOdometer column NOT found")
