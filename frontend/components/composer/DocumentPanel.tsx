"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import {
  Upload,
  Link,
  X,
  FileText,
  Globe,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { useChatStore } from "@/store/chatStore";
import { Document } from "@/types";

const STATUS_COLORS: Record<string, string> = {
  UPLOADED: "var(--text-muted)",
  PROCESSING: "var(--yellow)",
  EXTRACTING: "var(--yellow)",
  CHUNKING: "var(--yellow)",
  EMBEDDING: "var(--yellow)",
  INDEXING: "var(--yellow)",
  READY: "var(--green)",
  FAILED: "var(--red)",
};

const STATUS_LABELS: Record<string, string> = {
  UPLOADED: "Queued",
  PROCESSING: "Processing…",
  EXTRACTING: "Extracting…",
  CHUNKING: "Chunking…",
  EMBEDDING: "Embedding…",
  INDEXING: "Indexing…",
  READY: "Ready",
  FAILED: "Failed",
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "var(--text-muted)";
  const label = STATUS_LABELS[status] || status;
  const isProcessing = !["READY", "FAILED", "UPLOADED"].includes(status);

  return (
    <span
      className="flex items-center gap-1 text-xs font-medium"
      style={{ color }}
    >
      {isProcessing && <Loader2 size={10} className="animate-spin" />}
      {status === "READY" && <CheckCircle2 size={10} />}
      {status === "FAILED" && <XCircle size={10} />}
      {label}
    </span>
  );
}

interface DocumentPanelProps {
  onClose: () => void;
}

export function DocumentPanel({ onClose }: DocumentPanelProps) {
  const { documents, uploadDocument, addUrl, refreshDocuments, removeDocument } = useChatStore();
  const [urlInput, setUrlInput] = useState("");
  const [urlMode, setUrlMode] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [addingUrl, setAddingUrl] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Poll for status updates while any doc is processing
  const hasProcessing = documents.some(
    (d) => !["READY", "FAILED"].includes(d.status)
  );
  useEffect(() => {
    if (!hasProcessing) return;
    const interval = setInterval(refreshDocuments, 3000);
    return () => clearInterval(interval);
  }, [hasProcessing, refreshDocuments]);

  const handleFileChange = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      setError(null);
      setUploading(true);
      try {
        for (const file of Array.from(files)) {
          await uploadDocument(file);
        }
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
        onClose();
      } catch (e: any) {
        setError(e.message);
      } finally {
        setUploading(false);
      }
    },
    [uploadDocument]
  );

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    handleFileChange(e.dataTransfer.files);
  };

  const handleAddUrl = async () => {
    if (!urlInput.trim()) return;
    setError(null);
    setAddingUrl(true);
    try {
      await addUrl(urlInput.trim());
      setUrlInput("");
      setUrlMode(false);
      onClose();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAddingUrl(false);
    }
  };

  return (
    <div
      className="rounded-xl p-4 shadow-2xl"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        maxHeight: 320,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => setUrlMode(false)}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-all"
            style={{
              background: !urlMode ? "var(--accent-dim)" : "transparent",
              color: !urlMode ? "var(--accent)" : "var(--text-muted)",
            }}
          >
            <Upload size={12} /> Upload File
          </button>
          <button
            onClick={() => setUrlMode(true)}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-all"
            style={{
              background: urlMode ? "var(--accent-dim)" : "transparent",
              color: urlMode ? "var(--accent)" : "var(--text-muted)",
            }}
          >
            <Globe size={12} /> Add URL
          </button>
        </div>
        <button
          onClick={onClose}
          style={{ color: "var(--text-muted)" }}
          className="hover:text-white transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      {/* Upload area */}
      {!urlMode ? (
        <div
          className="rounded-lg border-2 border-dashed flex flex-col items-center justify-center py-6 gap-2 cursor-pointer transition-all"
          style={{ borderColor: "var(--border)" }}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onMouseEnter={(e) =>
            (e.currentTarget.style.borderColor = "var(--accent)")
          }
          onMouseLeave={(e) =>
            (e.currentTarget.style.borderColor = "var(--border)")
          }
        >
          <Upload size={20} style={{ color: "var(--text-muted)" }} />
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            {uploading ? "Uploading…" : "Click or drag PDF / DOCX"}
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            multiple
            className="hidden"
            onChange={(e) => handleFileChange(e.target.files)}
          />
        </div>
      ) : (
        <div className="flex gap-2">
          <input
            type="url"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            placeholder="https://example.com/article"
            className="flex-1 text-sm px-3 py-2 rounded-lg outline-none"
            style={{
              background: "var(--surface-raised)",
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
            }}
            onKeyDown={(e) => e.key === "Enter" && handleAddUrl()}
          />
          <button
            onClick={handleAddUrl}
            disabled={addingUrl || !urlInput.trim()}
            className="px-3 py-2 rounded-lg text-sm font-medium transition-all"
            style={{
              background: "var(--accent)",
              color: "#fff",
              opacity: addingUrl || !urlInput.trim() ? 0.5 : 1,
            }}
          >
            {addingUrl ? "Adding…" : "Add"}
          </button>
        </div>
      )}

      {error && (
        <p className="text-xs" style={{ color: "var(--red)" }}>
          {error}
        </p>
      )}

      {/* Document list */}
      {documents.length > 0 && (
        <div
          className="overflow-y-auto space-y-1"
          style={{ maxHeight: 120 }}
        >
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center gap-2 px-2 py-1.5 rounded-lg"
              style={{
                background: "var(--surface-raised)",
              }}
            >
              {doc.source_type === "URL" ? (
                <Globe size={14} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
              ) : (
                <FileText size={14} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
              )}
              <span
                className="flex-1 text-xs truncate"
                style={{ color: "var(--text-secondary)" }}
                title={doc.file_name}
              >
                {doc.file_name}
              </span>
              <StatusBadge status={doc.status} />
              <button
                onClick={() => removeDocument(doc.id)}
                className="p-1 rounded hover:bg-black/20 hover:text-red-400 transition-colors ml-1"
                style={{ color: "var(--text-muted)" }}
                title="Delete document"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
