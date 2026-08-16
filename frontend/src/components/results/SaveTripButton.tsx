import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { LoginDialog } from "@/components/auth/LoginDialog";
import { Button } from "@/components/ui/button";
import { saveTripOnBackend } from "@/lib/api";
import { syncCreateRoom } from "@/lib/collabApi";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";
import { useCollabStore } from "@/store/collabStore";
import { useTripStore } from "@/store/tripStore";
import type { SavedTrip } from "@/store/tripStore";

export function SaveTripButton({ trip, className }: { trip: SavedTrip; className?: string }) {
  const user = useAuthStore((state) => state.user);
  const isSaved = useTripStore((state) => state.isTripSaved(trip.tripId, trip.tier));
  const saveTrip = useTripStore((state) => state.saveTrip);
  const navigate = useNavigate();
  const [loginOpen, setLoginOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  const saveAndShare = async () => {
    const currentUser = useAuthStore.getState().user;
    if (!currentUser) {
      setLoginOpen(true);
      return;
    }
    setBusy(true);
    try {
      saveTrip(trip);
      const saved = await saveTripOnBackend(trip.tripId);
      if (!saved) throw new Error("Could not save this trip to your account.");
      const room = await syncCreateRoom({
        name: `${trip.destination} with friends`,
        tripId: trip.tripId,
      });
      useCollabStore.getState().mergeRoom(room);
      toast.success("Saved to your account. Invite friends from the trip room.");
      navigate(`/dashboard/rooms/${room.code}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not save trip.");
    } finally {
      setBusy(false);
    }
  };

  if (!user) {
    return (
      <>
        <Button
          type="button"
          variant="outline"
          size="lg"
          onClick={() => setLoginOpen(true)}
          className={cn("h-12 rounded-full px-4 text-sm font-medium whitespace-normal", className)}
        >
          Log in to save and share trip with friends
        </Button>
        <LoginDialog
          open={loginOpen}
          onOpenChange={setLoginOpen}
          onSuccess={() => void saveAndShare()}
          title="Log in to save and share trip with friends"
          description="Sign in with Google or email. We'll save this trip to your account and open a planning room."
        />
      </>
    );
  }

  return (
    <Button
      type="button"
      variant={isSaved ? "secondary" : "outline"}
      size="lg"
      disabled={busy}
      onClick={() => void saveAndShare()}
      className={cn("h-12 rounded-full px-4 text-sm font-medium", className)}
    >
      {busy ? "Saving…" : isSaved ? "Share with friends" : "Save and share with friends"}
    </Button>
  );
}
