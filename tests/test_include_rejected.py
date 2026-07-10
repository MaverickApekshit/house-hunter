"""
Tests for the include_rejected listing param (both API paths).

Default (include_rejected omitted/false) excludes Rejected rows; ?include_rejected=true
returns them. The derived-staleness filter on 'New' rows applies either way — a
stale 'New' row stays hidden regardless of include_rejected.

Self-cleaning; uses live Supabase for the cloud path. Drives the real handler
through TestClient in both local and production modes.

Usage:  venv/Scripts/python.exe tests/test_include_rejected.py
Exit 0 = all pass, 1 = any fail.
"""

import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import config        # noqa: E402
import api           # noqa: E402
import cloud_sync    # noqa: E402
from supabase import create_client              # noqa: E402
from fastapi.testclient import TestClient       # noqa: E402

REJ = "https://test.invalid/ir-rejected"      # Rejected, fresh
STALE = "https://test.invalid/ir-stale-new"   # New, 30d old  -> always hidden
FRESH = "https://test.invalid/ir-fresh-new"   # New, now      -> always shown


def seed(conn, url, ext, status, last_seen):
    conn.execute("DELETE FROM listings WHERE url = ?", (url,))
    conn.execute(
        """INSERT INTO listings (source, external_id, title, rent, deposit, area_sqft,
               bhk, furnishing, locality, url, latitude, longitude, commute_time_mins,
               distance_km, status, added_at, last_seen)
           VALUES ('TEST', ?, ?, 20000, 0, 0, '3 BHK', 'U', 'Testville', ?,
                   NULL, NULL, 20, 5.0, ?, ?, ?)""",
        (ext, "IR " + ext, url, status, last_seen, last_seen),
    )


def api_urls(mode, include_rejected):
    if mode == "cloud":
        config.ENVIRONMENT = "production"
        api.supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    else:
        config.ENVIRONMENT = "local"
    try:
        path = "/api/listings" + ("?include_rejected=true" if include_rejected else "")
        resp = TestClient(api.app).get(path)
        resp.raise_for_status()
        return {r["url"] for r in resp.json()}
    finally:
        config.ENVIRONMENT = "local"


def main():
    conn = sqlite3.connect(config.DATABASE_PATH)
    now = datetime.now(timezone.utc)
    d30 = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    now_s = now.strftime("%Y-%m-%d %H:%M:%S")
    client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    results = {}

    try:
        seed(conn, REJ, "ir-rejected", "Rejected", now_s)
        seed(conn, STALE, "ir-stale-new", "New", d30)
        seed(conn, FRESH, "ir-fresh-new", "New", now_s)
        conn.commit()
        cloud_sync.sync_to_cloud()

        for mode in ("local", "cloud"):
            default = api_urls(mode, include_rejected=False)
            incl = api_urls(mode, include_rejected=True)
            results[f"{mode}_default_excludes_rejected"] = REJ not in default
            results[f"{mode}_default_shows_fresh_new"] = FRESH in default
            results[f"{mode}_include_shows_rejected"] = REJ in incl
            results[f"{mode}_include_still_hides_stale_new"] = STALE not in incl
            results[f"{mode}_stale_new_hidden_by_default"] = STALE not in default
    finally:
        for url in (REJ, STALE, FRESH):
            conn.execute("DELETE FROM listings WHERE url = ?", (url,))
        conn.commit()
        conn.close()
        for url in (REJ, STALE, FRESH):
            client.table("properties").delete().eq("url", url).execute()
        config.ENVIRONMENT = "local"

    print("\n" + "=" * 56)
    print(" INCLUDE_REJECTED PARAM TESTS (local + cloud)")
    print("=" * 56)
    for k, v in results.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print("=" * 56)
    ok = all(results.values())
    print(f" RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
