"use client";

import React, { useState, useRef, useEffect } from "react";
import { Paperclip, ArrowUp } from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import { DocumentPanel } from "@/components/composer/DocumentPanel";

export function ChatInput() {
  const { activeChatId, isStreaming, sendMessage, createChat } = useChatStore();
  const [input, setInput] = useState("");
  const [showDocs, setShowDocs] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 140) + "px";
  }, [input]);

  // If no active chat, create one then toggle the panel
  const handleAttachClick = async () => {
    if (!activeChatId) {
      await createChat("New Chat");
    }
    setShowDocs((v) => !v);
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    setInput("");
    await sendMessage(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const canSubmit = !!input.trim() && !isStreaming;

  return (
    <div className="relative">
      {/* Document panel — shown above the input */}
      {showDocs && activeChatId && (
        <div className="absolute bottom-full left-0 right-0 mb-2">
          <DocumentPanel onClose={() => setShowDocs(false)} />
        </div>
      )}

      <div
        className="rounded-2xl flex flex-col transition-all"
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          boxShadow: "0 2px 12px rgba(0,0,0,0.3)",
        }}
      >
        <form onSubmit={handleSubmit} className="flex items-end gap-2 p-2">
          {/* Attach button — auto-creates a chat if needed */}
          <button
            type="button"
            id="attach-btn"
            onClick={handleAttachClick}
            title="Attach document or URL"
            className="p-2 rounded-lg shrink-0 transition-all"
            style={{
              color: showDocs ? "var(--accent)" : "var(--text-muted)",
              background: showDocs ? "var(--accent-dim)" : "transparent",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.color = "var(--text-secondary)")
            }
            onMouseLeave={(e) => {
              e.currentTarget.style.color = showDocs
                ? "var(--accent)"
                : "var(--text-muted)";
            }}
          >
            <Paperclip size={18} />
          </button>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isStreaming
                ? "Generating response..."
                : activeChatId
                ? "Ask anything about your documents..."
                : "Ask anything to start a new chat..."
            }
            disabled={isStreaming}
            rows={1}
            className="flex-1 bg-transparent resize-none outline-none py-2 text-sm"
            style={{
              color: "var(--text-primary)",
              maxHeight: 140,
              lineHeight: 1.6,
              caretColor: "var(--accent)",
            }}
          />

          {/* Send button */}
          <button
            type="submit"
            id="send-btn"
            disabled={!canSubmit}
            className="p-2 rounded-xl shrink-0 mb-0.5 transition-all"
            style={{
              background: canSubmit ? "var(--accent)" : "var(--surface-raised)",
              color: canSubmit ? "#fff" : "var(--text-muted)",
              transform: canSubmit ? "scale(1)" : "scale(0.95)",
              boxShadow: canSubmit ? "0 2px 8px rgba(79,142,247,0.4)" : "none",
            }}
          >
            {isStreaming ? (
              <div
                className="w-4 h-4 rounded-sm"
                style={{ background: "var(--text-muted)" }}
              />
            ) : (
              <ArrowUp size={18} />
            )}
          </button>
        </form>

        {/* Hint */}
        <p
          className="text-center text-xs pb-2"
          style={{ color: "var(--text-muted)" }}
        >
          Enter to send · Shift+Enter for new line · 📎 to attach docs
        </p>
      </div>
    </div>
  );
}
