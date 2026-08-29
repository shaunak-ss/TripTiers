import { create } from "zustand";
import type { User } from "@supabase/supabase-js";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";
import type { AuthUser } from "@/types/collab";

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  initialized: boolean;
  initialize: () => Promise<void>;
  signup: (input: { name: string; email: string; password: string }) => Promise<"session" | "confirm_email">;
  login: (input: { email: string; password: string }) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (input: { name: string }) => Promise<void>;
}

function fallbackUser(user: User): AuthUser {
  const meta = user.user_metadata ?? {};
  const name =
    (typeof meta.full_name === "string" && meta.full_name) ||
    (typeof meta.name === "string" && meta.name) ||
    user.email?.split("@")[0] ||
    "Traveler";
  const hueSource = user.id.replaceAll("-", "");
  const avatarHue = Number.parseInt(hueSource.slice(0, 6), 16) % 360;
  return { id: user.id, name, email: user.email ?? "", avatarHue };
}

const PROFILE_FETCH_TIMEOUT_MS = 4000;

async function profileFromApi(token: string, fallback: AuthUser): Promise<AuthUser> {
  if (!API_BASE) return fallback;
  try {
    const res = await fetch(`${API_BASE}/api/me`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(PROFILE_FETCH_TIMEOUT_MS),
    });
    if (!res.ok) return fallback;
    const body = (await res.json()) as AuthUser;
    return {
      id: body.id,
      name: body.name,
      email: body.email,
      avatarHue: body.avatarHue,
    };
  } catch {
    return fallback;
  }
}

function applySession(token: string | undefined, user: User | undefined) {
  if (!token || !user) {
    useAuthStore.setState({ user: null, accessToken: null });
    return;
  }
  const fallback = fallbackUser(user);
  // Show the Dashboard immediately from the JWT. /api/me can wait — on a
  // sleeping Render instance that call alone is often 10–50s and used to
  // block the whole nav swap from "Log in" → "Dashboard".
  useAuthStore.setState({ user: fallback, accessToken: token });
  void profileFromApi(token, fallback).then((mapped) => {
    const current = useAuthStore.getState();
    if (current.accessToken !== token) return;
    useAuthStore.setState({ user: mapped, accessToken: token });
  });
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  initialized: false,
  initialize: async () => {
    if (!isSupabaseConfigured()) {
      set({ initialized: true, user: null, accessToken: null });
      return;
    }

    const { data } = await supabase.auth.getSession();
    applySession(data.session?.access_token, data.session?.user);

    supabase.auth.onAuthStateChange((_event, session) => {
      applySession(session?.access_token, session?.user);
    });

    set({ initialized: true });
  },
  signup: async ({ name, email, password }) => {
    if (!isSupabaseConfigured()) throw new Error("Supabase is not configured on the frontend.");
    const { data, error } = await supabase.auth.signUp({
      email: email.trim(),
      password,
      options: {
        data: { full_name: name.trim() },
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    if (error) throw new Error(error.message);
    if (!data.session) return "confirm_email";
    applySession(data.session.access_token, data.session.user);
    return "session";
  },
  login: async ({ email, password }) => {
    if (!isSupabaseConfigured()) throw new Error("Supabase is not configured on the frontend.");
    const { data, error } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
    if (error) throw new Error(error.message);
    applySession(data.session?.access_token, data.session?.user);
  },
  loginWithGoogle: async () => {
    if (!isSupabaseConfigured()) throw new Error("Supabase is not configured on the frontend.");
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
        queryParams: { access_type: "offline", prompt: "consent" },
      },
    });
    if (error) throw new Error(error.message);
  },
  logout: async () => {
    await supabase.auth.signOut();
    set({ user: null, accessToken: null });
  },
  updateProfile: async ({ name }) => {
    const token = get().accessToken;
    if (!token) throw new Error("You need to be logged in.");
    const trimmed = name.trim();
    if (trimmed.length < 2) throw new Error("Name should be at least 2 characters.");
    await supabase.auth.updateUser({ data: { full_name: trimmed } });
    if (!API_BASE) {
      const current = get().user;
      if (current) set({ user: { ...current, name: trimmed } });
      return;
    }
    const res = await fetch(`${API_BASE}/api/me`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ displayName: trimmed }),
    });
    if (!res.ok) {
      const body = (await res.json().catch(() => ({}))) as { message?: string };
      throw new Error(body.message ?? "Could not update profile.");
    }
    const body = (await res.json()) as AuthUser;
    set({ user: { id: body.id, name: body.name, email: body.email, avatarHue: body.avatarHue } });
  },
}));

export async function getAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token ?? null;
  if (token) useAuthStore.setState({ accessToken: token });
  return token;
}
