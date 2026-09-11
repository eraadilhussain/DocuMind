"use client";

import React, { useEffect, useState, useRef } from "react";
import {
  PlusCircle,
  MessageSquare,
  Trash2,
  ChevronDown,
  Sparkles,
  FileText,
  PanelLeftClose,
  Menu,
} from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import { Chat } from "@/types";

function groupChatsByDate(chats: Chat[]): Record<string, Chat[]> {
  const now = new Date();
  const groups: Record<string, Chat[]> = {
    Today: [],
    Yesterday: [],
    "Last 7 days": [],
    Older: [],
  };

  for (const chat of chats) {
    const d = new Date(chat.updated_at);
    const diffDays = Math.floor(
      (now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24)
    );
    if (diffDays === 0) groups["Today"].push(chat);
    else if (diffDays === 1) groups["Yesterday"].push(chat);
    else if (diffDays <= 7) groups["Last 7 days"].push(chat);
    else groups["Older"].push(chat);
  }

  return groups;
}

export function Sidebar() {
  const { chats, activeChatId, documents, loadChats, createChat, selectChat, deleteChat, isSidebarOpen, toggleSidebar } =
    useChatStore();
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    loadChats();
  }, []);

  const handleNewChat = async () => {
    setCreating(true);
    await createChat();
    setCreating(false);
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    setDeletingId(id);
    await deleteChat(id);
    setDeletingId(null);
  };

  const grouped = groupChatsByDate(chats);

  // Count ready documents for the active chat
  const readyDocs = documents.filter((d) => d.status === "READY").length;
  const processingDocs = documents.filter(
    (d) => !["READY", "FAILED"].includes(d.status)
  ).length;

  if (!isSidebarOpen) {
    return (
      <button
        onClick={toggleSidebar}
        className="fixed top-4 left-4 z-50 p-2 rounded-lg transition-colors shadow-lg flex items-center justify-center group"
        style={{
          background: "var(--surface)",
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
        title="Open Sidebar"
      >
        <Menu size={18} className="transition-transform group-hover:scale-110" />
      </button>
    );
  }

  return (
    <aside
      className="flex flex-col h-full shrink-0 transition-all duration-300"
      style={{
        width: 260,
        background: "var(--surface)",
        borderRight: "1px solid var(--border)",
      }}
    >
      {/* Logo */}
      <div
        className="flex items-center justify-between px-4 py-4"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: "var(--accent)", boxShadow: "0 0 12px rgba(79,142,247,0.4)" }}
          >
            <Sparkles size={14} className="text-white" />
          </div>
          <span className="font-semibold text-base" style={{ color: "var(--text-primary)" }}>
            DocuMind
          </span>
        </div>
        <button
          onClick={toggleSidebar}
          className="p-1 rounded hover:bg-black/10 transition-colors"
          style={{ color: "var(--text-muted)" }}
          title="Close Sidebar"
        >
          <PanelLeftClose size={18} />
        </button>
      </div>

      {/* New Chat button */}
      <div className="px-3 py-3">
        <button
          id="new-chat-btn"
          onClick={handleNewChat}
          disabled={creating}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-sm font-medium transition-all"
          style={{
            background: "var(--accent-dim)",
            color: "var(--accent)",
            border: "1px solid rgba(79,142,247,0.25)",
          }}
          onMouseEnter={(e) =>
            (e.currentTarget.style.background = "rgba(79,142,247,0.2)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.background = "var(--accent-dim)")
          }
        >
          <PlusCircle size={16} />
          {creating ? "Creating..." : "New Chat"}
        </button>
      </div>

      {/* Active chat doc summary */}
      {activeChatId && (readyDocs > 0 || processingDocs > 0) && (
        <div
          className="mx-3 mb-2 px-3 py-2 rounded-lg text-xs flex items-center gap-2"
          style={{
            background: "var(--surface-raised)",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
          }}
        >
          <FileText size={12} />
          {readyDocs > 0 && <span>{readyDocs} doc{readyDocs > 1 ? "s" : ""} ready</span>}
          {processingDocs > 0 && (
            <span className="shimmer rounded px-1" style={{ color: "var(--yellow)" }}>
              {processingDocs} processing
            </span>
          )}
        </div>
      )}

      {/* Chat list */}
      <div className="flex-1 overflow-y-auto px-2">
        {chats.length === 0 ? (
          <div className="text-center py-8" style={{ color: "var(--text-muted)" }}>
            <p className="text-xs">No chats yet</p>
          </div>
        ) : (
          Object.entries(grouped).map(([group, items]) => {
            if (!items.length) return null;
            return (
              <div key={group} className="mb-4">
                <p
                  className="text-xs font-medium px-2 mb-1 uppercase tracking-wider"
                  style={{ color: "var(--text-muted)" }}
                >
                  {group}
                </p>
                <ul className="space-y-0.5">
                  {items.map((chat) => {
                    const isActive = chat.id === activeChatId;
                    const isDeleting = deletingId === chat.id;
                    return (
                      <li key={chat.id}>
                        <button
                          id={`chat-${chat.id}`}
                          onClick={() => selectChat(chat.id)}
                          disabled={isDeleting}
                          className="w-full text-left px-3 py-2 rounded-lg text-sm flex items-center gap-2 group relative transition-all"
                          style={{
                            background: isActive
                              ? "var(--accent-dim)"
                              : "transparent",
                            color: isActive
                              ? "var(--accent)"
                              : "var(--text-secondary)",
                            border: isActive
                              ? "1px solid rgba(79,142,247,0.2)"
                              : "1px solid transparent",
                          }}
                          onMouseEnter={(e) => {
                            if (!isActive)
                              e.currentTarget.style.background =
                                "var(--surface-raised)";
                          }}
                          onMouseLeave={(e) => {
                            if (!isActive)
                              e.currentTarget.style.background = "transparent";
                          }}
                        >
                          <MessageSquare size={14} className="shrink-0" />
                          <span className="truncate flex-1">{chat.title}</span>
                          {/* Delete button */}
                          <span
                            onClick={(e) => handleDelete(e, chat.id)}
                            role="button"
                            className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:text-red-400"
                            style={{ color: "var(--text-muted)" }}
                          >
                            <Trash2 size={12} />
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            );
          })
        )}
      </div>

      {/* Footer */}
      <div
        className="px-4 py-3 text-xs"
        style={{
          borderTop: "1px solid var(--border)",
          color: "var(--text-muted)",
        }}
      >
        Agentic RAG • Hybrid Retrieval
      </div>
    </aside>
  );
}
