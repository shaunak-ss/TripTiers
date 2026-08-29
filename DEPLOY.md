# Deploying TripEase — what's left

Based on your current `backend/.env` and `frontend/.env`, here's what's already done vs. what
actually still needs doing.

## Already set up ✅ — nothing to do here

- **Supabase** — project exists, `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY`/`SUPABASE_ANON_KEY`
  (backend) and `VITE_SUPABASE_URL`/`VITE_SUPABASE_ANON_KEY` (frontend) all point at the same
  project and already work (room chat, auth, and messages have been exercised live in this repo).
  The `collab_schema.sql` / `schema.sql` tables are already applied — no migration to run.
- **Gemini** — `GEMINI_API_KEY` set, `GEMINI_MODEL=gemini-flash-lite-latest` (the higher-quota
  model). Nothing to change.
- **Kiwi** — `KIWI_MOCK=true`. Intentional (Tequila is partner-only) — leave as is.

You'll reuse every one of these exact values as environment variables on whichever host you pick
below — no new accounts needed for Supabase or Gemini.

## Actually missing ❌

1. **A place to run the backend** — it's only ever been run locally via `uv run uvicorn`.
2. **A place to host the frontend build** — it's only ever been run locally via `npm run dev`.
3. **`CORS_ORIGIN`** currently only lists `localhost` — needs your real frontend URL once it exists.
4. **`VITE_API_URL`** currently points at `http://localhost:3001` — needs your real backend URL once it exists.

Everything below is just those four things, in order.

### Skipping Redis on purpose

This guide deploys with `ENVIRONMENT=development` (not `production`) specifically so you **don't**
need Redis. The requirement lives entirely in this validator in `app/config.py`:

```python
if self.environment == "production" and not self.redis_url:
    raise ValueError("REDIS_URL is required when ENVIRONMENT=production.")
```

Leave `ENVIRONMENT` unset (or `development`) and it never fires — `cache_service.py` falls back to a
plain in-process cache automatically, no code changes needed. Trade-offs, both fine for a small/demo
deploy with one backend instance:
- Cache resets on every restart/redeploy (nothing persists between them, so occasionally slower, never broken).
- Unhandled backend errors return the raw exception message to API clients instead of a generic one
  (`main.py`'s catch-all handler only hides it when `environment == "production"`).

If you later want a real production setup (shared cache across instances, safer error messages),
create a free Redis DB at [upstash.com](https://upstash.com), set `REDIS_URL` to the
`rediss://default:<TOKEN>@<HOST>:6379` value it gives you, and set `ENVIRONMENT=production`.

## 1. Deploy the backend

`backend/Dockerfile` already exists and works — pick any Docker-friendly host. **Render** is the
easiest free-tier option; steps for others are one-liners at the bottom.

Set these environment variables on the host — copy the first six straight from your local
`backend/.env`, unchanged:

| Variable | Value |
|---|---|
| `SUPABASE_URL` | *(same as your local `.env`)* |
| `SUPABASE_SERVICE_ROLE_KEY` | *(same as your local `.env`)* |
| `SUPABASE_ANON_KEY` | *(same as your local `.env`)* |
| `GEMINI_API_KEY` | *(same as your local `.env`)* |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` |
| `KIWI_MOCK` | `true` |
| `ENVIRONMENT` | `development` — leave as is, this is what skips the Redis requirement |
| `CORS_ORIGIN` | placeholder for now, e.g. `https://placeholder.vercel.app` — you'll fix this in Step 3 ⚠️ new |
| `APP_CURRENCY` | `USD` |

### Render steps

1. Push this repo to GitHub if it isn't already.
2. [dashboard.render.com](https://dashboard.render.com) → **New → Web Service** → connect the repo.
3. **Root Directory**: `backend`. **Runtime**: **Docker** (auto-detects the `Dockerfile`).
4. Add the env vars from the table above.
5. Deploy → you get a URL like `https://triptiers-backend.onrender.com`.
6. Verify: `curl https://<your-backend-url>/health` → `{"status":"ok"}`.

### One-liner equivalents for other hosts

- **Fly.io**: `fly launch` from `backend/` → `fly secrets set KEY=value ...` for the table above → `fly deploy`.
- **Railway**: New Project → Deploy from repo → Root Directory `backend` → add the same vars in Variables tab.
- **Google Cloud Run**: `gcloud run deploy --source backend --set-env-vars ...` (Cloud Run sets `$PORT` automatically; the Dockerfile already reads it).

## 3. Deploy the frontend

Static Vite build — `npm run build` → `frontend/dist/`. **Vercel** example below.

| Variable | Value |
|---|---|
| `VITE_SUPABASE_URL` | *(same as your local `.env`)* |
| `VITE_SUPABASE_ANON_KEY` | *(same as your local `.env`)* |
| `VITE_API_URL` | your backend URL from Step 2, e.g. `https://triptiers-backend.onrender.com` (no trailing slash) ⚠️ new |

### Vercel steps

1. [vercel.com/new](https://vercel.com/new) → import the repo.
2. **Root Directory**: `frontend`. Framework preset **Vite** (build/output defaults are fine).
3. Add the three env vars above.
4. Deploy → you get a URL like `https://your-app.vercel.app`.

> ⚠️ Vite + React Router needs a `vercel.json` in `frontend/` with a catch-all rewrite to `index.html`, otherwise direct/refreshed routes (e.g. `/join/ABC123`) 404. This repo already includes one — just make sure it's committed and pushed.

*(Netlify: same env vars. Base directory `frontend`, build command `npm run build`, publish directory `dist`. The `_redirects` file for SPA fallback is already included at `frontend/public/_redirects`. ⚠️ Netlify's "Publish directory" field must resolve to `frontend/dist` — if it resolves to `frontend` itself (the raw source, not the built output), the site will build "successfully" but show a blank white page, because it'll serve the source `index.html` which references `/src/main.tsx` instead of the compiled bundle. Check the deploy log's "Publish directory" line to confirm.)*

## 4. Close the loop on CORS

Go back to the backend host and set `CORS_ORIGIN` to your real Vercel URL from Step 3 (comma-separate
if you also want to allow a custom domain), then redeploy/restart the backend. This is the only
"circular" step — everything else deploys cleanly in order.

## 5. Smoke test

1. `GET https://<backend>/health` → `{"status":"ok"}`.
2. Sign up on the live frontend URL → lands on dashboard.
3. **Plan my trip** → generate → three tiers render.
4. **Invite friends** → open the room in a second browser as another account → both see each other.
5. In room chat: `/assistant 4 day trip to Thailand from Delhi, budget 2000` → assistant posts `✅ ... set to ...`.
6. **Generate from chat** → lands on a results page.

---

## Troubleshooting

- **Backend won't start**: `ValueError: REDIS_URL is required when ENVIRONMENT=production` → you (or the host's default) set `ENVIRONMENT=production`. Set it to `development` instead, or go set up Redis per the callout above.
- **`429 RESOURCE_EXHAUSTED` from Gemini** → daily free-tier cap hit on `gemini-flash-lite-latest`; switch `GEMINI_MODEL` to another available model and redeploy.
- **Frontend "Failed to fetch"** → `VITE_API_URL` wrong/backend down, or `CORS_ORIGIN` doesn't exactly match the frontend origin (scheme + no trailing slash) — see Step 3.
- **401 on every backend request** → frontend and backend pointing at different Supabase projects (shouldn't happen here since both already share the same `.env` values — just don't edit one without the other).
