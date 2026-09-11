import { Chat, Message, Document, StreamEvent, Source } from "@/types";

let BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
if (BASE_URL.startsWith("http") && !BASE_URL.endsWith("/api/v1")) {
  BASE_URL = `${BASE_URL.replace(/\/$/, "")}/api/v1`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── Chats ────────────────────────────────────────────────────────────────────

export const getChats = (): Promise<Chat[]> => request("/chats/");

export const createChat = (title?: string): Promise<Chat> =>
  request("/chats/", {
    method: "POST",
    body: JSON.stringify({ title: title || "New Chat" }),
  });

export const deleteChat = (id: number): Promise<void> =>
  request(`/chats/${id}`, { method: "DELETE" });

// ── Messages ─────────────────────────────────────────────────────────────────

export const getMessages = (chatId: number): Promise<Message[]> =>
  request(`/chats/${chatId}/messages`);

// ── Documents ────────────────────────────────────────────────────────────────

export const getDocuments = (chatId: number): Promise<Document[]> =>
  request(`/chats/${chatId}/documents`);

export const uploadDocument = async (
  chatId: number,
  file: File
): Promise<Document> => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/chats/${chatId}/documents`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

export const addUrl = (chatId: number, url: string): Promise<Document> =>
  request(`/chats/${chatId}/urls`, {
    method: "POST",
    body: JSON.stringify({ url }),
  });

export const deleteDocument = (chatId: number, documentId: number): Promise<void> =>
  request(`/chats/${chatId}/documents/${documentId}`, { method: "DELETE" });

// ── Streaming ────────────────────────────────────────────────────────────────

export async function streamChat(
  chatId: number,
  message: string,
  onToken: (token: string) => void,
  onSources: (sources: Source[]) => void,
  onDone: () => void,
  onError: (detail: string) => void
): Promise<void> {
  const res = await fetch(`${BASE_URL}/chats/${chatId}/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok || !res.body) {
    onError(`HTTP ${res.status}`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (!raw) continue;
      try {
        const event: StreamEvent = JSON.parse(raw);
        if (event.type === "token" && event.content) onToken(event.content);
        else if (event.type === "sources" && event.sources) onSources(event.sources);
        else if (event.type === "done") onDone();
        else if (event.type === "error") onError(event.detail || "Unknown error");
      } catch {
        // skip malformed lines
      }
    }
  }
}
