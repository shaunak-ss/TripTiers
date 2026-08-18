import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useShallow } from "zustand/react/shallow";
import { PageTransition } from "@/components/layout/PageTransition";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchMyRooms, fetchMySavedTrips, syncCreateRoom, syncJoinRoom } from "@/lib/collabApi";
import { useAuthStore } from "@/store/authStore";
import { useCollabStore } from "@/store/collabStore";
import type { SavedTrip } from "@/store/tripStore";

export function InvitePage() {
  const user = useAuthStore((state) => state.user);
  const rooms = useCollabStore(useShallow((state) => (user ? state.roomsForUser(user.id) : [])));
  const setRooms = useCollabStore((state) => state.setRooms);
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [tripId, setTripId] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [savedTrips, setSavedTrips] = useState<SavedTrip[]>([]);

  useEffect(() => {
    void fetchMyRooms().then(setRooms);
    void fetchMySavedTrips().then(setSavedTrips);
  }, [setRooms]);

  if (!user) return null;

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const room = await syncCreateRoom({ name, tripId: tripId || undefined });
      useCollabStore.getState().mergeRoom(room);
      toast.success(`Room ${room.code} is ready. Share the invite link with friends.`);
      navigate(`/dashboard/rooms/${room.code}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not create room.");
    }
  };

  const handleJoin = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const room = await syncJoinRoom({ code: joinCode });
      useCollabStore.getState().mergeRoom(room);
      toast.success(`Joined ${room.name}`);
      navigate(`/dashboard/rooms/${room.code}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not join room.");
    }
  };

  const copyInvite = async (code: string) => {
    await navigator.clipboard.writeText(code);
    toast.success("Invite code copied.");
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl px-4 py-8 sm:px-8 sm:py-12">
        <h1 className="font-display text-2xl font-semibold sm:text-3xl">Invite friends to join room</h1>
        <p className="mt-1 text-neutral-500">
          Create a planning room, share the code, then chat until you're ready to generate one itinerary for the group.
        </p>

        <form onSubmit={handleCreate} className="mt-8 flex flex-col gap-4 rounded-2xl border border-border p-5">
          <h2 className="font-display text-lg font-semibold">Start a room</h2>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="room-name">Room name</Label>
            <Input
              id="room-name"
              className="h-11 rounded-xl px-3"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Bali 2026 squad"
            />
          </div>
          {savedTrips.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="room-trip">Attach a saved trip (optional)</Label>
              <select
                id="room-trip"
                className="h-11 rounded-xl border border-input bg-transparent px-3 text-sm"
                value={tripId}
                onChange={(event) => setTripId(event.target.value)}
              >
                <option value="">None — decide in chat</option>
                {savedTrips.map((trip) => (
                  <option key={`${trip.tripId}-${trip.tier}`} value={trip.tripId}>
                    {trip.destination} · {trip.tier}
                  </option>
                ))}
              </select>
            </div>
          )}
          <Button type="submit" size="lg" className="h-11 rounded-full">
            Create room
          </Button>
        </form>

        <form onSubmit={handleJoin} className="mt-6 flex flex-col gap-4 rounded-2xl border border-border p-5">
          <h2 className="font-display text-lg font-semibold">Join with a code</h2>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="join-code">Invite code</Label>
            <Input
              id="join-code"
              className="h-11 rounded-xl px-3 uppercase"
              value={joinCode}
              onChange={(event) => setJoinCode(event.target.value.toUpperCase())}
              placeholder="AB12CD"
            />
          </div>
          <Button type="submit" variant="outline" size="lg" className="h-11 rounded-full">
            Join room
          </Button>
        </form>

        {rooms.length > 0 && (
          <div className="mt-8">
            <h2 className="font-display text-lg font-semibold">Your rooms</h2>
            <ul className="mt-3 flex flex-col gap-2">
              {rooms.map((room) => (
                <li
                  key={room.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border px-4 py-3"
                >
                  <Link to={`/dashboard/rooms/${room.code}`} className="min-w-0 font-medium hover:underline">
                    {room.name} <span className="text-neutral-400">· {room.code}</span>
                  </Link>
                  <Button type="button" variant="ghost" size="sm" onClick={() => copyInvite(room.code)}>
                    Copy invite
                  </Button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </PageTransition>
  );
}
