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
