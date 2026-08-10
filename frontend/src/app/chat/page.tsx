"use client";

import { useChatSocket } from "@/hooks/use-chat-socket";
import { ChatTimeline } from "@/components/chat/chat-timeline";
import { ChatInput } from "@/components/chat/chat-input";
import { ConnectionStatusBadge } from "@/components/chat/connection-status";

export default function ChatPage() {
  const { status, messages, sendMessage } = useChatSocket();

  return (
    <div className="mx-auto flex h-full max-w-2xl flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">Chat</h1>
        <ConnectionStatusBadge status={status} />
      </div>
      <ChatTimeline messages={messages} />
      <ChatInput disabled={status !== "open"} onSend={sendMessage} />
    </div>
  );
}
