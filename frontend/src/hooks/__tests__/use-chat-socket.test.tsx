import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { useChatSocket, type SocketLike } from "@/hooks/use-chat-socket";

class FakeSocket implements SocketLike {
  sent: string[] = [];
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  closed = false;

  send(data: string): void {
    this.sent.push(data);
  }

  close(): void {
    this.closed = true;
  }

  simulateOpen(): void {
    this.onopen?.();
  }

  simulateMessage(data: string): void {
    this.onmessage?.({ data });
  }

  simulateError(): void {
    this.onerror?.();
  }
}

function renderChatSocket() {
  const sockets: FakeSocket[] = [];
  const { result } = renderHook(() =>
    useChatSocket({
      createSocket: () => {
        const socket = new FakeSocket();
        sockets.push(socket);
        return socket;
      },
    }),
  );
  return { result, socket: () => sockets[0] };
}

describe("useChatSocket", () => {
  test("starts in the connecting state with no messages", () => {
    const { result } = renderChatSocket();

    expect(result.current.status).toBe("connecting");
    expect(result.current.messages).toEqual([]);
  });

  test("transitions to open when the socket opens", async () => {
    const { result, socket } = renderChatSocket();

    act(() => socket().simulateOpen());

    await waitFor(() => expect(result.current.status).toBe("open"));
  });

  test("appends an assistant message on incoming data", async () => {
    const { result, socket } = renderChatSocket();
    act(() => socket().simulateOpen());
    await waitFor(() => expect(result.current.status).toBe("open"));

    act(() => socket().simulateMessage("hello from jarvis"));

    await waitFor(() => expect(result.current.messages).toHaveLength(1));
    expect(result.current.messages[0]).toMatchObject({
      role: "assistant",
      content: "hello from jarvis",
    });
  });

  test("sendMessage appends a user message and forwards it to the socket", async () => {
    const { result, socket } = renderChatSocket();
    act(() => socket().simulateOpen());
    await waitFor(() => expect(result.current.status).toBe("open"));

    act(() => result.current.sendMessage("hi there"));

    await waitFor(() => expect(result.current.messages).toHaveLength(1));
    expect(result.current.messages[0]).toMatchObject({ role: "user", content: "hi there" });
    expect(socket().sent).toEqual(["hi there"]);
  });

  test("sendMessage is a no-op while not connected", () => {
    const { result, socket } = renderChatSocket();

    act(() => result.current.sendMessage("too early"));

    expect(result.current.messages).toEqual([]);
    expect(socket().sent).toEqual([]);
  });

  test("sendMessage ignores blank input", async () => {
    const { result, socket } = renderChatSocket();
    act(() => socket().simulateOpen());
    await waitFor(() => expect(result.current.status).toBe("open"));

    act(() => result.current.sendMessage("   "));

    expect(result.current.messages).toEqual([]);
    expect(socket().sent).toEqual([]);
  });

  test("transitions to error state on socket error", async () => {
    const { result, socket } = renderChatSocket();

    act(() => socket().simulateError());

    await waitFor(() => expect(result.current.status).toBe("error"));
  });
});
