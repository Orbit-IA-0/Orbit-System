"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Download, Send } from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import { ChatMessage, ChatMessageData, ToolEvent } from "@/components/ChatMessage";
import { ThinkingIndicator } from "@/components/ThinkingIndicator";
import { ThemeToggle } from "@/components/ThemeToggle";
import { FileUpload } from "@/components/FileUpload";
import { orbitApi } from "@/lib/api";

export default function ChatPage() {
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [input, setInput] = useState("");
  const [statusLabel, setStatusLabel] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [webSearchEnabled, setWebSearchEnabled] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    orbitApi.me().then((me) => setIsAdmin(me.is_admin)).catch(() => router.replace("/login"));
  }, [router]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, statusLabel]);

  const loadConversation = async (id: string) => {
    const data = await orbitApi.getConversation(id);
    setConversationId(id);
    setMessages(
      data.messages.map((m: { id: string; role: string; content: string }) => ({
        id: m.id, role: m.role, content: m.content,
      }))
    );
  };

  const handleNew = () => {
    setConversationId(undefined);
    setMessages([]);
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text) return;
    setInput("");

    const userMsg: ChatMessageData = { id: `u-${Date.now()}`, role: "user", content: text };
    const assistantMsg: ChatMessageData = { id: `a-${Date.now()}`, role: "assistant", content: "", tools: [] };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setStatusLabel("Orbit IA está pensando...");

    let toolBuffer: ToolEvent[] = [];

    await orbitApi.streamChat(
      { message: text, conversation_id: conversationId, use_web_search: webSearchEnabled },
      {
        onConversation: (id) => setConversationId((prev) => prev || id),
        onStatus: (msg) => setStatusLabel(msg),
        onToolStart: (tool) => {
          toolBuffer = [...toolBuffer, { tool }];
          setMessages((prev) => updateLast(prev, (m) => ({ ...m, tools: toolBuffer })));
        },
        onToolResult: (tool, result) => {
          toolBuffer = toolBuffer.map((t) => (t.tool === tool ? { ...t, result } : t));
          setMessages((prev) => updateLast(prev, (m) => ({ ...m, tools: toolBuffer })));
        },
        onDelta: (content) => {
          setStatusLabel(null);
          setMessages((prev) => updateLast(prev, (m) => ({ ...m, content: m.content + content })));
        },
        onDone: () => setStatusLabel(null),
        onError: (msg) => {
          setStatusLabel(null);
          setMessages((prev) => updateLast(prev, (m) => ({ ...m, content: m.content || `⚠️ ${msg}` })));
        },
      }
    );
  };

  const updateLast = (list: ChatMessageData[], fn: (m: ChatMessageData) => ChatMessageData) => {
    if (list.length === 0) return list;
    const copy = [...list];
    copy[copy.length - 1] = fn(copy[copy.length - 1]);
    return copy;
  };

  return (
    <div className="flex h-screen bg-orbit-gradient">
      <Sidebar activeId={conversationId} onSelect={loadConversation} onNew={handleNew} isAdmin={isAdmin} />

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-orbit-border px-6 py-4">
          <div className="md:hidden"><span className="font-display font-semibold">Orbit IA</span></div>
          <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer select-none">
            <input
              type="checkbox" checked={webSearchEnabled}
              onChange={(e) => setWebSearchEnabled(e.target.checked)}
              className="accent-orbit-purple"
            />
            Busca na web
          </label>
          <div className="flex items-center gap-2">
            {conversationId && (
              <>
                <a href={orbitApi.exportUrl(conversationId, "markdown")} className="orbit-btn-ghost !p-2.5" title="Exportar Markdown">
                  <Download size={16} />
                </a>
              </>
            )}
            <ThemeToggle />
          </div>
        </header>

        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 md:px-10">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center text-center text-slate-500 gap-2">
              <p className="text-lg font-display text-slate-300">O que vamos explorar hoje?</p>
              <p className="text-sm">Pergunte qualquer coisa, envie um arquivo ou peça uma busca atualizada na web.</p>
            </div>
          )}
          <div className="mx-auto max-w-3xl space-y-6">
            {messages.map((m) => (
              <ChatMessage key={m.id} message={m} />
            ))}
            {statusLabel && <ThinkingIndicator label={statusLabel} />}
          </div>
        </div>

        <div className="border-t border-orbit-border p-4 md:p-6">
          <div className="mx-auto flex max-w-3xl items-end gap-2">
            <FileUpload conversationId={conversationId} onUploaded={() => {}} />
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Envie uma mensagem para a Orbit IA..."
              rows={1}
              className="orbit-input flex-1 resize-none max-h-40"
            />
            <button onClick={handleSend} className="orbit-btn-primary !p-3" aria-label="Enviar mensagem">
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
