# TripTiers (Trip-Ease)

**One trip request, three real ways to take it — solo or planned live with friends in a group chat.**

TripTiers turns "we should go to Bali" into three fully-priced, day-by-day itineraries (Backpacker / Comfort / Luxury) built from real flight prices, cost-aware hotel estimates, and AI-generated day plans grounded in curated destination facts. Groups can plan together in a shared **Trip Room** chat, where a command-driven AI assistant (`/assistant ...`) fills in a shared trip brief — destination, dates, budget, travelers, style — that anyone can edit, right up until the group generates.

## Demo

- **Demo video:** _[add link here]_
- **Live app:** _[add frontend deploy link here]_
- **Live API:** _[add backend deploy link here]_

## Table of contents

- [How it works](#how-it-works)
- [Key features](#key-features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Repository structure](#repository-structure)
- [Backend deep dive](#backend-deep-dive)
- [Frontend deep dive](#frontend-deep-dive)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [Testing](#testing)
- [Deployment](#deployment)

## How it works

1. **Solo mode:** a user fills a 3-step wizard (destination/dates → budget/travelers → review). The backend runs a pipeline that fetches a real cheapest flight, estimates hotel cost per tier, asks Gemini to sanity-check pricing/highlights, and generates a day-by-day itinerary per tier — all three tiers are built from the *same* flight and destination facts so they're a fair, apples-to-apples comparison.
2. **Group mode:** a user creates a **Trip Room** and invites friends by code/link. Everyone chats freely; anyone can type `/assistant <instruction>` (e.g. `/assistant 4 day trip to Thailand from Delhi, budget 2000`) and the assistant extracts structured fields (destination, dates, budget, travelers, tier, pace, dietary) into a shared **trip brief** shown in the room sidebar. Any member can update any field at any time — last write wins. Once the brief is complete, the group generates a trip together and it's saved to the room.

## Key features

- **Three-tier trip generation** — Backpacker, Comfort, and Luxury itineraries built from one real flight search + destination facts, so the tiers are genuinely comparable (see [`ItineraryDayCard`](frontend/src/components/results/ItineraryDayCard.tsx), [`TierCard`](frontend/src/components/results/TierCard.tsx)).
- **Real flight pricing** via the Kiwi Tequila API (with a `KIWI_MOCK` fallback for local dev without partner API access), cached in Redis/in-memory and durably in Postgres so repeat searches and API outages don't block generation.
- **AI itinerary + tiering + destination-facts agents** powered by Google Gemini, using Pydantic-schema structured output so every LLM call returns validated, typed data instead of free-form text.
- **Group trip rooms** with realtime-ish chat (short-poll), a command-driven assistant (`/assistant ...`), inline multiple-choice questions for ambiguous fields (e.g. "what trip styles are available?"), and a shared, always-editable trip brief.
- **Deterministic input normalization** for messy chat input — dates ("three august 2026", "21 aug 2026", "next friday"), budgets ("20k", "₹20,000", "twenty thousand"), traveler counts ("solo", "a couple", "five of us"), and tier/pace synonyms all normalize to strict typed values before hitting the pipeline.
- **Auth + persistence via Supabase** — email/password and Google OAuth, saved trips per user, and Postgres-backed collaboration rooms with row-level durability for messages, members, and the trip brief.
- **MCP (Model Context Protocol) server** exposing the same flight-search, destination-facts, hotel-cost, and budget-normalization tools to any MCP-compatible client (e.g. Claude Desktop, Cursor) — the FastAPI pipeline also calls these underlying functions directly for speed.
- **Deterministic quality gates** — after generation, `validate_trip_result` checks itineraries aren't empty, tiers aren't missing, and prices aren't below the flight cost alone; a failed check retries once before surfacing an error instead of silently returning a broken trip.

## Architecture

```mermaid
flowchart LR
    subgraph Client["Frontend — React + Vite"]
        UI[Trip wizard / Results / Trip Rooms]
    end

    subgraph API["Backend — FastAPI"]
        Routers["/api/trips, /api/collab, /api/me"]
        Orchestrator[Trip Pipeline]
        Agents["Gemini agents\n(tiering, itinerary, destination facts,\nconcierge, collab-extract)"]
        Validators["Normalizers + deterministic\nvalidators (dates, budget, tiers)"]
    end

    subgraph Data["Data & integrations"]
        Supabase[(Supabase\nPostgres + Auth)]
        Redis[(Redis / in-memory cache)]
        Kiwi[Kiwi Tequila\nflight search]
        Gemini[Google Gemini API]
    end

    UI -->|fetch + Bearer JWT| Routers
    Routers --> Orchestrator
    Orchestrator --> Agents
    Orchestrator --> Validators
    Agents --> Gemini
    Orchestrator --> Kiwi
    Orchestrator --> Redis
    Routers --> Supabase
    Orchestrator --> Supabase
```

The trip pipeline (`backend/app/orchestrator/trip_pipeline.py`) is the heart of the backend:

1. Resolve destination facts (cached, bootstrapped from Gemini + curated data on first lookup).
2. Search the cheapest real flight for the route/dates (Kiwi, cached).
3. Estimate a hotel price-per-night for each of the three tiers from the destination's cost index.
4. Ask the **tiering agent** (Gemini) to sanity-check pricing, pick stay names, and flag a budget warning if the budget can't cover the flight.
5. Run the **itinerary agent** for all three tiers in parallel to produce a day-by-day plan grounded in curated destination facts (never inventing attraction names).
6. Convert prices to the destination's local currency via live FX rates when needed.
7. Run deterministic validation on the assembled result; retry itinerary generation once for any tier that fails before raising an error.
8. Persist the trip to Supabase and return it.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 8, TypeScript, React Router 7, Zustand, Tailwind CSS v4, shadcn/ui (Base UI primitives), Framer Motion, React Hook Form + Zod |
| Backend | Python 3.11+, FastAPI, Pydantic v2 / Pydantic Settings, `uv` for dependency management, `structlog` for logging, `tenacity` for retries |
| AI | Google Gemini (`google-genai`) via structured JSON-schema output; a FastMCP server exposing the same tools over MCP |
| Data | Supabase (Postgres + Auth), Redis (Upstash-compatible) with an in-memory + Postgres durable fallback |
| External APIs | Kiwi Tequila (flight search), FX rate service (currency conversion) |
| Deploy targets | Render / Fly.io / Railway / Cloud Run (backend, Docker), Vercel / Netlify (frontend, static) |

## Repository structure

```
TripEase/
├── backend/
│   ├── app/
│   │   ├── agents/          # Gemini-backed agents: tiering, itinerary, destination facts, concierge, collab-extract, flight search
│   │   ├── auth/            # Supabase JWT verification (CurrentUserDep)
│   │   ├── db/               # Repositories (trips, collab, destinations, flight cache) + collab_schema.sql + seed data
│   │   ├── mcp_server/       # FastMCP server + underlying tool implementations (search_flights, get_destination_facts, estimate_hotel_cost, normalize_budget)
│   │   ├── orchestrator/     # trip_pipeline.py — the end-to-end trip generation flow
│   │   ├── prompts/          # System prompts (*.prompt.md) for each agent
│   │   ├── routers/          # FastAPI routes: /api/trips, /api/collab, /api/me, /health
│   │   ├── services/         # Gemini client, cache, Kiwi client, FX client, trip-brief field parsing, concierge command handling
│   │   ├── utils/            # dates, number-word parsing, slugs, logging, retry, errors
│   │   └── validators/       # Pydantic schemas + deterministic date/budget normalizers + trip result validator
│   ├── tests/                 # pytest suite (date/budget normalizers, trip-brief fields, pipeline)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/        # ui/ (shadcn primitives), trip-search/, results/, layout/, auth/
│   │   ├── pages/             # One file per route, incl. dashboard/ (rooms, invite, profile, trips)
│   │   ├── store/             # Zustand stores: auth, trip search, collab rooms
│   │   ├── lib/                # API clients, Supabase client, formatting, date helpers
│   │   ├── mocks/              # Fixture trips so the UI runs standalone without a backend
│   │   └── types/              # Shared TypeScript contracts (trip.ts, collab.ts)
│   └── vercel.json / public/_redirects   # SPA rewrite config for Vercel / Netlify
├── DEPLOY.md                  # Step-by-step production deployment checklist
└── FRONTEND_CHATBOT_ITINERARY_SPEC.md   # Product spec for the group-chat trip planning flow
```

## Backend deep dive

**Agents** (`backend/app/agents/`) — each wraps one Gemini call via `create_structured_output`, which enforces a Pydantic JSON schema on the model's response so the rest of the codebase works with typed objects, never raw text:

- `flight_search_agent` — not actually an LLM call; wraps the Kiwi search deterministically and picks the cheapest option.
- `tiering_agent` — given the real flight + hotel estimates, produces per-tier stay names/types, highlights, and a budget warning if needed. Never invents prices.
- `itinerary_agent` — produces a day-by-day plan per tier, grounded in the destination's curated facts (attractions/neighborhoods/tips) so it can't hallucinate places that don't exist. Cached per destination+tier+day-count, with a separate short-TTL cache when group preferences personalize the result.
- `destination_facts_agent` — bootstraps curated facts + a cost index for a destination the first time it's requested; subsequent requests hit the cache/DB.
- `concierge_agent` — powers the Trip Room `/assistant` command: extracts trip-brief fields from a chat instruction, decides whether the user is asking a question that needs a multiple-choice answer (vs. giving an instruction), and resolves relative dates against "today".
- `collab_agent` — extracts a full trip request from an entire room's chat transcript (used by the legacy/no-room-context generate path).

**Orchestrator** (`backend/app/orchestrator/trip_pipeline.py`) ties the above together end-to-end (see [Architecture](#architecture)) and is called from both `/api/trips` (solo) and the collab generate flow (group).

**Deterministic normalization** (`backend/app/validators/`, `backend/app/services/trip_brief_fields.py`) — before any value reaches the pipeline or gets stored in a trip brief, free-text chat input is normalized:

- Dates: `date_normalizer.py` handles ISO, `DD/MM/YYYY`, and natural language ("3 august 2026", "next friday", "sept 5"), including spelled-out day numbers, with sensible year-rollover for partial dates.
- Budget: `budget_normalizer.py` handles `"20k"`, `"₹20,000"`, `"twenty thousand"`, scale words, and currency symbols.
- Travelers/tier/pace: spelled-out numbers and common synonyms ("solo", "a couple", "backpacking" → `backpacker`) are mapped to canonical values.

**Collaboration** (`backend/app/routers/collab.py`, `backend/app/services/concierge_debouncer.py`) — rooms are silent by default; the assistant only acts when a member types `/assistant <instruction>`, extracting and posting confirmations for whatever it resolved, or a small inline multiple-choice question (`kind: "choice"`) when the member asked about available options for a field. Any member can update any already-resolved field — the room always reflects the latest tap/command, not just the first.

**MCP server** (`backend/app/mcp_server/travel_tools_server.py`) exposes `search_flights_tool`, `get_destination_facts_tool`, `estimate_hotel_cost_tool`, and `normalize_budget_tool` over the Model Context Protocol, so the same deterministic/grounded tools the pipeline uses internally can be plugged into any MCP-compatible AI client.

## Frontend deep dive

- **Routing** (`src/App.tsx`) — public routes (landing, results, join-room, auth callback) under `SiteLayout`; a focused wizard flow (`/plan`, `/plan/generating`) under `FocusLayout`; and an authenticated dashboard (`/dashboard/*` — trips, invite, profile, rooms) gated by `RequireAuth`.
- **State** — Zustand stores for auth (`authStore.ts`, backed by Supabase sessions), the solo trip wizard (`tripStore.ts`), and collaboration rooms (`collabStore.ts`).
- **API client** (`src/lib/api.ts`, `src/lib/collabApi.ts`) — talks to the FastAPI backend when `VITE_API_URL` is set; otherwise falls back to `src/mocks/` fixtures so the UI is fully explorable without any backend running.
- **Mock-first design** — every API function has a mock counterpart shaped identically to the real response, so the frontend was originally (and can still be) developed and demoed with zero backend dependency.

## Getting started

Requires **Python 3.11+** with [`uv`](https://docs.astral.sh/uv/), and **Node.js 20+** with npm.

### 1. Backend

```bash
cd backend
cp .env .env.local   # or create .env — see Environment variables below
uv sync --extra dev
uv run python -m app.db.seed        # optional: seed sample destinations
uv run uvicorn app.main:app --reload --port 3001
```

Verify it's up: `curl http://localhost:3001/health` → `{"status":"ok"}`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (defaults to **http://localhost:5173**). Leave `VITE_API_URL` unset to run against mock data only, or point it at `http://localhost:3001` to use the real backend.

### 3. Supabase schema

Run `backend/app/db/collab_schema.sql` in your Supabase project's SQL editor to create the `profiles`, `collab_rooms`, `collab_members`, and `collab_messages` tables (safe to re-run).

## Environment variables

### Backend (`backend/.env`)

| Variable | Required | Notes |
|---|---|---|
| `ENVIRONMENT` | No (default `development`) | `production` requires `REDIS_URL` and either `KIWI_MOCK=true` or `KIWI_API_KEY` |
| `PORT` | No (default `3001`) | |
| `CORS_ORIGIN` | Yes | Comma-separated list of allowed frontend origins |
| `APP_CURRENCY` | No (default `USD`) | `USD` or `INR` |
| `SUPABASE_URL` | Yes | |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Server-side key, never expose to the frontend |
| `SUPABASE_ANON_KEY` | No | Needed for verifying frontend-issued JWTs |
| `GEMINI_API_KEY` | Yes | Free key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | No (default `gemini-flash-lite-latest`) | Use a `-lite` model for a higher free-tier quota |
| `KIWI_API_KEY` | No | Kiwi Tequila is partner-only; leave unset with `KIWI_MOCK=true` for local dev |
| `KIWI_MOCK` | No (default `false`) | Set `true` to skip live Kiwi calls |
| `REDIS_URL` | Required in production | Falls back to in-memory cache if omitted in dev |

### Frontend (`frontend/.env`)

| Variable | Required | Notes |
|---|---|---|
| `VITE_API_URL` | No | Backend base URL. Omit to run entirely on mock data |
| `VITE_SUPABASE_URL` | Yes (for auth) | |
| `VITE_SUPABASE_ANON_KEY` | Yes (for auth) | |

## Testing

```bash
cd backend
uv run pytest
```

Covers date normalization, budget normalization, trip-brief field parsing, and the trip pipeline.

## Deployment

See [`DEPLOY.md`](DEPLOY.md) for a full checklist covering Supabase, Gemini, Redis, backend hosting (Render/Fly.io/Railway/Cloud Run), frontend hosting (Vercel/Netlify), CORS wiring, and smoke testing.



# TripTiers — Chatroom AI Wizard + Personalized Itinerary (Frontend Spec)
*For: Cursor. Scope: FRONTEND ONLY. Backend is being implemented in parallel against this exact contract — do not wait for it to land; build against the shapes below.*

**Revision note:** this replaces the previous version of this spec. The bot is no longer a plain text-only participant — it now asks for trip details as **tappable option chips** embedded in chat messages, the whole group can see and race to answer them, and the group's confirmed trip details are visible as a live summary strip, editable any time by just typing a correction in chat.

---

## 0. What this feature is

"TripTiers Assistant" is a bot participant in the room chat that runs the group through a short wizard — destination, origin city, dates, budget, travelers, trip style, pace, dietary needs — one question at a time, **inside the chat thread**. Each question can arrive as either:

- **A choice message**: the bot's chat bubble includes a row of tappable option chips (e.g. Budget → "Under $1,000" / "$1,000–2,500" / "$2,500–5,000" / "$5,000+"). Any member can tap one, or ignore the chips and just type their own answer in the normal message box instead.
- **A plain question**: for fields that don't suit fixed options (destination, origin city, dates) — the bot just asks in text, and members answer by typing.

**First response wins.** Whoever taps a chip or types a clear answer first locks that field for the whole group — the chips on that bubble then grey out and show who picked it and what they picked. Everyone sees this within the existing 3s poll, no new transport needed.

**Editing later.** If the group wants to change something already locked in — headcount, budget, trip style — they just say so in the chat ("actually make it 6 people", "change the budget to 70k"). The bot detects this as a correction, updates the locked value, and posts a short confirmation. There is no separate "edit" UI — it's just a chat message.

A live **"Trip so far" strip** pinned near the top of the room shows every field's current state (set or still open) so the group never has to scroll back through the chat to check what's been decided.

---

## 1. Type changes

### `frontend/src/types/collab.ts`

```ts
export type CollabMessageKind = "text" | "choice" | "system";

export interface CollabMessageResolution {
  value: string;        // canonical stored value, e.g. "1750" for budget, "comfort" for tier
  optionLabel: string;  // the human-readable label that was picked/typed, e.g. "$1,000–2,500"
  setByUserId: string | null;
  setByName: string;
  setAt: string;
}

export interface CollabMessageMeta {
  field?: string;                       // one of the TripBriefField keys below — present for "choice" and field-asking "text" bot messages
  options?: string[];                   // chip labels — present only for "choice" messages
  resolved?: CollabMessageResolution;   // present once this specific question has been answered by anyone
}

export interface CollabMessage {
  id: string;
  roomId: string;
  userId: string | null;   // null for bot ("choice"/"system") messages
  displayName: string;     // "TripTiers Assistant" for bot messages
  body: string;
  createdAt: string;
  isBot?: boolean;
  kind: CollabMessageKind; // NEW — default to "text" if absent (older cached rooms)
  meta?: CollabMessageMeta; // NEW
}

export type TripBriefField =
  | "destination"
  | "originCity"
  | "startDate"
  | "endDate"
  | "budget"
  | "travelers"
  | "tier"
  | "pace"
  | "dietary";

export interface TripBriefEntry {
  value: string;
  optionLabel: string;
  setByUserId: string | null;
  setByName: string;
  setAt: string;
}

export type TripBrief = Partial<Record<TripBriefField, TripBriefEntry>>;

export interface CollabRoom {
  id: string;
  code: string;
  name: string;
  tripId?: string;
  generatedTripId?: string;
  hostUserId: string;
  members: CollabMember[];
  messages: CollabMessage[];
  createdAt: string;
  tripBrief: TripBrief; // NEW
}
```

### `frontend/src/types/trip.ts`

Unchanged from the previous revision — still add the optional summary field if not already present:

```ts
export interface TripResult {
  // ...existing fields, unchanged...
  groupPreferencesSummary?: string; // optional — only present for collab-generated trips
}
```

### Field display labels (for both the strip and the results tier default)

Use this exact copy so it matches the bot's own phrasing:

```ts
export const TRIP_BRIEF_LABELS: Record<TripBriefField, string> = {
  destination: "Destination",
  originCity: "Flying from",
  startDate: "Start date",
  endDate: "End date",
  budget: "Budget",
  travelers: "Travelers",
  tier: "Trip style",
  pace: "Pace",
  dietary: "Dietary needs",
};
```

---

## 2. New API surface

### `POST /api/collab/rooms/{code}/messages/{messageId}/select`

Called when a member taps a chip on a `choice` message.

```ts
// frontend/src/lib/collabApi.ts — add this
export async function syncSelectOption(input: {
  code: string;
  messageId: string;
  value: string; // the exact chip label, e.g. "$1,000–2,500"
}): Promise<CollabMessage> {
  const res = await fetch(
    `${API_BASE}/api/collab/rooms/${encodeURIComponent(input.code)}/messages/${encodeURIComponent(input.messageId)}/select`,
    {
      method: "POST",
      headers: await authHeaders(),
      body: JSON.stringify({ value: input.value }),
    }
  );
  if (!res.ok) {
    const parsed = await parseJson(res);
    throw new Error((parsed.message as string) || "Could not select that.");
  }
  return (await res.json()) as CollabMessage; // the message, with meta.resolved now set (win OR loss — always re-sync from this)
}
```

**Important:** this call can "lose" the race — if someone else already picked, the backend still returns 200 with the message showing *their* resolution, not an error. Always re-render the chip UI from the returned `meta.resolved` (or the next poll's room state) rather than assuming your own tap won. After calling this, immediately call `fetchRoom` (same pattern the existing `send()` function in `RoomPage.tsx` already uses after posting a message) so the whole room — including the "Trip so far" strip — reflects the outcome without waiting for the next 3s tick.

### Existing endpoints — response shape additions

- `GET /api/collab/rooms/{code}` and the join/create room endpoints now include `tripBrief` on the room object (see §1).
- `CollabMessage` objects everywhere now include `kind` and optionally `meta`.

No other endpoint shapes change.

---

## 3. RoomPage — rendering choice, text, and system bot messages

File: `frontend/src/pages/dashboard/RoomPage.tsx`

Branch on `message.kind` (not just `isBot`) when rendering the message list:

### `kind === "system"`

Render as a small centered pill, not a chat bubble — these are confirmation/change announcements, not conversation:

```tsx
<li key={message.id} className="flex justify-center">
  <span className="rounded-full bg-neutral-100 px-3 py-1 text-xs font-medium text-neutral-600">
    {message.body}
  </span>
</li>
```

### `kind === "choice"`

Bot bubble (same left-aligned brand-tinted style as the previous spec) plus a chip row below the question text:

```tsx
<li key={message.id} className="flex justify-start">
  <div className="flex max-w-[85%] flex-col gap-2">
    <div className="flex items-start gap-2">
      <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-500 text-white">
        <Sparkles className="size-3.5" />
      </div>
      <div className="rounded-2xl bg-brand-50 px-3.5 py-2.5 text-sm text-brand-900">
        <p className="mb-0.5 text-[11px] font-semibold opacity-80">TripTiers Assistant</p>
        <p className="whitespace-pre-wrap">{message.body}</p>
      </div>
    </div>
    {message.meta?.resolved ? (
      <p className="ml-9 text-xs text-neutral-500">
        ✓ {message.meta.resolved.optionLabel} — picked by {message.meta.resolved.setByName}
      </p>
    ) : (
      <div className="ml-9 flex flex-wrap gap-2">
        {message.meta?.options?.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => handleSelect(message.id, option)}
            className="rounded-full border border-brand-200 bg-white px-3 py-1.5 text-xs font-medium text-brand-700 transition hover:bg-brand-50"
          >
            {option}
          </button>
        ))}
      </div>
    )}
  </div>
</li>
```

- `handleSelect` calls `syncSelectOption`, then re-syncs the room (see §2). Disable the tapped button (local optimistic state) while the request is in flight so a double-tap doesn't double-fire.
- Once `message.meta.resolved` is present, always show the resolved line instead of the chips — never show chips for an already-resolved question, even to the member who didn't pick.

### `kind === "text"` and `isBot === true` (plain question, no chips)

Same bubble as `choice` above, minus the chip row / resolved line. Structurally identical to the previous spec's bot bubble.

### `kind === "text"` and `isBot` falsy (human message)

Unchanged from before — existing "mine" vs "theirs" bubble logic.

---

## 4. "Trip so far" strip

New, pinned just under the room header (between the header and the scrollable message list) in `RoomPage.tsx`. Horizontally scrollable row of chips, one per `TripBriefField`, in this fixed order: `destination, originCity, startDate, endDate, travelers, budget, tier, pace, dietary`.

```tsx
<div className="flex shrink-0 gap-2 overflow-x-auto border-b border-border/70 px-4 py-2.5 sm:px-6">
  {FIELD_ORDER.map((field) => {
    const entry = room.tripBrief[field];
    return (
      <span
        key={field}
        className={cn(
          "shrink-0 rounded-full px-3 py-1 text-xs font-medium",
          entry ? "bg-brand-50 text-brand-900" : "bg-neutral-100 text-neutral-400"
        )}
      >
        {TRIP_BRIEF_LABELS[field]}
        {entry ? `: ${entry.optionLabel}` : ""}
      </span>
    );
  })}
</div>
```

- Unset fields show just the label in a muted/greyed chip (visually "still open").
- Set fields show label + value in the brand color, same visual language as the resolved-chip line in §3.
- This strip is purely a read-model of `room.tripBrief` — it needs no separate polling; it updates whenever `room` updates via the existing `mergeRoom` flow.

---

## 5. Sending a plain chat message still works exactly as before

`send()` in `RoomPage.tsx` is unchanged — typing "6 people" or "let's do comfort tier" in the normal text box is still a completely valid way to answer the bot's current question, or to correct an already-set field. The chips are a *shortcut*, not the only path. Don't gate the text input behind "wait for the bot to ask a compatible field" — it should always be available, exactly as it is today.

---

## 6. Results page — trip style default + personalization summary

File: `frontend/src/pages/ResultsPage.tsx`

- Personalization summary pill: unchanged from the previous spec — render `trip.groupPreferencesSummary` near the header when present, hide entirely when absent.
- **New, small addition:** if the room's `tripBrief.tier` was set (you'll have this from the room the user just generated from, or omit this if the results page has no room context available — check whether `ResultsPage` is reachable with room context; if not, skip this bullet, it's a nice-to-have, not required) — default the tier comparison view to the group's chosen tier tab instead of always defaulting to "Comfort". If wiring this through is awkward given how `ResultsPage` currently gets its data, it's fine to leave the existing default-to-Comfort behavior as-is.

---

## 7. What you do NOT need to do

- No WebSocket/SSE — still plain polling, same as before.
- No new pages/routes.
- No change to `syncPostMessage`, `fetchRoom`, `syncJoinRoom`, `syncCreateRoom` call signatures.
- Don't try to reconcile an old resolved `choice` bubble when a field later gets *changed* via chat — a change produces a fresh `system` pill announcing the new value; the original bubble's `meta.resolved` still shows whatever was true when it was first answered. That's fine and expected — the chat is a log, the **strip** (§4) is the always-current source of truth.
- Don't build a custom "type your own answer" input inside the chip row — the existing message composer already serves that purpose (see §5).

---

## 8. Manual test checklist once backend is live

1. Create a room, send an opening message → a `choice` bot message should appear (e.g. asking travelers or trip style) with tappable chips.
2. From a second member/browser, tap a chip → both members should see the chips replaced with "✓ … — picked by …" within a few seconds, and the "Trip so far" strip should update for both.
3. Try tapping an already-resolved chip's sibling option from a different session — it should not overwrite the winner; the response should reflect the existing resolution.
4. Type a plain-text correction for an already-set field ("actually change the budget to 70k") → a system pill should appear announcing the update, and the strip should reflect the new value.
5. Type a plain-text answer (no tapping) to a currently-open question → it should resolve the field just like a tap would.
6. Once all fields are set, confirm a system message announces readiness, and Generate produces a results page showing the personalization summary pill.
