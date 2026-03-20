"""
Script to update all clients and set their city to 'Walvis Bay'.
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "trippen.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


def update_clients_city(city="Walvis Bay"):
    """Update all clients and set their city to the specified value."""
    with get_db() as db:
        # Get all clients before update
        rows_before = db.execute("SELECT COUNT(*) as count FROM clients").fetchone()
        count_before = rows_before["count"]

        print(f"Total clients before update: {count_before}")

        if count_before == 0:
            print("No clients found in database.")
            return

        # Update all clients with the new city
        cursor = db.execute(
            "UPDATE clients SET city = ? WHERE city IS NULL OR city != ?",
            (city, city),
        )
        updated_count = cursor.rowcount

        print(f"Updated {updated_count} client(s) with city = '{city}'")

        # Display updated clients
        print("\nUpdated clients:")
        rows = db.execute("SELECT client, city FROM clients ORDER BY client").fetchall()
        for row in rows:
            print(f"  - {row['client']}: {row['city']}")


if __name__ == "__main__":
    print("Updating clients city to 'Walvis Bay'...\n")
    update_clients_city("Walvis Bay")
    print("\nDone!")
