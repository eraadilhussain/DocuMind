"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Source } from "@/types";
import { BookOpen, ChevronDown } from "lucide-react";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  sources?: Source[];
}

export function MessageBubble({
  role,
  content,
  isStreaming = false,
  sources = [],
}: MessageBubbleProps) {
  const [sourcesOpen, setSourcesOpen] = React.useState(false);
  const isUser = role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end animate-fade-in">
        <div
          className="max-w-[70%] px-4 py-3 rounded-2xl rounded-br-sm text-sm"
          style={{
            background: "var(--accent)",
            color: "#fff",
            lineHeight: 1.6,
          }}
        >
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 animate-fade-in">
      {/* Avatar */}
      <div
        className="w-7 h-7 rounded-full shrink-0 flex items-center justify-center text-xs font-bold mt-0.5"
        style={{
          background: "linear-gradient(135deg, var(--accent), #a78bfa)",
          color: "#fff",
          boxShadow: "0 0 10px rgba(79,142,247,0.3)",
        }}
      >
        ✦
      </div>

      <div className="flex-1 min-w-0">
        {/* Message content */}
        <div
          className={`prose text-sm leading-relaxed${isStreaming ? " cursor-blink" : ""}`}
          style={{ color: "var(--text-primary)" }}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content || " "}</ReactMarkdown>
        </div>

        {/* Sources */}
        {sources.length > 0 && !isStreaming && (
          <div className="mt-3">
            <button
              onClick={() => setSourcesOpen(!sourcesOpen)}
              className="flex items-center gap-1.5 text-xs transition-colors"
              style={{ color: "var(--text-secondary)" }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.color = "var(--accent)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.color = "var(--text-secondary)")
              }
            >
              <BookOpen size={12} />
              <span>{sources.length} source{sources.length > 1 ? "s" : ""}</span>
              <ChevronDown
                size={12}
                style={{
                  transform: sourcesOpen ? "rotate(180deg)" : "rotate(0deg)",
                  transition: "transform 0.2s",
                }}
              />
            </button>
            {sourcesOpen && (
              <div className="mt-1.5 space-y-1">
                {sources.map((src, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 text-xs px-2 py-1.5 rounded-md"
                    style={{
                      background: "var(--surface-raised)",
                      border: "1px solid var(--border)",
                      color: "var(--text-secondary)",
                    }}
                  >
                    <span
                      className="w-4 h-4 rounded text-center text-xs font-bold shrink-0 flex items-center justify-center"
                      style={{ background: "var(--accent-dim)", color: "var(--accent)" }}
                    >
                      {i + 1}
                    </span>
                    <span className="truncate">{src.source}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
