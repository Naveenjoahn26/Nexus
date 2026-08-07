import { createFileRoute } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Sparkles, User } from "lucide-react";
import { toast } from "sonner";

import { chat as chatApi } from "@/api";

export const Route = createFileRoute("/_authenticated/chat")({
  component: ChatPage,
  head: () => ({
    meta: [
      { title: "Chat · NEXUS EDU" },
      { name: "description", content: "Chat with your RAG-powered AI tutor." },
      { property: "og:title", content: "Chat · NEXUS EDU" },
      { property: "og:description", content: "Chat with your RAG-powered AI tutor." },
    ],
  }),
});

type Msg = { id: string; role: "user" | "assistant"; content: string };

function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const m = useMutation({
    mutationFn: (msg: string) => chatApi.send(msg),
    onSuccess: (r) =>
      setMessages((prev) => [...prev, { id: r.message_id, role: "assistant", content: r.content }]),
    onError: (e: Error) => toast.error(e.message),
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, m.isPending]);

  const send = () => {
    const trimmed = text.trim();
    if (!trimmed || m.isPending) return;
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: trimmed }]);
    m.mutate(trimmed);
    setText("");
  };

  return (
    <div className="flex h-[calc(100vh-3rem)] flex-col gap-4">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Chat</h1>
        <p className="mt-1 text-muted-foreground">
          Conversation is grounded in your current workspace's documents.
        </p>
      </header>

      <div ref={scrollRef} className="glass-strong flex-1 overflow-y-auto rounded-2xl p-6">
        {messages.length === 0 && !m.isPending && (
          <div className="grid h-full place-items-center text-center text-muted-foreground">
            <div>
              <Sparkles className="mx-auto h-8 w-8 text-primary" />
              <p className="mt-3 text-sm">Ask NEXUS about your uploaded material.</p>
            </div>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`mb-4 flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
            >
              {msg.role === "assistant" && (
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-primary to-secondary">
                  <Sparkles className="h-4 w-4 text-primary-foreground" />
                </div>
              )}
              <div
                className={`max-w-[75%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-primary/90 text-primary-foreground"
                    : "glass border border-white/5"
                }`}
              >
                {msg.content}
              </div>
              {msg.role === "user" && (
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white/10">
                  <User className="h-4 w-4" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {m.isPending && (
          <div className="mb-4 flex gap-3">
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-primary to-secondary">
              <Sparkles className="h-4 w-4 text-primary-foreground" />
            </div>
            <div className="glass rounded-2xl px-4 py-3 text-sm">
              <span className="inline-flex gap-1">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:0.15s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-primary [animation-delay:0.3s]" />
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="glass-strong flex items-end gap-2 rounded-2xl p-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder="Ask anything about your course material…"
          rows={1}
          className="flex-1 resize-none bg-transparent px-3 py-2 text-sm outline-none placeholder:text-muted-foreground"
        />
        <button
          onClick={send}
          disabled={!text.trim() || m.isPending}
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary to-secondary px-4 py-2.5 text-sm font-semibold text-primary-foreground glow-cyan disabled:opacity-50"
        >
          {m.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}
