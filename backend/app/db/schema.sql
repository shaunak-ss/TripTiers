-- TripTiers schema — run this in the Supabase SQL editor (or `supabase db query`).
-- Auth FKs match Section 4 of BACKEND_ARCHITECTURE_SPEC.md.
-- If you haven't enabled Auth users yet, anonymous trip search still works
-- (trips.user_id is nullable). Saving a trip requires a signed-in user.

create table if not exists destinations (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  city text not null,
  country text not null,
  cost_index numeric not null,
  currency_code text not null default 'USD',
  curated_facts jsonb not null default '{}',
  source text not null default 'manual',
  last_updated timestamptz not null default now()
);

create table if not exists trips (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id),
  origin_city text not null,
  destination_slug text not null references destinations(slug),
  start_date date not null,
  end_date date not null,
  budget_input_raw text not null,
  budget_normalized integer not null,
  travelers integer not null default 1,
  status text not null default 'pending',
  currency text not null default 'USD',
  group_preferences_summary text,
  label text,
  created_at timestamptz not null default now()
);

alter table trips add column if not exists group_preferences_summary text;
alter table trips add column if not exists label text;

create table if not exists trip_tiers (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid not null references trips(id) on delete cascade,
  tier text not null check (tier in ('backpacker','comfort','luxury')),
  total_price integer not null,
  flight jsonb not null,
  stay jsonb not null,
  highlights text[] not null,
  created_at timestamptz not null default now(),
  unique (trip_id, tier)
);

create table if not exists itinerary_days (
  id uuid primary key default gen_random_uuid(),
  trip_tier_id uuid not null references trip_tiers(id) on delete cascade,
  day_number integer not null,
  title text not null,
  morning text not null,
  afternoon text not null,
  evening text not null,
  unique (trip_tier_id, day_number)
);

create table if not exists flight_search_cache (
  id uuid primary key default gen_random_uuid(),
  cache_key text unique not null,
  response jsonb not null,
  expires_at timestamptz not null
);

create table if not exists itinerary_skeleton_cache (
  id uuid primary key default gen_random_uuid(),
  cache_key text unique not null,
  days jsonb not null,
  expires_at timestamptz not null
);

create table if not exists saved_trips (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id),
  trip_id uuid not null references trips(id),
  saved_at timestamptz not null default now(),
  unique (user_id, trip_id)
);

create index if not exists idx_flight_cache_key on flight_search_cache (cache_key);
create index if not exists idx_itinerary_cache_key on itinerary_skeleton_cache (cache_key);
create index if not exists idx_trips_destination on trips (destination_slug);
create index if not exists idx_trip_tiers_trip_id on trip_tiers (trip_id);
create index if not exists idx_itinerary_days_trip_tier_id on itinerary_days (trip_tier_id);

create table if not exists collab_rooms (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  name text not null,
  trip_id text,
  generated_trip_id text,
  host_user_id text not null,
  created_at timestamptz not null default now()
);

create table if not exists collab_members (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references collab_rooms(id) on delete cascade,
  user_id text not null,
  display_name text not null,
  email text,
  joined_at timestamptz not null default now(),
  unique (room_id, user_id)
);

create table if not exists collab_messages (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references collab_rooms(id) on delete cascade,
  user_id text not null,
  display_name text not null,
  body text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_collab_messages_room on collab_messages (room_id, created_at);
create index if not exists idx_collab_members_room on collab_members (room_id);
