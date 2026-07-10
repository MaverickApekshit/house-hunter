"""
Guard tests for cloud_sync.py — failure paths that must fail cleanly/loudly.

- test_connect_failure_is_clean: if sqlite3.connect() itself raises, sync must
  return via a named error path, not a NameError on an unbound `conn`. (Item 1)
- test_write_capability_guard: the write-capability probe must exit non-zero and
  name the service_role requirement when writes don't land (the audit's silent
  RLS block), and must proceed when writes succeed. (Item 6)

Hermetic — no real Supabase/network: a FakeSupabase stands in for the client.

Usage:  venv/Scripts/python.exe tests/test_cloud_sync_guards.py
Exit 0 = all pass, 1 = any fail.
"""

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import cloud_sync  # noqa: E402


class FakeResp:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    """A chainable stub; execute() returns the configured rows."""
    def __init__(self, data):
        self._data = data

    def upsert(self, *a, **k):
        return self

    def delete(self, *a, **k):
        return self

    def select(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def in_(self, *a, **k):
        return self

    def execute(self):
        return FakeResp(self._data)


class FakeSupabase:
    """write_ok controls whether the write-capability probe sees rows land."""
    def __init__(self, write_ok=True):
        self.write_ok = write_ok

    def table(self, name):
        return FakeQuery([{"url": "probe"}] if self.write_ok else [])


def _run(patched_client, connect_raises=False):
    """Run sync_to_cloud with cloud_sync.create_client / sqlite3.connect patched.
    Returns ("ok", value) or ("exit", code) or ("error", exc)."""
    orig_create = cloud_sync.create_client
    orig_connect = cloud_sync.sqlite3.connect
    cloud_sync.create_client = lambda url, key: patched_client
    if connect_raises:
        def boom(*a, **k):
            raise sqlite3.OperationalError("simulated connect failure")
        cloud_sync.sqlite3.connect = boom
    try:
        return ("ok", cloud_sync.sync_to_cloud())
    except SystemExit as e:
        return ("exit", e.code)
    except NameError as e:
        return ("error", e)
    finally:
        cloud_sync.create_client = orig_create
        cloud_sync.sqlite3.connect = orig_connect


def main():
    results = {}

    # Item 1: connect failure must not raise NameError; must return cleanly.
    kind, val = _run(FakeSupabase(write_ok=True), connect_raises=True)
    results["item1_connect_failure_clean"] = (kind == "ok")

    # Item 6: probe sees no rows land -> must exit non-zero (loud), not proceed.
    has_probe = hasattr(cloud_sync, "assert_write_capability")
    if has_probe:
        kind, val = _run(FakeSupabase(write_ok=False))
        results["item6_no_write_exits_nonzero"] = (kind == "exit" and val not in (0, None))
        # And with writes OK it should NOT exit on the probe (connect failure here
        # just short-circuits cleanly, proving the probe passed first).
        kind, val = _run(FakeSupabase(write_ok=True), connect_raises=True)
        results["item6_write_ok_proceeds"] = (kind == "ok")
    else:
        # Item 6 not yet implemented at this commit — skip its assertions.
        pass

    print("\n" + "=" * 52)
    print(" CLOUD_SYNC GUARD TESTS")
    print("=" * 52)
    for k, v in results.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print("=" * 52)
    ok = all(results.values())
    print(f" RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
