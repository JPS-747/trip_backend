#!/usr/bin/env python3
"""
Insert Namibia public holidays (2018-2026) into the database.
Uses the holidays library to get official Namibia holidays.
"""
import sys
from datetime import datetime

try:
    import holidays
except ImportError:
    print("Installing holidays library...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "holidays"])
    import holidays

from db import get_db


def insert_namibia_holidays():
    """Insert all Namibia public holidays from 2018 to 2026 into the database."""

    # Get Namibia holidays
    namibia_holidays = holidays.Namibia(years=range(2018, 2027))

    print("=" * 70)
    print("NAMIBIA PUBLIC HOLIDAYS (2018-2026)")
    print("=" * 70)

    # Connect to database
    with get_db() as db:
        # First, clear existing holidays
        print("\nClearing existing holidays...")
        db.execute("DELETE FROM public_holidays")

        # Prepare data
        holidays_list = []
        for date, name in sorted(namibia_holidays.items()):
            year = date.year
            date_str = date.strftime("%Y-%m-%d")
            holidays_list.append((None, "Namibia", year, date_str, name))
            print(f"  {date_str} - {name}")

        # Insert holidays
        print(f"\nInserting {len(holidays_list)} holidays into database...")
        db.executemany(
            """
            INSERT INTO public_holidays (id, country, year, date, name)
            VALUES (?, ?, ?, ?, ?)
            """,
            holidays_list,
        )

        # Verify insertion
        cursor = db.execute("SELECT COUNT(*) as count FROM public_holidays")
        count = cursor.fetchone()["count"]

        print(f"\n✓ Successfully inserted {count} holidays")

        # Show summary by year
        print("\nHolidays by year:")
        cursor = db.execute(
            "SELECT year, COUNT(*) as count FROM public_holidays GROUP BY year ORDER BY year"
        )
        for row in cursor.fetchall():
            print(f"  {row['year']}: {row['count']} holidays")

        # Show some sample holidays
        print("\nSample holidays:")
        cursor = db.execute(
            "SELECT date, name FROM public_holidays ORDER BY date LIMIT 10"
        )
        for row in cursor.fetchall():
            print(f"  {row['date']} - {row['name']}")


if __name__ == "__main__":
    try:
        insert_namibia_holidays()
        print("\n" + "=" * 70)
        print("✓ Namibia holidays successfully inserted!")
        print("=" * 70)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
