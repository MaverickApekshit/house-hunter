# Backlog

Side-findings noted while working, intentionally **not** fixed in the change
that introduced this file (that change was scoped to a single bug: the cloud
sync clobbering `status` / `created_at`). Each item is a separate follow-up.

## Noticed while fixing the sync status-clobber bug

- **Supabase write policies depend entirely on a `service_role` key.** RLS is
  enabled on `public.properties` but there is **no INSERT policy**, and the
  UPDATE policy is restricted to the `authenticated` role. Writes succeed today
  only because `SUPABASE_KEY` in `.env` is a `service_role` key (which bypasses
  RLS). `.env.example` tells operators to use the **anon** key
  (`SUPABASE_KEY=your_supabase_anon_key_here`) — with that key every sync write
  is silently blocked by RLS and no rows land. Either add an explicit
  service-role-only write policy + document the key requirement, or add the
  missing INSERT/UPDATE policies.

- **`properties.status` column default is `'Interested'`, not `'New'`.** Any
  insert path that ever omits `status` would silently create a row as
  "Interested". `cloud_sync.py` always sends `status` for new rows, so it's safe
  today, but the default is a latent trap — consider defaulting to `'New'`.

- **Dedup key mismatch: local `external_id` vs cloud `url`.** Local SQLite
  de-duplicates on `external_id`; the cloud upsert conflict target is `url`. The
  sync fix de-duplicates each batch by `url` to keep a single upsert call safe,
  but the deeper inconsistency remains — two local rows with the same `url` but
  different `external_id` are distinct locally yet collapse to one cloud row.
  Pick one canonical identity for both stores.

## Known, deferred (explicitly out of scope for the sync fix)

- `finally_close(conn)` in `cloud_sync.py` raises `NameError` if the initial
  `sqlite3.connect` itself fails (`conn` is unbound at that point).
- `cloud_sync.py` never syncs `deposit`, `area_sqft`, or `source`; the cloud
  `properties` table has no columns for them, so the API serves fallback
  `0` / `null` / `"Cloud"`.
- No `last_seen` / delisting logic anywhere — dead listings accumulate forever
  in both SQLite and Supabase.
- Commute destination: `.env` `TARGET_LAT`/`TARGET_LNG` resolve ~6 km from the
  configured `TARGET_DESTINATION_NAME`; coordinates win, so commutes measure to
  the wrong place.
- Scraper field parsing: `deposit`/`area_sqft` digit-concatenation hazard
  (e.g. a ₹25,002,500 deposit); `latitude`/`longitude` never extracted
  (hardcoded `None`); case-sensitive locality split yields junk localities.
