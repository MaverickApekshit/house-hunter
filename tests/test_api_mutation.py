"""
Tests for the hardened status-mutation endpoint (POST /api/listings/{id}/status).

Drives the real handler via TestClient in local mode against a synthetic row it
inserts and removes. Asserts: invalid status -> 422; wrong/missing password ->
401; query-param password no longer accepted (header-only); happy path -> 200
and the status actually changes.

Usage:  venv/Scripts/python.exe tests/test_api_mutation.py
Exit 0 = all pass, 1 = any fail.
"""

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import config  # noqa: E402
import api      # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

URL = "https://test.invalid/mutation-check"


def main():
    config.ENVIRONMENT = "local"
    client = TestClient(api.app)
    pw = config.MASTER_PASSWORD

    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute("DELETE FROM listings WHERE url = ?", (URL,))
    cur = conn.execute(
        """INSERT INTO listings (source, external_id, title, rent, deposit, area_sqft,
               bhk, furnishing, locality, url, status)
           VALUES ('TEST', 'mutcheck', 'MUT TEST', 20000, 0, 0, '3 BHK', 'U',
                   'Testville', ?, 'New')""",
        (URL,),
    )
    conn.commit()
    rid = cur.lastrowid

    results = {}
    try:
        # invalid status, valid password -> 422
        r = client.post(f"/api/listings/{rid}/status?status=Banana", headers={"X-Master-Password": pw})
        results["invalid_status_422"] = (r.status_code == 422)

        # valid status, wrong password -> 401
        r = client.post(f"/api/listings/{rid}/status?status=Interested", headers={"X-Master-Password": "wrong"})
        results["wrong_password_401"] = (r.status_code == 401)

        # valid status, password only as query param (no header) -> 401 (path removed)
        r = client.post(f"/api/listings/{rid}/status?status=Interested&password={pw}")
        results["queryparam_password_rejected_401"] = (r.status_code == 401)

        # valid status, valid header password -> 200 and status actually changes
        r = client.post(f"/api/listings/{rid}/status?status=Contacted", headers={"X-Master-Password": pw})
        changed = conn.execute("SELECT status FROM listings WHERE id = ?", (rid,)).fetchone()[0]
        results["happy_path_200"] = (r.status_code == 200 and changed == "Contacted")
    finally:
        conn.execute("DELETE FROM listings WHERE url = ?", (URL,))
        conn.commit()
        conn.close()

    print("\n" + "=" * 52)
    print(" MUTATION ENDPOINT HARDENING TESTS")
    print("=" * 52)
    for k, v in results.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print("=" * 52)
    ok = all(results.values())
    print(f" RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
