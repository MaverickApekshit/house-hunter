import sqlite3
import os
import config

DB_PATH = config.DATABASE_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create listings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            external_id TEXT UNIQUE,
            title TEXT,
            rent INTEGER,
            deposit INTEGER,
            area_sqft INTEGER,
            bhk TEXT,
            furnishing TEXT,
            locality TEXT,
            url TEXT,
            latitude REAL,
            longitude REAL,
            commute_time_mins INTEGER,
            distance_km REAL,
            status TEXT DEFAULT 'New', -- New, Interested, Contacted, Rejected
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Idempotent migration for databases created before delisting existed: add
    # last_seen if missing and backfill from added_at so no pre-existing row is
    # ever treated as stale on the first run. (SQLite can't ALTER-ADD a column
    # with a CURRENT_TIMESTAMP default, hence the explicit backfill.)
    existing_cols = [row[1] for row in cursor.execute("PRAGMA table_info(listings)").fetchall()]
    if "last_seen" not in existing_cols:
        cursor.execute("ALTER TABLE listings ADD COLUMN last_seen TIMESTAMP")
        cursor.execute("UPDATE listings SET last_seen = added_at WHERE last_seen IS NULL")
    conn.commit()
    conn.close()

def listing_exists(external_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM listings WHERE external_id = ?', (external_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def add_listing(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Every sighting touches last_seen. If the listing already exists, advance
    # its last_seen (this is what resurrects a previously-stale row) and skip
    # the insert. Both the insert and the duplicate-skip path are covered.
    cursor.execute('SELECT 1 FROM listings WHERE external_id = ?', (data['external_id'],))
    if cursor.fetchone() is not None:
        cursor.execute(
            'UPDATE listings SET last_seen = CURRENT_TIMESTAMP WHERE external_id = ?',
            (data['external_id'],)
        )
        conn.commit()
        conn.close()
        return False

    cursor.execute('''
        INSERT INTO listings (
            source, external_id, title, rent, deposit, area_sqft,
            bhk, furnishing, locality, url, latitude, longitude, last_seen
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        data.get('source'), data.get('external_id'), data.get('title'),
        data.get('rent'), data.get('deposit'), data.get('area_sqft'),
        data.get('bhk'), data.get('furnishing'), data.get('locality'),
        data.get('url'), data.get('latitude'), data.get('longitude')
    ))
    conn.commit()
    conn.close()
    return True

def get_unprocessed_commutes():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM listings WHERE commute_time_mins IS NULL')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_commute(listing_id, commute_time_mins, distance_km):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE listings 
        SET commute_time_mins = ?, distance_km = ?
        WHERE id = ?
    ''', (commute_time_mins, distance_km, listing_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
