import { useState } from "react";
import { toast } from "sonner";
import { PageTransition } from "@/components/layout/PageTransition";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/store/authStore";

export function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const updateProfile = useAuthStore((state) => state.updateProfile);
  const [name, setName] = useState(user?.name ?? "");
  const [busy, setBusy] = useState(false);

  if (!user) return null;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    try {
      await updateProfile({ name });
      toast.success("Profile updated.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not update profile.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-lg px-4 py-8 sm:px-8 sm:py-12">
        <h1 className="font-display text-2xl font-semibold sm:text-3xl">Change user profile</h1>
        <p className="mt-1 text-neutral-500">This name is what friends see in the planning room chat.</p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4 rounded-2xl border border-border p-5">
          <div className="flex items-center gap-3">
            <span
              className="flex size-14 items-center justify-center rounded-full text-lg font-semibold text-white"
              style={{ backgroundColor: `hsl(${user.avatarHue} 70% 42%)` }}
            >
              {user.name.slice(0, 1).toUpperCase()}
            </span>
            <div>
              <p className="font-medium">{user.name}</p>
              <p className="text-sm text-neutral-500">{user.email}</p>
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="profile-name">Name</Label>
            <Input
              id="profile-name"
              className="h-11 rounded-xl px-3"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="profile-email">Email</Label>
            <Input id="profile-email" type="email" className="h-11 rounded-xl px-3" value={user.email} disabled />
            <p className="text-xs text-neutral-400">Email comes from your login provider and cannot be changed here.</p>
          </div>
          <Button type="submit" size="lg" className="h-11 rounded-full" disabled={busy}>
            {busy ? "Saving…" : "Save profile"}
          </Button>
        </form>
      </div>
    </PageTransition>
  );
}
