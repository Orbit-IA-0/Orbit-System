"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CodeBlock } from "@/components/CodeBlock";

export function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div className="prose prose-invert prose-sm sm:prose-base max-w-none prose-p:leading-relaxed prose-headings:font-display">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code(props) {
            const { className, children, ...rest } = props as { className?: string; children?: React.ReactNode };
            const match = /language-(\w+)/.exec(className || "");
            const isInline = !match && !String(children).includes("\n");
            if (isInline) {
              return (
                <code className="bg-orbit-surface px-1.5 py-0.5 rounded text-orbit-purple text-[0.85em]" {...rest}>
                  {children}
                </code>
              );
            }
            return <CodeBlock language={match?.[1] || ""} value={String(children).replace(/\n$/, "")} />;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
