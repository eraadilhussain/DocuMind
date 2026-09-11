"use client";

import { create } from "zustand";
import {
  Chat,
  Message,
  Document as DocType,
  Source,
} from "@/types";
import {
  getChats,
  createChat as apiCreateChat,
  deleteChat as apiDeleteChat,
  getMessages,
  getDocuments,
  uploadDocument as apiUploadDocument,
  addUrl as apiAddUrl,
  deleteDocument as apiDeleteDocument,
  streamChat,
} from "@/lib/api";

interface ChatStore {
  // ── State ──────────────────────────────────────────────────────────────────
  chats: Chat[];
  activeChatId: number | null;
  messages: Message[];
  documents: DocType[];
  isStreaming: boolean;
  streamingContent: string;
  streamingSources: Source[];
  error: string | null;
  isSidebarOpen: boolean;

  // ── Chat actions ───────────────────────────────────────────────────────────
  toggleSidebar: () => void;
  loadChats: () => Promise<void>;
  createChat: (title?: string) => Promise<Chat>;
  selectChat: (id: number) => Promise<void>;
  deleteChat: (id: number) => Promise<void>;

  // ── Message actions ────────────────────────────────────────────────────────
  loadMessages: (chatId: number) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;

  // ── Document actions ───────────────────────────────────────────────────────
  loadDocuments: (chatId: number) => Promise<void>;
  uploadDocument: (file: File) => Promise<void>;
  addUrl: (url: string) => Promise<void>;
  removeDocument: (documentId: number) => Promise<void>;
  refreshDocuments: () => Promise<void>;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  chats: [],
  activeChatId: null,
  messages: [],
  documents: [],
  isStreaming: false,
  streamingContent: "",
  streamingSources: [],
  error: null,
  isSidebarOpen: true,

  // ── Chat actions ───────────────────────────────────────────────────────────

  toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),

  loadChats: async () => {
    try {
      const chats = await getChats();
      set({ chats });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  createChat: async (title?: string) => {
    const chat = await apiCreateChat(title);
    set((s) => ({ chats: [chat, ...s.chats] }));
    await get().selectChat(chat.id);
    return chat;
  },

  selectChat: async (id: number) => {
    set({ activeChatId: id, messages: [], documents: [], streamingContent: "", streamingSources: [] });
    await Promise.all([get().loadMessages(id), get().loadDocuments(id)]);
  },

  deleteChat: async (id: number) => {
    await apiDeleteChat(id);
    set((s) => {
      const chats = s.chats.filter((c) => c.id !== id);
      const activeChatId = s.activeChatId === id ? (chats[0]?.id ?? null) : s.activeChatId;
      return { chats, activeChatId };
    });
    const newActive = get().activeChatId;
    if (newActive) {
      await get().selectChat(newActive);
    } else {
      set({ messages: [], documents: [] });
    }
  },

  // ── Message actions ────────────────────────────────────────────────────────

  loadMessages: async (chatId: number) => {
    try {
      const messages = await getMessages(chatId);
      set({ messages });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  sendMessage: async (content: string) => {
    const { activeChatId } = get();
    if (!activeChatId || !content.trim()) return;

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: Date.now(),
      chat_id: activeChatId,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    set((s) => ({
      messages: [...s.messages, tempUserMsg],
      isStreaming: true,
      streamingContent: "",
      streamingSources: [],
      error: null,
    }));

    await streamChat(
      activeChatId,
      content,
      (token) => set((s) => ({ streamingContent: s.streamingContent + token })),
      (sources) => set({ streamingSources: sources }),
      async () => {
        // On done: reload messages from DB and clear streaming state
        const messages = await getMessages(activeChatId);
        set({ messages, isStreaming: false, streamingContent: "", streamingSources: [] });
        // Update chat list (title may have changed)
        get().loadChats();
      },
      (detail) => {
        set((s) => ({
          isStreaming: false,
          streamingContent: "",
          messages: [
            ...s.messages,
            {
              id: Date.now() + 1,
              chat_id: activeChatId,
              role: "assistant" as const,
              content: `⚠️ Error: ${detail}`,
              created_at: new Date().toISOString(),
            },
          ],
          error: detail,
        }));
      }
    );
  },

  // ── Document actions ───────────────────────────────────────────────────────

  loadDocuments: async (chatId: number) => {
    try {
      const documents = await getDocuments(chatId);
      set({ documents });
    } catch (e: any) {
      set({ error: e.message });
    }
  },

  uploadDocument: async (file: File) => {
    const { activeChatId } = get();
    if (!activeChatId) return;
    await apiUploadDocument(activeChatId, file);
    await get().loadDocuments(activeChatId);
  },

  addUrl: async (url: string) => {
    const { activeChatId } = get();
    if (!activeChatId) return;
    await apiAddUrl(activeChatId, url);
    await get().loadDocuments(activeChatId);
  },

  removeDocument: async (documentId: number) => {
    const { activeChatId, documents } = get();
    if (!activeChatId) return;
    
    // Optimistically update UI
    set({ documents: documents.filter(d => d.id !== documentId) });
    
    try {
      await apiDeleteDocument(activeChatId, documentId);
    } catch (e: any) {
      set({ error: e.message });
      // Revert on error
      await get().loadDocuments(activeChatId);
    }
  },

  refreshDocuments: async () => {
    const { activeChatId } = get();
    if (activeChatId) await get().loadDocuments(activeChatId);
  },
}));
