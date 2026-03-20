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


def init_db():
    with get_db() as db:
        db.execute(
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
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                client TEXT,
                city TEXT,
                distanceKm REAL,
                totalDistanceKm REAL,
                tripType INTEGER,
                isPrivateTrip INTEGER DEFAULT 0,
                vehicleRegNumber TEXT,
                FOREIGN KEY(client) REFERENCES clients(client),
                FOREIGN KEY(vehicleRegNumber) REFERENCES vehicles(regNumber)
            )
        """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicles (
                regNumber TEXT PRIMARY KEY,
                make TEXT,
                model TEXT,
                year INTEGER,
                kmPerLiter REAL,
                currentOdometer REAL DEFAULT 0,
                ratePerKm REAL DEFAULT 0,
                isDisabled INTEGER DEFAULT 0
            )
        """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS public_holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT,
                year INTEGER,
                date TEXT,
                name TEXT,
                UNIQUE(date, name)
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
