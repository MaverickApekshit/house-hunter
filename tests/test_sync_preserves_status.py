"""
End-to-end verification that cloud_sync.py preserves cloud-managed state.

Guards the fix in cloud_sync.py that stops the sync from clobbering dashboard
triage (`status`) and the original `created_at` on rows that already exist in
Supabase, while still inserting genuinely new rows and propagating changed
scrape data (e.g. rent -> price) to existing rows.

Runs against the LIVE Supabase project and the local SQLite DB configured in
`.env`. It is self-cleaning: any row it changes for the test is restored, and
the synthetic row it inserts is deleted from both databases afterward.

Usage (from anywhere):
    venv/Scripts/python.exe tests/test_sync_preserves_status.py

Exit code 0 = all of A1/B2/C3/D4 PASS, 1 = at least one FAIL.

Acceptance criteria:
  A1  An existing cloud row keeps its `status` and `created_at` across syncs.
  B2  A genuinely new local row inserts with status='New'.
  C3  Changed scrape data on an existing row still propagates (rent -> price),
      without disturbing that row's status.
  D4  A batch containing both new and existing rows succeeds in one run.
"""

import os
import sqlite3
import sys

# Make the repo root importable and the working dir, so `import config`,
# `import cloud_sync`, .env loading, and the relative SQLite path all resolve
# regardless of where this script is launched from.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import config          # noqa: E402
import cloud_sync      # noqa: E402
from supabase import create_client  # noqa: E402

SYNTH_URL = "https://test.invalid/fix1-check"


def cloud_client():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def cloud_row(sb, url):
    resp = sb.table("properties").select("*").eq("url", url).execute()
    return resp.data[0] if resp.data else None


def run_sync():
    """Invoke the real production sync entrypoint."""
    cloud_sync.sync_to_cloud()


def main():
    if not config.SUPABASE_URL or not config.SUPABASE_KEY or config.SUPABASE_URL == "your_supabase_url_here":
        print("ABORT: Supabase credentials are not configured in .env")
        return 1

    sb = cloud_client()
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    # Pick a url present in BOTH local SQLite and cloud (so the sync will match
    # it as an existing row). Prefer one whose cloud status is currently 'New'
    # so the test's temporary 'Contacted' set is easy to restore cleanly.
    local_by_url = {
        r["url"]: r
        for r in conn.execute("SELECT * FROM listings WHERE url IS NOT NULL AND url != ''")
    }
    cloud_by_url = {r["url"]: r for r in sb.table("properties").select("*").execute().data}
    common = [u for u in local_by_url if u in cloud_by_url]
    if not common:
        print("ABORT: no url exists in both local SQLite and cloud; run a sync first.")
        conn.close()
        return 1

    pick = next((u for u in common if cloud_by_url[u]["status"] == "New"), common[0])
    orig_cloud = cloud_by_url[pick]
    orig_snap = {"status": orig_cloud["status"], "price": orig_cloud["price"]}
    orig_local_rent = local_by_url[pick]["rent"]

    results = {"A1": False, "B2": False, "C3": False, "D4": False}

    try:
        # --- A1: existing row keeps status + created_at across syncs ---
        sb.table("properties").update({"status": "Contacted"}).eq("url", pick).execute()
        created_before = cloud_row(sb, pick)["created_at"]

        run_sync()
        after1 = cloud_row(sb, pick)
        run_sync()  # idempotence: a second run must not drift either
        after2 = cloud_row(sb, pick)
        results["A1"] = (
            after1["status"] == "Contacted" and after1["created_at"] == created_before and
            after2["status"] == "Contacted" and after2["created_at"] == created_before
        )

        # --- C3: changed scrape data propagates without touching status ---
        new_rent = orig_local_rent + 500
        conn.execute("UPDATE listings SET rent = ? WHERE url = ?", (new_rent, pick))
        conn.commit()
        run_sync()
        after3 = cloud_row(sb, pick)
        results["C3"] = (
            int(after3["price"]) == new_rent and
            after3["status"] == "Contacted" and
            after3["created_at"] == created_before
        )
        # restore local rent (cloud price gets corrected by the B2 sync below)
        conn.execute("UPDATE listings SET rent = ? WHERE url = ?", (orig_local_rent, pick))
        conn.commit()

        # --- B2 + D4: insert a synthetic NEW local row, sync a mixed batch ---
        conn.execute("DELETE FROM listings WHERE url = ?", (SYNTH_URL,))
        conn.commit()
        sb.table("properties").delete().eq("url", SYNTH_URL).execute()
        conn.execute(
            """INSERT INTO listings
               (source, external_id, title, rent, deposit, area_sqft, bhk,
                furnishing, locality, url, latitude, longitude, status)
               VALUES ('TEST', 'fix1-check', 'SYNC FIX TEST ROW', 12345, 0, 0,
                       '3 BHK', 'Unknown', 'Testville', ?, NULL, NULL, 'New')""",
            (SYNTH_URL,),
        )
        conn.commit()

        run_sync()  # batch now contains the new synthetic row + all existing rows
        synth = cloud_row(sb, SYNTH_URL)
        existing_still = cloud_row(sb, pick)
        results["B2"] = synth is not None and synth["status"] == "New"
        results["D4"] = (
            results["B2"] and existing_still is not None and existing_still["status"] == "Contacted"
        )

    finally:
        # Cleanup: remove synthetic row from both DBs, restore the picked row's
        # cloud status/price and local rent to their original values.
        conn.execute("DELETE FROM listings WHERE url = ?", (SYNTH_URL,))
        conn.execute("UPDATE listings SET rent = ? WHERE url = ?", (orig_local_rent, pick))
        conn.commit()
        conn.close()
        sb.table("properties").delete().eq("url", SYNTH_URL).execute()
        sb.table("properties").update(
            {"status": orig_snap["status"], "price": orig_snap["price"]}
        ).eq("url", pick).execute()

    print("\n" + "=" * 44)
    print(" SYNC STATUS-PRESERVATION VERIFICATION")
    print("=" * 44)
    labels = {
        "A1": "existing row keeps status + created_at",
        "B2": "new local row inserts as status='New'",
        "C3": "changed rent propagates, status intact",
        "D4": "mixed new+existing batch succeeds",
    }
    for key in ("A1", "B2", "C3", "D4"):
        print(f"  {key}  {'PASS' if results[key] else 'FAIL'}  {labels[key]}")
    print("=" * 44)

    all_pass = all(results.values())
    print(f" RESULT: {'ALL PASS' if all_pass else 'FAILURES PRESENT'}\n")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
