"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Trash2 } from "lucide-react";
import { OrbitLogo } from "@/components/OrbitLogo";
import { orbitApi } from "@/lib/api";

interface MemoryFact {
  key: string;
  value: string;
}

export default function SettingsPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<{ full_name: string; language: string; preferred_model: string } | null>(null);
  const [facts, setFacts] = useState<MemoryFact[]>([]);
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    orbitApi.me().then(setProfile).catch(() => router.replace("/login"));
    orbitApi.getMemory().then((d) => setFacts(d.facts));
  }, [router]);

  const handleSaveProfile = async () => {
    if (!profile) return;
    await orbitApi.updateProfile(profile);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleAddFact = async () => {
    if (!newKey || !newValue) return;
    await orbitApi.setMemory(newKey, newValue);
    setFacts((prev) => [...prev.filter((f) => f.key !== newKey), { key: newKey, value: newValue }]);
    setNewKey("");
    setNewValue("");
  };

  const handleDeleteFact = async (key: string) => {
    await orbitApi.deleteMemory(key);
    setFacts((prev) => prev.filter((f) => f.key !== key));
  };

  if (!profile) return null;

  return (
    <main className="min-h-screen bg-orbit-gradient px-4 py-8 md:px-10">
      <div className="mx-auto max-w-2xl">
        <div className="flex items-center gap-3 mb-8">
          <button onClick={() => router.push("/chat")} className="orbit-btn-ghost !p-2.5" aria-label="Voltar">
            <ArrowLeft size={18} />
          </button>
          <OrbitLogo />
        </div>

        <section className="glass-panel p-6 mb-6">
          <h2 className="font-display font-semibold text-lg mb-4">Perfil e preferências</h2>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-300 mb-1 block">Nome</label>
              <input
                value={profile.full_name || ""}
                onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                className="orbit-input w-full"
              />
            </div>
            <div>
              <label className="text-sm text-slate-300 mb-1 block">Idioma</label>
              <select
                value={profile.language}
                onChange={(e) => setProfile({ ...profile, language: e.target.value })}
                className="orbit-input w-full"
              >
                <option value="pt-BR">Português (Brasil)</option>
                <option value="en-US">English (US)</option>
                <option value="es-ES">Español</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-300 mb-1 block">Modelo preferido</label>
              <select
                value={profile.preferred_model}
                onChange={(e) => setProfile({ ...profile, preferred_model: e.target.value })}
                className="orbit-input w-full"
              >
                <option value="llama3">Llama 3 (local)</option>
                <option value="mistral">Mistral (local)</option>
                <option value="qwen2.5">Qwen 2.5 (local)</option>
                <option value="gpt-4o">GPT-4o (API)</option>
                <option value="gpt-4o-mini">GPT-4o mini (API)</option>
              </select>
            </div>
            <button onClick={handleSaveProfile} className="orbit-btn-primary">
              {saved ? "Salvo!" : "Salvar alterações"}
            </button>
          </div>
        </section>

        <section className="glass-panel p-6">
          <h2 className="font-display font-semibold text-lg mb-1">Memória da Orbit IA</h2>
          <p className="text-sm text-slate-400 mb-4">
            Fatos e preferências que a Orbit IA lembra entre conversas.
          </p>

          <div className="space-y-2 mb-4">
            {facts.map((f) => (
              <div key={f.key} className="flex items-center justify-between bg-orbit-surface rounded-lg px-3 py-2 text-sm">
                <span><strong className="text-slate-300">{f.key}:</strong> <span className="text-slate-400">{f.value}</span></span>
                <button onClick={() => handleDeleteFact(f.key)} className="text-slate-500 hover:text-red-400" aria-label="Remover">
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
            {facts.length === 0 && <p className="text-xs text-slate-500">Nenhum fato salvo ainda.</p>}
          </div>

          <div className="flex gap-2">
            <input value={newKey} onChange={(e) => setNewKey(e.target.value)} placeholder="chave (ex: linguagem_favorita)" className="orbit-input flex-1 text-sm" />
            <input value={newValue} onChange={(e) => setNewValue(e.target.value)} placeholder="valor (ex: Python)" className="orbit-input flex-1 text-sm" />
            <button onClick={handleAddFact} className="orbit-btn-primary text-sm">Adicionar</button>
          </div>
        </section>
      </div>
    </main>
  );
}
