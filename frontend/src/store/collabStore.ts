import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthUser, CollabMessage, CollabRoom } from "@/types/collab";

function roomCode(): string {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  let code = "";
  for (let i = 0; i < 6; i += 1) {
    code += alphabet[Math.floor(Math.random() * alphabet.length)];
  }
  return code;
}

interface CollabState {
  rooms: CollabRoom[];
  createRoom: (input: { name: string; host: AuthUser; tripId?: string }) => CollabRoom;
  joinRoom: (input: { code: string; user: AuthUser }) => CollabRoom;
  postMessage: (input: { code: string; user: AuthUser; body: string }) => CollabMessage;
  setGeneratedTrip: (code: string, tripId: string) => void;
  mergeRoom: (room: CollabRoom) => void;
  setRooms: (rooms: CollabRoom[]) => void;
  roomsForUser: (userId: string) => CollabRoom[];
  roomByCode: (code: string) => CollabRoom | undefined;
}

export const useCollabStore = create<CollabState>()(
  persist(
    (set, get) => ({
      rooms: [],
      createRoom: ({ name, host, tripId }) => {
        const now = new Date().toISOString();
        const room: CollabRoom = {
          id: crypto.randomUUID(),
          code: roomCode(),
          name: name.trim() || `${host.name}'s trip room`,
          tripId,
          hostUserId: host.id,
          members: [{ userId: host.id, displayName: host.name, email: host.email, joinedAt: now }],
          messages: [],
          createdAt: now,
          tripBrief: {},
        };
        set((state) => ({ rooms: [room, ...state.rooms] }));
        return room;
      },
      joinRoom: ({ code, user }) => {
        const room = get().rooms.find((item) => item.code.toUpperCase() === code.trim().toUpperCase());
        if (!room) throw new Error("Room not found. Check the invite code and try again.");
        if (room.members.some((member) => member.userId === user.id)) return room;
        const next: CollabRoom = {
          ...room,
          members: [
            ...room.members,
            { userId: user.id, displayName: user.name, email: user.email, joinedAt: new Date().toISOString() },
          ],
        };
        set((state) => ({ rooms: state.rooms.map((item) => (item.id === next.id ? next : item)) }));
        return next;
      },
      postMessage: ({ code, user, body }) => {
        const text = body.trim();
        if (!text) throw new Error("Write a message first.");
        const room = get().rooms.find((item) => item.code.toUpperCase() === code.trim().toUpperCase());
        if (!room) throw new Error("Room not found.");
        if (!room.members.some((member) => member.userId === user.id)) {
          throw new Error("Join this room before chatting.");
        }
        const message: CollabMessage = {
          id: crypto.randomUUID(),
          roomId: room.id,
          userId: user.id,
          displayName: user.name,
          body: text,
          createdAt: new Date().toISOString(),
          kind: "text",
        };
        set((state) => ({
          rooms: state.rooms.map((item) =>
            item.id === room.id ? { ...item, messages: [...item.messages, message] } : item
          ),
        }));
        return message;
      },
      setGeneratedTrip: (code, tripId) => {
        set((state) => ({
          rooms: state.rooms.map((item) =>
            item.code.toUpperCase() === code.toUpperCase() ? { ...item, generatedTripId: tripId } : item
          ),
        }));
      },
      mergeRoom: (room) => {
        set((state) => {
          const others = state.rooms.filter((item) => item.id !== room.id && item.code !== room.code);
          return { rooms: [room, ...others] };
        });
      },
      setRooms: (rooms) => set({ rooms: Array.isArray(rooms) ? rooms : [] }),
      roomsForUser: (userId) => get().rooms.filter((room) => room.members.some((member) => member.userId === userId)),
      roomByCode: (code) => get().rooms.find((room) => room.code.toUpperCase() === code.toUpperCase()),
    }),
    {
      name: "triptiers.collab",
      partialize: (state) => ({ rooms: state.rooms }),
      // A bad deploy (or version-skewed frontend/backend during a rollout) could
      // have persisted something other than an array under "rooms" before this
      // guard existed. Sanitize on rehydration so an already-corrupted
      // localStorage entry self-heals instead of crashing the app forever.
      merge: (persisted, current) => {
        const rooms = (persisted as Partial<CollabState> | undefined)?.rooms;
        return { ...current, rooms: Array.isArray(rooms) ? rooms : current.rooms };
      },
    }
  )
);
