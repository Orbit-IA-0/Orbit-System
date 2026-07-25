"use client";

import { useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/cjs/styles/prism";
import { Check, Copy } from "lucide-react";

export function CodeBlock({ language, value }: { language: string; value: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="relative group my-3 rounded-xl overflow-hidden border border-orbit-border">
      <div className="flex items-center justify-between px-3 py-1.5 bg-orbit-surface text-xs text-slate-400">
        <span>{language || "texto"}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 hover:text-slate-100 transition-colors"
          aria-label="Copiar código"
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? "Copiado" : "Copiar"}
        </button>
      </div>
      <SyntaxHighlighter
        language={language || "text"}
        style={vscDarkPlus}
        customStyle={{ margin: 0, padding: "1rem", background: "#0d0f1a", fontSize: "0.85rem" }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
}
