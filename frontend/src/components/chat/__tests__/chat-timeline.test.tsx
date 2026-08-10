import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { ChatTimeline } from "@/components/chat/chat-timeline";

describe("ChatTimeline", () => {
  test("shows an empty-state prompt with no messages", () => {
    render(<ChatTimeline messages={[]} />);

    expect(screen.getByText("Say something to start the conversation.")).toBeDefined();
  });

  test("renders each message's content", () => {
    render(
      <ChatTimeline
        messages={[
          { id: "1", role: "user", content: "hi" },
          { id: "2", role: "assistant", content: "hello there" },
        ]}
      />,
    );

    expect(screen.getByText("hi")).toBeDefined();
    expect(screen.getByText("hello there")).toBeDefined();
  });
});
