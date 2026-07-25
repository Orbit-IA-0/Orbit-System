"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { OrbitLogo } from "@/components/OrbitLogo";
import { orbitApi, setTokens } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await orbitApi.login(email, password);
      setTokens(data.access_token, data.refresh_token);
      router.push("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao entrar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-orbit-gradient px-4">
      <div className="w-full max-w-md glass-panel p-8 shadow-glow">
        <div className="flex justify-center mb-6">
          <OrbitLogo size={36} />
        </div>
        <h1 className="text-center text-xl font-display font-semibold mb-1">Bem-vindo de volta</h1>
        <p className="text-center text-sm text-slate-400 mb-6">Entre para continuar sua órbita</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-slate-300 mb-1 block">E-mail</label>
            <input
              type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="orbit-input w-full" placeholder="voce@exemplo.com"
            />
          </div>
          <div>
            <label className="text-sm text-slate-300 mb-1 block">Senha</label>
            <input
              type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
              className="orbit-input w-full" placeholder="••••••••"
            />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button type="submit" disabled={loading} className="orbit-btn-primary w-full">
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <div className="flex items-center gap-3 my-6">
          <div className="h-px flex-1 bg-orbit-border" />
          <span className="text-xs text-slate-500">ou continue com</span>
          <div className="h-px flex-1 bg-orbit-border" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <a href={orbitApi.oauthUrl("google")} className="orbit-btn-ghost text-center text-sm">Google</a>
          <a href={orbitApi.oauthUrl("github")} className="orbit-btn-ghost text-center text-sm">GitHub</a>
        </div>

        <p className="text-center text-sm text-slate-400 mt-6">
          Não tem conta? <Link href="/register" className="text-orbit-purple hover:underline">Cadastre-se</Link>
        </p>
      </div>
    </main>
  );
}
