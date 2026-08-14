"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "react-toastify";
import MessageContent from "./components/MessageContent";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

type Message = { sender: "ai" | "human"; text: string };
type ChatSession = { checkpoint_id: string; latest_message: string };

export default function Home() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  async function loadSessions() {
    try {
      const res = await fetch(`${API_URL}/chat-history`);
      if (res.ok) setSessions(await res.json());
    } catch {
      toast.error("Could not load chat history.");
    }
  }

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages]);

  async function selectSession(session: ChatSession) {
    setActiveThreadId(session.checkpoint_id);
    try {
      const res = await fetch(`${API_URL}/chat/${session.checkpoint_id}/messages`);
      if (!res.ok) throw new Error(await res.text());
      setMessages(await res.json());
    } catch {
      toast.error("Could not load this conversation.");
      setMessages([]);
    }
  }

  function startNewChat() {
    setActiveThreadId(null);
    setMessages([]);
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;

    setMessages((prev) => [...prev, { sender: "human", text }]);
    setInput("");
    setSending(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, thread_id: activeThreadId }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data: { thread_id: string; message: string } = await res.json();

      setActiveThreadId(data.thread_id);
      setMessages((prev) => [...prev, { sender: "ai", text: data.message }]);
      loadSessions();
    } catch {
      toast.error("Something went wrong reaching the agent.");
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="grid grid-cols-4 h-screen">
      <div className="col-span-1 h-screen border-r border-dashed border-dark1 p-6 flex flex-col gap-4">
        <button
          onClick={startNewChat}
          className="rounded-xl bg-dark1 text-background px-4 py-2 font-medium hover:bg-dark2 transition-colors"
        >
          New chat
        </button>
        <div className="flex-1 overflow-y-auto flex flex-col gap-2">
          {sessions.map((session) => (
            <button
              key={session.checkpoint_id}
              onClick={() => selectSession(session)}
              className={`text-left px-3 py-2 text-sm ${
                activeThreadId === session.checkpoint_id
                  ? "bg-accent text-dark2"
                  : "text-dark2 hover:bg-accent/40"
              }`}
            >
              <p className="truncate">{session.latest_message}</p>
            </button>
          ))}
        </div>
      </div>
      <div className="col-span-3 relative h-screen">
        <div
          ref={listRef}
          className="h-full overflow-y-auto flex flex-col gap-3 p-6 pb-28"
        >
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`max-w-[70%] rounded-2xl px-4 py-2 text-base ${
                msg.sender === "ai"
                  ? "self-start bg-accent text-dark2"
                  : "self-end bg-dark1 text-background"
              }`}
            >
              <MessageContent text={msg.text} />
            </div>
          ))}
        </div>

        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-[90%] max-w-xl flex items-center gap-2 rounded-2xl border border-dark1 bg-background px-3 py-2 shadow-lg">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type your message..."
            disabled={sending}
            className="flex-1 bg-transparent text-dark2 outline-none px-2"
          />
          <button
            onClick={handleSend}
            disabled={sending}
            className="rounded-xl bg-dark1 text-background px-4 py-2 font-medium hover:bg-dark2 transition-colors disabled:opacity-50"
          >
            Enter
          </button>
        </div>
      </div>
    </main>
  );
}
