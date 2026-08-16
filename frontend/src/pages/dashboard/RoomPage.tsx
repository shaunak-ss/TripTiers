import { Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { PageTransition } from "@/components/layout/PageTransition";
import { Button } from "@/components/ui/button";
import {
  generateItineraryFromChat,
  fetchRoom,
  serializeMessages,
  syncJoinRoom,
  syncPostMessage,
  syncSelectOption,
} from "@/lib/collabApi";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import { useCollabStore } from "@/store/collabStore";
import { TRIP_BRIEF_FIELD_ORDER, TRIP_BRIEF_LABELS } from "@/types/collab";

export function RoomPage() {
  const { code = "" } = useParams<{ code: string }>();
  const user = useAuthStore((state) => state.user);
  const room = useCollabStore((state) => state.roomByCode(code));
  const mergeRoom = useCollabStore((state) => state.mergeRoom);
  const setGeneratedTrip = useCollabStore((state) => state.setGeneratedTrip);
  const navigate = useNavigate();
  const [draft, setDraft] = useState("");
  const [generating, setGenerating] = useState(false);
  const [selectingMessageId, setSelectingMessageId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!user || !code) return;
    let cancelled = false;
    const pull = async () => {
      const remote = await fetchRoom(code);
      if (!cancelled && remote) mergeRoom(remote);
    };
    void pull();
    const timer = window.setInterval(() => void pull(), 3000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [code, mergeRoom, user]);

  useEffect(() => {
    if (!user || !code || room) return;
    void (async () => {
      try {
        const remote = await syncJoinRoom({ code });
        mergeRoom(remote);
      } catch {
        // GET poll will 403 until they join from the invite page.
      }
    })();
  }, [code, mergeRoom, room, user]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [room?.messages.length]);

  if (!user) return null;

  if (!room) {
    return (
      <PageTransition>
        <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3 px-6 text-center">
          <h1 className="font-display text-2xl font-semibold">Room not found</h1>
          <p className="max-w-sm text-sm text-neutral-500">
            This invite may be from another browser. Open the join link or enter the code on Invite friends.
          </p>
          <Button size="lg" className="h-11 rounded-full" nativeButton={false} render={<Link to="/dashboard/invite">Back to invite</Link>} />
        </div>
      </PageTransition>
    );
  }

  const send = async (event: React.FormEvent) => {
    event.preventDefault();
    const body = draft.trim();
    if (!body) return;
    setDraft("");
    try {
      const remote = await syncPostMessage({ code: room.code, body });
      const latest = await fetchRoom(room.code);
      if (latest) mergeRoom(latest);
      else mergeRoom({ ...room, messages: [...room.messages, remote] });
    } catch (error) {
      setDraft(body);
      toast.error(error instanceof Error ? error.message : "Could not send.");
    }
  };

  const handleSelect = async (messageId: string, value: string) => {
    if (selectingMessageId) return;
    setSelectingMessageId(messageId);
    try {
      const remote = await syncSelectOption({ code: room.code, messageId, value });
      const latest = await fetchRoom(room.code);
      if (latest) mergeRoom(latest);
      else {
        mergeRoom({
          ...room,
          messages: room.messages.map((message) => (message.id === remote.id ? remote : message)),
        });
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not select that.");
    } finally {
      setSelectingMessageId(null);
    }
  };

  const copyInvite = async () => {
    await navigator.clipboard.writeText(`${window.location.origin}/join/${room.code}`);
    toast.success("Invite link copied.");
  };

  const generate = async () => {
    if (room.messages.length < 2) {
      toast.error("Chat a bit first — we need the group's preferences, dates, and budget.");
      return;
    }
    setGenerating(true);
    try {
      const result = await generateItineraryFromChat({
        roomCode: room.code,
        memberCount: room.members.length,
        messages: serializeMessages(room.messages),
      });
      if (result.trip) {
        setGeneratedTrip(room.code, result.trip.tripId);
        toast.success("Group itinerary is ready.");
        navigate(`/results/${result.trip.tripId}`);
        return;
      }
      const missing = result.missingFields?.length
        ? `Still need: ${result.missingFields.join(", ")}.`
        : result.message;
      toast.error(missing ?? "Keep discussing, then try again.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Generation failed.");
    } finally {
      setGenerating(false);
    }
  };

  const tripBrief = room.tripBrief ?? {};

  return (
    <PageTransition>
      <div className="flex h-[calc(100dvh-3.5rem)] flex-col md:h-dvh">
        <header className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-border/70 px-4 py-3 sm:px-6">
          <div className="min-w-0">
            <h1 className="truncate font-display text-lg font-semibold">{room.name}</h1>
            <p className="text-xs text-neutral-500">
              Code {room.code} · {room.members.map((member) => member.displayName).join(", ")}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" className="h-10 rounded-full" onClick={copyInvite}>
              Copy invite
            </Button>
            {room.generatedTripId && (
              <Button
                className="h-10 rounded-full"
                nativeButton={false}
                render={<Link to={`/results/${room.generatedTripId}`}>View itinerary</Link>}
              />
            )}
            <Button type="button" className="h-10 rounded-full" onClick={generate} disabled={generating}>
              <Sparkles className="size-4" />
              {generating ? "Building itinerary…" : "Generate from chat"}
            </Button>
          </div>
        </header>

        <div className="flex shrink-0 gap-2 overflow-x-auto border-b border-border/70 px-4 py-2.5 sm:px-6">
          {TRIP_BRIEF_FIELD_ORDER.map((field) => {
            const entry = tripBrief[field];
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

        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-6">
          <p className="mb-4 rounded-2xl bg-brand-50 px-4 py-3 text-sm text-brand-900">
            TripTiers Assistant will ask one thing at a time — tap an option or type in the box. Tap Generate once the
            trip looks right.
          </p>
          {room.messages.length === 0 ? (
            <p className="text-sm text-neutral-500">
              No messages yet. Say where you're thinking of going — TripTiers Assistant will help fill in the rest.
            </p>
          ) : (
            <ul className="flex flex-col gap-3">
              {room.messages.map((message) => {
                const kind = message.kind ?? "text";

                if (kind === "system") {
                  return (
                    <li key={message.id} className="flex justify-center">
                      <span className="rounded-full bg-neutral-100 px-3 py-1 text-xs font-medium text-neutral-600">
                        {message.body}
                      </span>
                    </li>
                  );
                }

                if (kind === "choice") {
                  return (
                    <li key={message.id} className="flex justify-start">
                      <div className="flex max-w-[85%] flex-col gap-2">
                        <AssistantBubble body={message.body} />
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
                                disabled={selectingMessageId === message.id}
                                onClick={() => void handleSelect(message.id, option)}
                                className="rounded-full border border-brand-200 bg-white px-3 py-1.5 text-xs font-medium text-brand-700 transition hover:bg-brand-50 disabled:cursor-not-allowed disabled:opacity-60"
                              >
                                {option}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </li>
                  );
                }

                if (message.isBot) {
                  return (
                    <li key={message.id} className="flex justify-start">
                      <div className="flex max-w-[85%]">
                        <AssistantBubble body={message.body} />
                      </div>
                    </li>
                  );
                }

                const mine = message.userId === user.id;
                return (
                  <li key={message.id} className={cn("flex", mine ? "justify-end" : "justify-start")}>
                    <div
                      className={cn(
                        "max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm",
                        mine ? "bg-brand-500 text-white" : "bg-neutral-100 text-neutral-800"
                      )}
                    >
                      {!mine && <p className="mb-0.5 text-[11px] font-semibold opacity-80">{message.displayName}</p>}
                      <p className="whitespace-pre-wrap">{message.body}</p>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={send} className="shrink-0 border-t border-border/70 p-3 sm:p-4">
          <div className="flex gap-2">
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              rows={1}
              placeholder="Share dates, budget, or what you want from this trip…"
              className="min-h-12 flex-1 resize-none rounded-2xl border border-input bg-transparent px-3.5 py-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            />
            <Button type="submit" className="h-12 rounded-full px-5">
              Send
            </Button>
          </div>
        </form>
      </div>
    </PageTransition>
  );
}

function AssistantBubble({ body }: { body: string }) {
  return (
    <div className="flex items-start gap-2">
      <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-brand-500 text-white">
        <Sparkles className="size-3.5" />
      </div>
      <div className="rounded-2xl bg-brand-50 px-3.5 py-2.5 text-sm text-brand-900">
        <p className="mb-0.5 text-[11px] font-semibold opacity-80">TripTiers Assistant</p>
        <p className="whitespace-pre-wrap">{body}</p>
      </div>
    </div>
  );
}
