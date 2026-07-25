"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut, MessageSquarePlus, Search, Settings, ShieldCheck, Trash2 } from "lucide-react";
import { OrbitLogo } from "@/components/OrbitLogo";
import { orbitApi, clearTokens } from "@/lib/api";

interface ConversationSummary {
  id: string;
  title: string;
  updated_at: string;
}

export function Sidebar({
  activeId,
  onSelect,
  onNew,
  isAdmin,
}: {
  activeId?: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  isAdmin?: boolean;
}) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [query, setQuery] = useState("");
  const router = useRouter();

  const load = async (q?: string) => {
    const data = await orbitApi.listConversations(q);
    setConversations(data);
  };

  useEffect(() => {
    load();
  }, [activeId]);

  useEffect(() => {
    const timeout = setTimeout(() => load(query || undefined), 300);
    return () => clearTimeout(timeout);
  }, [query]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await orbitApi.deleteConversation(id);
    load(query || undefined);
    if (id === activeId) onNew();
  };

  const handleLogout = () => {
    clearTokens();
    router.push("/login");
  };

  return (
    <aside className="hidden md:flex md:w-72 shrink-0 flex-col border-r border-orbit-border bg-orbit-surface/60 p-4">
      <OrbitLogo />

      <button onClick={onNew} className="orbit-btn-primary mt-6 flex items-center justify-center gap-2 text-sm">
        <MessageSquarePlus size={16} /> Nova conversa
      </button>

      <div className="relative mt-4">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar conversas..."
          className="orbit-input w-full pl-9 text-sm py-2"
        />
      </div>

      <div className="mt-4 flex-1 space-y-1 overflow-y-auto">
        {conversations.map((c) => (
          <div
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={`group flex items-center justify-between rounded-lg px-3 py-2 text-sm cursor-pointer transition-colors ${
              c.id === activeId ? "bg-orbit-purple/20 text-slate-100" : "text-slate-400 hover:bg-white/5"
            }`}
          >
            <span className="truncate">{c.title}</span>
            <button
              onClick={(e) => handleDelete(e, c.id)}
              className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-500 hover:text-red-400"
              aria-label="Apagar conversa"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
        {conversations.length === 0 && (
          <p className="text-xs text-slate-500 px-3 py-2">Nenhuma conversa ainda. Comece agora!</p>
        )}
      </div>

      <div className="mt-4 space-y-1 border-t border-orbit-border pt-3">
        {isAdmin && (
          <button
            onClick={() => router.push("/admin")}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-white/5"
          >
            <ShieldCheck size={16} /> Painel admin
          </button>
        )}
        <button
          onClick={() => router.push("/settings")}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-white/5"
        >
          <Settings size={16} /> Configurações
        </button>
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-white/5"
        >
          <LogOut size={16} /> Sair
        </button>
      </div>
    </aside>
  );
}
