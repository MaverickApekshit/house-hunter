"""
End-to-end verification of derived-staleness delisting via `last_seen`.

Delisting is derived state, never a status write (`status` is cloud-managed and
stripped by the sync). A listing still 'New' that hasn't been re-seen in a scrape
for DELIST_AFTER_DAYS is hidden by the API; triaged rows are always shown; a stale
row that reappears in a scrape becomes visible again automatically.

Runs against the LIVE Supabase project and the local SQLite DB from `.env`. It is
self-cleaning. Exercises BOTH API code paths (local SQLite and cloud Supabase) by
driving the real `get_listings` handler through FastAPI's TestClient.

Usage:  venv/Scripts/python.exe tests/test_delisting.py
Exit 0 = all of A1/B2/C3/D4/E5 PASS, 1 = at least one FAIL.

  A1  last_seen exists + backfilled in both stores (0 nulls).
  B2  add_listing touches last_seen on insert AND duplicate-skip.
  C3  last_seen flows to Supabase (matches local for synthetic rows).
  D4  API (local + cloud) hides stale 'New' rows, always shows triaged.
  E5  a resurrected (re-seen) stale row reappears with no status change.
"""

import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import config          # noqa: E402
import database        # noqa: E402
import cloud_sync      # noqa: E402
import api             # noqa: E402
from supabase import create_client  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

U = {"a": "https://test.invalid/delist-a",
     "b": "https://test.invalid/delist-b",
     "c": "https://test.invalid/delist-c"}
EXT = {"a": "delist-a", "b": "delist-b", "c": "delist-c"}
B2_URL, B2_EXT = "https://test.invalid/delist-b2", "delist-b2"


def sb():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def insert_synth(conn, key, status, last_seen):
    conn.execute("DELETE FROM listings WHERE url = ?", (U[key],))
    conn.execute(
        """INSERT INTO listings
           (source, external_id, title, rent, deposit, area_sqft, bhk, furnishing,
            locality, url, latitude, longitude, commute_time_mins, distance_km,
            status, added_at, last_seen)
           VALUES ('TEST', ?, ?, 20000, 0, 0, '3 BHK', 'Unknown', 'Testville',
                   ?, NULL, NULL, 20, 5.0, ?, ?, ?)""",
        (EXT[key], "DELIST TEST " + key, U[key], status, last_seen, last_seen),
    )


def api_urls(mode):
    """Return the set of urls the real get_listings handler returns for `mode`."""
    if mode == "cloud":
        config.ENVIRONMENT = "production"
        api.supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    else:
        config.ENVIRONMENT = "local"
    try:
        resp = TestClient(api.app).get("/api/listings")
        resp.raise_for_status()
        return {row["url"] for row in resp.json()}
    finally:
        config.ENVIRONMENT = "local"


def main():
    database.init_db()
    conn = sqlite3.connect(config.DATABASE_PATH)
    client = sb()

    now = datetime.now(timezone.utc)
    d30 = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    now_s = now.strftime("%Y-%m-%d %H:%M:%S")

    results = {k: False for k in ("A1", "B2", "C3", "D4", "E5")}

    try:
        # --- A1: no null last_seen in either store (post-backfill) ---
        local_nulls = conn.execute("SELECT COUNT(*) FROM listings WHERE last_seen IS NULL").fetchone()[0]
        cloud_nulls = client.table("properties").select("id", count="exact").is_("last_seen", "null").execute().count
        results["A1"] = (local_nulls == 0 and cloud_nulls == 0)

        # --- seed 3 synthetic rows and sync ---
        insert_synth(conn, "a", "New", d30)          # stale New   -> should hide
        insert_synth(conn, "b", "Interested", d30)   # stale triaged -> always show
        insert_synth(conn, "c", "New", now_s)        # fresh New   -> show
        conn.commit()
        cloud_sync.sync_to_cloud()

        # --- D4: both API paths hide (a), show (b) and (c) ---
        local_urls = api_urls("local")
        cloud_urls = api_urls("cloud")
        def d4(urls):
            return (U["a"] not in urls) and (U["b"] in urls) and (U["c"] in urls)
        results["D4"] = d4(local_urls) and d4(cloud_urls)

        # --- C3: last_seen reached Supabase, matches local (minute precision) ---
        def to_min(v):
            return str(v).replace("T", " ")[:16]
        c3 = True
        for k in U:
            cr = client.table("properties").select("last_seen").eq("url", U[k]).execute().data
            lr = conn.execute("SELECT last_seen FROM listings WHERE url = ?", (U[k],)).fetchone()[0]
            c3 = c3 and cr and to_min(cr[0]["last_seen"]) == to_min(lr)
        results["C3"] = bool(c3)

        # --- E5: resurrect (a) by touching last_seen, re-sync, it reappears ---
        conn.execute("UPDATE listings SET last_seen = ? WHERE url = ?", (now_s, U["a"]))
        conn.commit()
        cloud_sync.sync_to_cloud()
        results["E5"] = (U["a"] in api_urls("local")) and (U["a"] in api_urls("cloud"))

        # --- B2: add_listing touches last_seen on insert AND duplicate-skip ---
        data = {"source": "TEST", "external_id": B2_EXT, "title": "B2", "rent": 20000,
                "deposit": 0, "area_sqft": 0, "bhk": "3 BHK", "furnishing": "U",
                "locality": "Testville", "url": B2_URL, "latitude": None, "longitude": None}
        conn.execute("DELETE FROM listings WHERE external_id = ?", (B2_EXT,))
        conn.commit()
        inserted = database.add_listing(data)                       # insert path
        conn.execute("UPDATE listings SET last_seen = ? WHERE external_id = ?", (d30, B2_EXT))
        conn.commit()
        skipped = (database.add_listing(data) is False)             # duplicate-skip path
        touched = conn.execute("SELECT last_seen FROM listings WHERE external_id = ?", (B2_EXT,)).fetchone()[0]
        results["B2"] = inserted and skipped and (str(touched) > d30)

    finally:
        for url in list(U.values()) + [B2_URL]:
            conn.execute("DELETE FROM listings WHERE url = ?", (url,))
        conn.commit()
        conn.close()
        cleanup = sb()
        for url in list(U.values()) + [B2_URL]:
            cleanup.table("properties").delete().eq("url", url).execute()
        config.ENVIRONMENT = "local"

    print("\n" + "=" * 52)
    print(" DELISTING (last_seen) VERIFICATION")
    print("=" * 52)
    labels = {
        "A1": "last_seen present + backfilled, 0 nulls both stores",
        "B2": "add_listing touches last_seen on insert + skip",
        "C3": "last_seen flows to Supabase (matches local)",
        "D4": "API hides stale New, always shows triaged (local+cloud)",
        "E5": "resurrected stale row reappears, no status change",
    }
    for k in ("A1", "B2", "C3", "D4", "E5"):
        print(f"  {k}  {'PASS' if results[k] else 'FAIL'}  {labels[k]}")
    print("=" * 52)
    ok = all(results.values())
    print(f" RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
