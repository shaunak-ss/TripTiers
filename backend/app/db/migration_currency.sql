-- One-time migration for the destination-local-currency feature.
-- Run this in the Supabase SQL editor (Project → SQL Editor → New query → Run).
-- Safe to run on an existing database — schema.sql already has these columns
-- for anyone setting up a fresh database from scratch.

alter table destinations add column if not exists currency_code text not null default 'USD';
alter table trips add column if not exists currency text not null default 'USD';
