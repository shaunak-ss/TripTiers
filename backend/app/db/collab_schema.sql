-- Auth profiles + collaboration rooms (JWT / auth.users).
-- Run this in the Supabase SQL editor. Safe to re-run.

create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  display_name text not null default '',
  avatar_hue integer not null default 200,
  updated_at timestamptz not null default now()
);

alter table profiles add column if not exists email text;
alter table profiles add column if not exists display_name text;
alter table profiles add column if not exists avatar_hue integer;
alter table profiles add column if not exists updated_at timestamptz;

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email, display_name, avatar_hue)
  values (
    new.id,
    new.email,
    coalesce(
      new.raw_user_meta_data->>'full_name',
      new.raw_user_meta_data->>'name',
      split_part(new.email, '@', 1),
      'Traveler'
    ),
    (abs(hashtext(new.id::text)) % 360)
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Recreate collab tables with auth.users FKs (drops demo text-id rows).
drop table if exists collab_messages cascade;
drop table if exists collab_members cascade;
drop table if exists collab_rooms cascade;

create table collab_rooms (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,
  name text not null,
  trip_id text,
  generated_trip_id text,
  host_user_id uuid not null references auth.users(id) on delete cascade,
  trip_brief jsonb not null default '{}'::jsonb,
  generated_trip_brief jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table collab_members (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references collab_rooms(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  display_name text not null,
  email text,
  joined_at timestamptz not null default now(),
  unique (room_id, user_id)
);

create table collab_messages (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references collab_rooms(id) on delete cascade,
  user_id uuid references auth.users(id) on delete cascade,
  display_name text not null,
  body text not null,
  is_bot boolean not null default false,
  kind text not null default 'text' check (kind in ('text', 'choice', 'system')),
  meta jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint collab_messages_user_or_bot check (is_bot or user_id is not null)
);

create index if not exists idx_collab_messages_room on collab_messages (room_id, created_at);
create index if not exists idx_collab_members_room on collab_members (room_id);
create index if not exists idx_collab_members_user on collab_members (user_id);

alter table profiles enable row level security;
alter table collab_rooms enable row level security;
alter table collab_members enable row level security;
alter table collab_messages enable row level security;
alter table saved_trips enable row level security;

drop policy if exists profiles_select_own on profiles;
create policy profiles_select_own on profiles for select using (auth.uid() = id);
drop policy if exists profiles_update_own on profiles;
create policy profiles_update_own on profiles for update using (auth.uid() = id);

-- Anon/authenticated cannot hit collab/saved via the public API key.
-- FastAPI uses the service_role key, which bypasses RLS.
