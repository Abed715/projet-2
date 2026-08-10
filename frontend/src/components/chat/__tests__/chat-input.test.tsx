import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, test, vi } from "vitest";
import { ChatInput } from "@/components/chat/chat-input";

describe("ChatInput", () => {
  test("calls onSend with the typed message and clears the input", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput disabled={false} onSend={onSend} />);

    const input = screen.getByLabelText("Message");
    await user.type(input, "hello jarvis");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(onSend).toHaveBeenCalledWith("hello jarvis");
    expect(input).toHaveValue("");
  });

  test("does not call onSend for blank input", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput disabled={false} onSend={onSend} />);

    await user.type(screen.getByLabelText("Message"), "   ");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(onSend).not.toHaveBeenCalled();
  });

  test("disables the input and button when disabled", () => {
    render(<ChatInput disabled={true} onSend={vi.fn()} />);

    expect(screen.getByLabelText("Message")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
  });
});
