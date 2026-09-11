"use client";

import React, { useEffect, useRef } from "react";
import { useChatStore } from "@/store/chatStore";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/composer/ChatInput";
import { Sparkles, FileText } from "lucide-react";

const SUGGESTIONS = [
  "Summarise the key points",
  "What are the main findings?",
  "Explain the methodology",
  "List the conclusions",
];

export function ChatWindow() {
  const { activeChatId, messages, isStreaming, streamingContent, streamingSources } =
    useChatStore();
  const { sendMessage } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages / streaming tokens
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  // Welcome / empty state
  if (!activeChatId) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex-1 flex flex-col items-center justify-center px-4 text-center">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5"
            style={{
              background: "linear-gradient(135deg, var(--accent), #a78bfa)",
              boxShadow: "0 0 30px rgba(79,142,247,0.3)",
            }}
          >
            <Sparkles size={24} className="text-white" />
          </div>
          <h2 className="text-2xl font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
            What would you like to explore?
          </h2>
          <p className="text-sm mb-8 max-w-sm" style={{ color: "var(--text-secondary)" }}>
            Start a new chat, upload a document, and ask questions. DocuMind will
            retrieve and synthesise your content.
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => {}}
                className="px-4 py-2 text-sm rounded-full transition-all"
                style={{
                  background: "var(--surface-raised)",
                  border: "1px solid var(--border)",
                  color: "var(--text-secondary)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--accent)";
                  e.currentTarget.style.color = "var(--accent)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border)";
                  e.currentTarget.style.color = "var(--text-secondary)";
                }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <div
          className="p-4"
          style={{ borderTop: "1px solid var(--border)" }}
        >
          <div className="max-w-3xl mx-auto">
            <ChatInput />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
          {messages.length === 0 && !isStreaming && (
            <div className="text-center py-12" style={{ color: "var(--text-muted)" }}>
              <FileText size={32} className="mx-auto mb-3 opacity-40" />
              <p className="text-sm">
                Upload a document and start asking questions.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              role={msg.role}
              content={msg.content}
            />
          ))}

          {/* Streaming bubble */}
          {isStreaming && (
            <MessageBubble
              role="assistant"
              content={streamingContent}
              isStreaming={true}
              sources={streamingSources}
            />
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div
        className="p-4"
        style={{ borderTop: "1px solid var(--border)", background: "var(--background)" }}
      >
        <div className="max-w-3xl mx-auto">
          <ChatInput />
        </div>
      </div>
    </div>
  );
}
