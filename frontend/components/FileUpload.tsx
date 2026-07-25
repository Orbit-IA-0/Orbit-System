"use client";

import { useRef, useState } from "react";
import { Paperclip, X } from "lucide-react";
import { orbitApi } from "@/lib/api";

export function FileUpload({
  conversationId,
  onUploaded,
}: {
  conversationId?: string;
  onUploaded: (filename: string) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [pending, setPending] = useState<string[]>([]);

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPending((p) => [...p, file.name]);
    try {
      await orbitApi.uploadFile(file, conversationId);
      onUploaded(file.name);
    } finally {
      setPending((p) => p.filter((n) => n !== file.name));
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div className="flex items-center gap-2">
      <input ref={inputRef} type="file" className="hidden" onChange={handleChange}
             accept=".pdf,.docx,.txt,image/png,image/jpeg" />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="orbit-btn-ghost !p-2.5"
        aria-label="Anexar arquivo"
        title="Anexar arquivo (PDF, DOCX, TXT, imagem)"
      >
        <Paperclip size={18} />
      </button>
      {pending.map((name) => (
        <span key={name} className="flex items-center gap-1 text-xs text-slate-400 bg-orbit-surface rounded-full px-2 py-1">
          Enviando {name}... <X size={12} />
        </span>
      ))}
    </div>
  );
}
