"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setTokens } from "@/lib/api";

function OAuthCallbackInner() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const accessToken = params.get("access_token");
    const refreshToken = params.get("refresh_token");
    if (accessToken && refreshToken) {
      setTokens(accessToken, refreshToken);
      router.replace("/chat");
    } else {
      router.replace("/login");
    }
  }, [params, router]);

  return (
    <div className="flex h-screen items-center justify-center bg-orbit-gradient text-slate-400">
      Concluindo login...
    </div>
  );
}

export default function OAuthCallback() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-orbit-gradient text-slate-400">
          Concluindo login...
        </div>
      }
    >
      <OAuthCallbackInner />
    </Suspense>
  );
}
