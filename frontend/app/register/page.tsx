"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { OrbitLogo } from "@/components/OrbitLogo";
import { orbitApi, setTokens } from "@/lib/api";

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
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
      const data = await orbitApi.register(email, password, fullName);
      setTokens(data.access_token, data.refresh_token);
      router.push("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao cadastrar");
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
        <h1 className="text-center text-xl font-display font-semibold mb-1">Crie sua conta</h1>
        <p className="text-center text-sm text-slate-400 mb-6">Comece a usar a Orbit IA gratuitamente</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-slate-300 mb-1 block">Nome completo</label>
            <input value={fullName} onChange={(e) => setFullName(e.target.value)} className="orbit-input w-full" placeholder="Seu nome" />
          </div>
          <div>
            <label className="text-sm text-slate-300 mb-1 block">E-mail</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="orbit-input w-full" placeholder="voce@exemplo.com" />
          </div>
          <div>
            <label className="text-sm text-slate-300 mb-1 block">Senha</label>
            <input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} className="orbit-input w-full" placeholder="Mínimo 8 caracteres" />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button type="submit" disabled={loading} className="orbit-btn-primary w-full">
            {loading ? "Criando conta..." : "Criar conta"}
          </button>
        </form>

        <p className="text-center text-sm text-slate-400 mt-6">
          Já tem conta? <Link href="/login" className="text-orbit-purple hover:underline">Entrar</Link>
        </p>
      </div>
    </main>
  );
}
