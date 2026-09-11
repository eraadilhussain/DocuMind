import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocuMind — Agentic RAG Chatbot",
  description:
    "Upload documents and chat with an AI that retrieves, synthesises, and cites your content.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="antialiased h-screen flex overflow-hidden">
        {children}
      </body>
    </html>
  );
}
