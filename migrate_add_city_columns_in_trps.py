#!/usr/bin/env python3
"""
Migration script to add new city columns to existing database.
This script adds: city column to the trips table.
"""

import sqlite3
import sys

DB_PATH = "trippen.db"


def migrate_add_trip_columns():
    """Add new columns to trips table if they don't already exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get existing columns
        cursor.execute("PRAGMA table_info(trips)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        new_columns = {
            "city": "TEXT",
        }

        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                print(f"Adding column: {col_name} ({col_type})")
                cursor.execute(f"ALTER TABLE trips ADD COLUMN {col_name} {col_type}")
            else:
                print(f"Column already exists: {col_name}")

        conn.commit()
        print("\n✓ Migration complete! All columns are in place.")
        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"✗ Database error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    print("Starting migration: Add new trip columns...")
    success = migrate_add_trip_columns()
    sys.exit(0 if success else 1)
