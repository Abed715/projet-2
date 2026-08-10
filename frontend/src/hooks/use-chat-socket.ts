"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getWsUrl } from "@/lib/config";

export type ConnectionStatus = "connecting" | "open" | "closed" | "error";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

/** The subset of the browser `WebSocket` API this hook needs, so tests can
 * inject a fake instead of a real socket connecting to a real backend.
 */
export interface SocketLike {
  send(data: string): void;
  close(): void;
  onopen: (() => void) | null;
  onclose: (() => void) | null;
  onerror: (() => void) | null;
  onmessage: ((event: { data: string }) => void) | null;
}

function nextId(): string {
  return crypto.randomUUID();
}

/** Wraps a real browser `WebSocket` behind `SocketLike`, driving the
 * wrapper's own `on*` fields via `addEventListener` instead of assigning
 * to `WebSocket`'s native `on*` properties directly - those carry a
 * `this: WebSocket` DOM event signature that doesn't structurally match
 * `SocketLike`'s simpler callback shape.
 */
function createBrowserSocket(url: string): SocketLike {
  const socket = new WebSocket(url);
  const wrapper: SocketLike = {
    send: (data) => socket.send(data),
    close: () => socket.close(),
    onopen: null,
    onclose: null,
    onerror: null,
    onmessage: null,
  };
  socket.addEventListener("open", () => wrapper.onopen?.());
  socket.addEventListener("close", () => wrapper.onclose?.());
  socket.addEventListener("error", () => wrapper.onerror?.());
  socket.addEventListener("message", (event) => wrapper.onmessage?.({ data: event.data }));
  return wrapper;
}

interface UseChatSocketOptions {
  path?: string;
  createSocket?: (url: string) => SocketLike;
}

export function useChatSocket({
  path = "/ws/chat",
  createSocket = createBrowserSocket,
}: UseChatSocketOptions = {}) {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const socketRef = useRef<SocketLike | null>(null);

  useEffect(() => {
    const socket = createSocket(getWsUrl(path));
    socketRef.current = socket;

    socket.onopen = () => setStatus("open");
    socket.onclose = () => setStatus("closed");
    socket.onerror = () => setStatus("error");
    socket.onmessage = (event) => {
      setMessages((current) => [
        ...current,
        { id: nextId(), role: "assistant", content: event.data },
      ]);
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reconnecting on every `createSocket`/`path` identity change would tear down the connection on each render; both are effectively static for a given page.
  }, []);

  const sendMessage = useCallback(
    (content: string) => {
      const socket = socketRef.current;
      if (socket === null || status !== "open" || content.trim() === "") {
        return;
      }
      socket.send(content);
      setMessages((current) => [...current, { id: nextId(), role: "user", content }]);
    },
    [status],
  );

  return { status, messages, sendMessage };
}
