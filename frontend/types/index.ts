export interface Chat {
  id: number;
  title: string;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  chat_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Document {
  id: number;
  chat_id: number;
  file_name: string;
  source_type: "PDF" | "DOCX" | "URL";
  source_url: string | null;
  status:
    | "UPLOADED"
    | "PROCESSING"
    | "EXTRACTING"
    | "CHUNKING"
    | "EMBEDDING"
    | "INDEXING"
    | "READY"
    | "FAILED";
  error_message: string | null;
  created_at: string;
}

export interface Source {
  source: string;
  document_id: number | null;
}

export type StreamEventType = "token" | "sources" | "done" | "error";

export interface StreamEvent {
  type: StreamEventType;
  content?: string;
  sources?: Source[];
  detail?: string;
}
