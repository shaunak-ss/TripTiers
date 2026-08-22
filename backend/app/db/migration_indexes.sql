-- One-time migration adding indexes for columns that are filtered directly
-- but were never indexed. Run this in the Supabase SQL editor (Project ->
-- SQL Editor -> New query -> Run). Safe to run on an existing database --
-- schema.sql already has these for anyone setting up a fresh database.
--
-- Why these two:
--   - get_trip_result() filters trip_tiers by trip_id on every trip page load.
--   - get_trip_result() (batched) filters itinerary_days by trip_tier_id on
--     every trip page load.
-- Neither column had an index, so Postgres fell back to a sequential scan of
-- the whole table on every request. Both columns are foreign keys, and
-- Postgres does not auto-index FK columns (only the referenced primary key).
--
-- To see the effect yourself, run in the Supabase SQL editor:
--   explain analyze select * from trip_tiers where trip_id = '<some-uuid>';
-- before and after applying this migration -- the plan should move from
-- "Seq Scan on trip_tiers" to "Index Scan using idx_trip_tiers_trip_id".

create index if not exists idx_trip_tiers_trip_id on trip_tiers (trip_id);
create index if not exists idx_itinerary_days_trip_tier_id on itinerary_days (trip_tier_id);
