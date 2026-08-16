import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabase";

export function AuthCallbackPage() {
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    const finish = async () => {
      const params = new URLSearchParams(window.location.search);
      const hasCode = params.has("code");
      const { data: existing } = await supabase.auth.getSession();
      if (!existing.session && hasCode) {
        const { error } = await supabase.auth.exchangeCodeForSession(window.location.href);
        if (error && !cancelled) {
          navigate("/?authError=1", { replace: true });
          return;
        }
      }
      const { data } = await supabase.auth.getSession();
      if (cancelled) return;
      navigate(data.session ? "/dashboard" : "/", { replace: true });
    };
    void finish();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  return (
    <div className="flex min-h-dvh items-center justify-center px-6 text-center">
      <p className="text-sm text-neutral-500">Signing you in…</p>
    </div>
  );
}
