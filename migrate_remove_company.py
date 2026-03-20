"""
Migration script to remove company column from trips and clients tables.
This script will:
1. Create backup versions of the tables
2. Remove the company column from both tables
3. Verify the migration was successful
"""

import sqlite3

DB_PATH = "trippen.db"


def migrate():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        print("Starting migration to remove company column...")

        # 1. Backup existing tables
        print("Creating backups...")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clients_backup AS
            SELECT * FROM clients
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trips_backup AS
            SELECT * FROM trips
            """
        )

        # 2. Drop old tables
        print("Dropping old tables...")
        cursor.execute("DROP TABLE trips")
        cursor.execute("DROP TABLE clients")

        # 3. Create new tables without company column
        print("Creating new tables without company column...")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                client TEXT PRIMARY KEY,
                distanceFromOffice REAL,
                fullAddress TEXT,
                isDisabled INTEGER DEFAULT 0,
                phoneNumber TEXT,
                email TEXT,
                contactPerson TEXT,
                city TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                client TEXT,
                distanceKm REAL,
                totalDistanceKm REAL,
                tripType INTEGER,
                isPrivateTrip INTEGER DEFAULT 0,
                FOREIGN KEY(client) REFERENCES clients(client)
            )
        """
        )

        # 4. Restore data to new tables (without company column)
        print("Restoring data...")
        cursor.execute(
            """
            INSERT INTO clients (client, distanceFromOffice, fullAddress, isDisabled, phoneNumber, email, contactPerson, city)
            SELECT client, distanceFromOffice, fullAddress, isDisabled, phoneNumber, email, contactPerson, city
            FROM clients_backup
        """
        )
        cursor.execute(
            """
            INSERT INTO trips (id, date, client, distanceKm, totalDistanceKm, tripType, isPrivateTrip)
            SELECT id, date, client, distanceKm, totalDistanceKm, tripType, isPrivateTrip
            FROM trips_backup
        """
        )

        conn.commit()

        # 5. Verify migration
        print("Verifying migration...")
        cursor.execute("SELECT COUNT(*) FROM clients")
        client_count = cursor.fetchone()[0]
        print(f"✓ Clients migrated: {client_count}")

        cursor.execute("SELECT COUNT(*) FROM trips")
        trip_count = cursor.fetchone()[0]
        print(f"✓ Trips migrated: {trip_count}")

        print("\n✅ Migration completed successfully!")
        print("Backups are available as 'clients_backup' and 'trips_backup' tables.")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
