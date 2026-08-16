# TripTiers — Frontend

One trip, three ways to take it. This is the frontend implementation of TripTiers, built against the spec in [`../FRONTEND_BUILD_SPEC.md`](../FRONTEND_BUILD_SPEC.md).

Frontend only — there is no backend yet. All trip data comes from `src/mocks/`, shaped exactly like the eventual real API response (`src/types/trip.ts`), so wiring in real agents later is a drop-in replacement for `src/mocks/api.ts`.

## Tech stack

React 18 + Vite + TypeScript · Tailwind CSS v4 · shadcn/ui (Base UI primitives) · Framer Motion · React Router v6 · Zustand · React Hook Form + Zod · Lucide React · date-fns.

## Getting started

Requires **Node.js 20+** (developed against Node 24) and npm.

```bash
cd frontend
npm install
npm run dev
```

Then open the URL Vite prints (defaults to **http://localhost:5173**).

## Other scripts

```bash
npm run build     # type-check + production build to dist/
npm run preview   # preview the production build locally
npm run lint      # oxlint
```

## Trying it out

1. Land on `/` and click **Plan my trip**.
2. Walk through the 3-step wizard (destination/dates → budget/travelers → review) and submit.
3. Watch the generating screen narrate progress, then land on `/results/:tripId` with three tier options.
4. Toggle **Show differences**, open a tier's **See full plan** for the full day-by-day itinerary, and try **Save trip**.
5. Visit `/trips` to see saved trips (persisted to `localStorage`, so they survive a refresh).

Generated trips and saved trips are persisted in `localStorage` under the `triptiers.*` keys — clear site data to reset.

## Project structure

```
src/
  components/
    ui/              # shadcn/ui primitives
    trip-search/      # wizard steps
    results/          # tier card, comparison toggle, itinerary accordion, booking cards
    layout/           # nav, footer, page transition, layout shells
  pages/               # one file per route
  mocks/               # fixture trips + getMockTripResult() / generateMockTripResult()
  store/               # zustand store (search input, active trip, saved trips)
  types/               # trip.ts data contract
  lib/                 # cn(), formatCurrency, date helpers, motion variants, tier metadata
```

## Notes

- No real network calls are made; `src/mocks/api.ts` simulates async latency so swapping in real fetches later requires no component changes.
- Dark mode follows the OS setting (`prefers-color-scheme`) via Tailwind's `dark:` variant.
- Motion respects `prefers-reduced-motion` globally via Framer Motion's `MotionConfig`.
