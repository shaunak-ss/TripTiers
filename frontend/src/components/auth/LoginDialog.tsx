import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { isSupabaseConfigured } from "@/lib/supabase";
import { useAuthStore } from "@/store/authStore";

interface LoginDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
  title?: string;
  description?: string;
}

export function LoginDialog({
  open,
  onOpenChange,
  onSuccess,
  title = "Log in to save and share",
  description = "Sign in with Google or email. Your session is a Supabase JWT stored only in this browser.",
}: LoginDialogProps) {
  const login = useAuthStore((state) => state.login);
  const signup = useAuthStore((state) => state.signup);
  const loginWithGoogle = useAuthStore((state) => state.loginWithGoogle);
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const handleGoogle = async () => {
    setBusy(true);
    try {
      await loginWithGoogle();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Google sign-in is not enabled yet.");
      setBusy(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!isSupabaseConfigured()) {
      toast.error("Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to frontend/.env");
      return;
    }
    setBusy(true);
    try {
      if (mode === "signup") {
        const result = await signup({ name, email, password });
        if (result === "confirm_email") {
          toast.success("Check your email to confirm, then log in.");
          onOpenChange(false);
          return;
        }
        toast.success("You're in — trips and rooms now save to your account.");
      } else {
        await login({ email, password });
        toast.success("Welcome back.");
      }
      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not log in.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-display text-lg font-semibold">{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <Button
          type="button"
          variant="outline"
          size="lg"
          className="h-11 rounded-full"
          disabled={busy}
          onClick={() => void handleGoogle()}
        >
          Continue with Google
        </Button>
        <div className="flex items-center gap-3 text-xs text-neutral-400">
          <span className="h-px flex-1 bg-border" />
          or email
          <span className="h-px flex-1 bg-border" />
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {mode === "signup" && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="auth-name">Name</Label>
              <Input
                id="auth-name"
                className="h-11 rounded-xl px-3"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Alex"
                autoComplete="name"
                required
              />
            </div>
          )}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="auth-email">Email</Label>
            <Input
              id="auth-email"
              type="email"
              className="h-11 rounded-xl px-3"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@email.com"
              autoComplete="email"
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="auth-password">Password</Label>
            <Input
              id="auth-password"
              type="password"
              className="h-11 rounded-xl px-3"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 6 characters"
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
              required
            />
          </div>
          <Button type="submit" size="lg" className="mt-1 h-11 rounded-full" disabled={busy}>
            {busy ? "Please wait…" : mode === "signup" ? "Create account" : "Log in"}
          </Button>
        </form>
        <p className="text-center text-sm text-neutral-500">
          {mode === "signup" ? "Already have an account?" : "New here?"}{" "}
          <button
            type="button"
            className="font-medium text-brand-600 hover:underline"
            onClick={() => setMode(mode === "signup" ? "login" : "signup")}
          >
            {mode === "signup" ? "Log in" : "Create an account"}
          </button>
        </p>
      </DialogContent>
    </Dialog>
  );
}
