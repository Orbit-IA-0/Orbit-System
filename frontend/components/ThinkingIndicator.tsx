import { Bot } from "lucide-react";

export function ThinkingIndicator({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 animate-fadeUp">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-orbit-accent shadow-glow">
        <Bot size={16} className="text-white" />
      </div>
      <div className="glass-panel rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2 text-sm text-slate-300">
        <span>{label}</span>
        <span className="flex gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-orbit-purple animate-pulseDot [animation-delay:0ms]" />
          <span className="h-1.5 w-1.5 rounded-full bg-orbit-purple animate-pulseDot [animation-delay:150ms]" />
          <span className="h-1.5 w-1.5 rounded-full bg-orbit-purple animate-pulseDot [animation-delay:300ms]" />
        </span>
      </div>
    </div>
  );
}
