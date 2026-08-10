"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage as ChatMessageType } from "@/hooks/use-chat-socket";
import { ChatMessage } from "@/components/chat/chat-message";

export function ChatTimeline({ messages }: { messages: ChatMessageType[] }) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-zinc-500 dark:text-zinc-500">
        Say something to start the conversation.
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-y-auto pb-4">
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
