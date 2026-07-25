import clsx from "clsx";
import { Bot, User as UserIcon, Wrench } from "lucide-react";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";

export interface ToolEvent {
  tool: string;
  result?: unknown;
}

export interface ChatMessageData {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  tools?: ToolEvent[];
}

export function ChatMessage({ message }: { message: ChatMessageData }) {
  const isUser = message.role === "user";

  return (
    <div className={clsx("flex gap-3 animate-fadeUp", isUser ? "flex-row-reverse" : "flex-row")}>
      <div
        className={clsx(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-orbit-border" : "bg-orbit-accent shadow-glow"
        )}
      >
        {isUser ? <UserIcon size={16} /> : <Bot size={16} className="text-white" />}
      </div>

      <div className={clsx("max-w-[80%] space-y-2", isUser && "flex flex-col items-end")}>
        {message.tools?.map((t, i) => (
          <div
            key={i}
            className="flex items-center gap-1.5 text-xs text-slate-400 bg-orbit-surface/70 border border-orbit-border rounded-lg px-2.5 py-1 w-fit"
          >
            <Wrench size={12} />
            <span>Usou o plugin <strong className="text-slate-300">{t.tool}</strong></span>
          </div>
        ))}

        <div
          className={clsx(
            "rounded-2xl px-4 py-3",
            isUser
              ? "bg-orbit-accent text-white rounded-tr-sm"
              : "glass-panel rounded-tl-sm"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          ) : (
            <MarkdownRenderer content={message.content || "…"} />
          )}
        </div>
      </div>
    </div>
  );
}
