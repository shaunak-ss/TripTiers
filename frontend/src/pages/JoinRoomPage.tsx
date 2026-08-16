import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { LoginDialog } from "@/components/auth/LoginDialog";
import { PageTransition } from "@/components/layout/PageTransition";
import { Button } from "@/components/ui/button";
import { syncJoinRoom } from "@/lib/collabApi";
import { useAuthStore } from "@/store/authStore";
import { useCollabStore } from "@/store/collabStore";

export function JoinRoomPage() {
  const { code = "" } = useParams<{ code: string }>();
  const user = useAuthStore((state) => state.user);
  const initialized = useAuthStore((state) => state.initialized);
  const navigate = useNavigate();
  const [loginOpen, setLoginOpen] = useState(false);

  const enterRoom = async () => {
    const current = useAuthStore.getState().user;
    if (!current) {
      setLoginOpen(true);
      return;
    }
    try {
      const room = await syncJoinRoom({ code });
      useCollabStore.getState().mergeRoom(room);
      toast.success(`Joined ${room.name}`);
      navigate(`/dashboard/rooms/${room.code}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not join this room.");
    }
  };

  return (
    <PageTransition>
      <div className="mx-auto flex min-h-[70vh] max-w-md flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="text-sm font-medium tracking-wide text-brand-600 uppercase">Trip room invite</p>
        <h1 className="font-display text-3xl font-semibold">Join {code || "this room"}</h1>
        <p className="text-sm text-neutral-500">
          Chat with the group, then we'll turn the discussion into one shared itinerary.
        </p>
        <Button size="lg" className="h-12 rounded-full px-6" onClick={() => void enterRoom()} disabled={!initialized}>
          {user ? "Join room" : "Log in to join"}
        </Button>
        <Link to="/" className="text-sm text-neutral-500 hover:underline">
          Back home
        </Link>
        <LoginDialog
          open={loginOpen}
          onOpenChange={setLoginOpen}
          onSuccess={enterRoom}
          title="Log in to join this trip room"
          description="Friends are planning together. Log in so we can add you to the chat."
        />
      </div>
    </PageTransition>
  );
}
