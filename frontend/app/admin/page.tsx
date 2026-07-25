"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { OrbitLogo } from "@/components/OrbitLogo";
import { orbitApi } from "@/lib/api";

interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  is_admin: boolean;
  is_active: boolean;
  preferred_model: string;
}

interface UsageByModel {
  model: string;
  requests: number;
  tokens_input: number;
  tokens_output: number;
  cost_usd: number;
  avg_latency_ms: number;
}

interface PluginLog {
  id: string;
  plugin_name: string;
  success: boolean;
  created_at: string;
}

export default function AdminPage() {
  const router = useRouter();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [usage, setUsage] = useState<{ total_requests: number; total_cost_usd: number; by_model: UsageByModel[] } | null>(null);
  const [logs, setLogs] = useState<PluginLog[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([orbitApi.adminUsers(), orbitApi.adminUsageSummary(30), orbitApi.adminPluginLogs()])
      .then(([u, s, l]) => {
        setUsers(u);
        setUsage(s);
        setLogs(l);
      })
      .catch(() => setError("Acesso restrito a administradores."));
  }, []);

  const handleToggle = async (id: string) => {
    await orbitApi.adminToggleUser(id);
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, is_active: !u.is_active } : u)));
  };

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-orbit-gradient">
        <div className="glass-panel p-8 text-center">
          <p className="text-slate-300">{error}</p>
          <button onClick={() => router.push("/chat")} className="orbit-btn-primary mt-4">Voltar ao chat</button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-orbit-gradient px-4 py-8 md:px-10">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center gap-3 mb-8">
          <button onClick={() => router.push("/chat")} className="orbit-btn-ghost !p-2.5" aria-label="Voltar">
            <ArrowLeft size={18} />
          </button>
          <OrbitLogo />
          <span className="text-sm text-slate-400">/ Painel administrativo</span>
        </div>

        {usage && (
          <section className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <div className="glass-panel p-5">
              <p className="text-xs text-slate-400">Requisições (30 dias)</p>
              <p className="text-2xl font-display font-semibold">{usage.total_requests}</p>
            </div>
            <div className="glass-panel p-5">
              <p className="text-xs text-slate-400">Custo total (USD)</p>
              <p className="text-2xl font-display font-semibold">${usage.total_cost_usd.toFixed(4)}</p>
            </div>
            <div className="glass-panel p-5">
              <p className="text-xs text-slate-400">Usuários cadastrados</p>
              <p className="text-2xl font-display font-semibold">{users.length}</p>
            </div>
          </section>
        )}

        {usage && usage.by_model.length > 0 && (
          <section className="glass-panel p-6 mb-8 overflow-x-auto">
            <h2 className="font-display font-semibold mb-4">Custo por modelo</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 border-b border-orbit-border">
                  <th className="pb-2">Modelo</th>
                  <th className="pb-2">Requisições</th>
                  <th className="pb-2">Tokens in/out</th>
                  <th className="pb-2">Custo (USD)</th>
                  <th className="pb-2">Latência média</th>
                </tr>
              </thead>
              <tbody>
                {usage.by_model.map((m) => (
                  <tr key={m.model} className="border-b border-orbit-border/50">
                    <td className="py-2">{m.model}</td>
                    <td className="py-2">{m.requests}</td>
                    <td className="py-2">{m.tokens_input} / {m.tokens_output}</td>
                    <td className="py-2">${m.cost_usd.toFixed(4)}</td>
                    <td className="py-2">{m.avg_latency_ms.toFixed(0)} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        <section className="glass-panel p-6 mb-8 overflow-x-auto">
          <h2 className="font-display font-semibold mb-4">Usuários</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-orbit-border">
                <th className="pb-2">E-mail</th>
                <th className="pb-2">Nome</th>
                <th className="pb-2">Modelo</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Ação</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-orbit-border/50">
                  <td className="py-2">{u.email}</td>
                  <td className="py-2">{u.full_name || "-"}</td>
                  <td className="py-2">{u.preferred_model}</td>
                  <td className="py-2">{u.is_active ? "Ativo" : "Desativado"}</td>
                  <td className="py-2">
                    <button onClick={() => handleToggle(u.id)} className="orbit-btn-ghost !py-1 !px-3 text-xs">
                      {u.is_active ? "Desativar" : "Reativar"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="glass-panel p-6 overflow-x-auto">
          <h2 className="font-display font-semibold mb-4">Logs de plugins recentes</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-orbit-border">
                <th className="pb-2">Plugin</th>
                <th className="pb-2">Sucesso</th>
                <th className="pb-2">Data</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id} className="border-b border-orbit-border/50">
                  <td className="py-2">{l.plugin_name}</td>
                  <td className="py-2">{l.success ? "✅" : "❌"}</td>
                  <td className="py-2">{new Date(l.created_at).toLocaleString("pt-BR")}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr><td colSpan={3} className="py-4 text-center text-slate-500 text-xs">Nenhum log ainda.</td></tr>
              )}
            </tbody>
          </table>
        </section>
      </div>
    </main>
  );
}
