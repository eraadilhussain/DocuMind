import { Sidebar } from "@/components/sidebar/Sidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";

export default function Home() {
  return (
    <>
      <Sidebar />
      <main
        className="flex-1 flex flex-col h-full overflow-hidden"
        style={{ background: "var(--background)" }}
      >
        <ChatWindow />
      </main>
    </>
  );
}
