import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

if (!url || !anonKey) {
  console.warn("VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are required for login.");
}

export const supabase = createClient(url ?? "https://example.supabase.co", anonKey ?? "missing", {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    flowType: "pkce",
  },
});

export function isSupabaseConfigured(): boolean {
  return Boolean(url && anonKey);
}
