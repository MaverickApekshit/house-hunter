-- Cycle 5 (chore/cycle5-hygiene) — cloud DDL applied to public.properties.
-- Applied via the Supabase migration API during the session; recorded here
-- because the repo otherwise has no record of the cloud schema. Idempotent.
--
-- Owner pre-approved for this session only (P1, P2).

-- P1: real columns for scrape data the sync now carries (was served as
--     API fallbacks 0 / null / "Cloud" before).
ALTER TABLE public.properties ADD COLUMN IF NOT EXISTS deposit integer;
ALTER TABLE public.properties ADD COLUMN IF NOT EXISTS area_sqft integer;
ALTER TABLE public.properties ADD COLUMN IF NOT EXISTS source text;

-- P2: a bare insert (no status) should be 'New', not the old 'Interested'
--     latent-trap default. Sync inserts still send status explicitly.
ALTER TABLE public.properties ALTER COLUMN status SET DEFAULT 'New';
