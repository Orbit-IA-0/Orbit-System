"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const hasToken = typeof window !== "undefined" && localStorage.getItem("orbit_access_token");
    router.replace(hasToken ? "/chat" : "/login");
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center bg-orbit-gradient text-slate-400">
      Carregando Orbit IA...
    </div>
  );
}
