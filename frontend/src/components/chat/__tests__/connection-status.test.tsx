import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { ConnectionStatusBadge } from "@/components/chat/connection-status";

describe("ConnectionStatusBadge", () => {
  test.each([
    ["connecting", "Connecting…"],
    ["open", "Connected"],
    ["closed", "Disconnected"],
    ["error", "Connection error"],
  ] as const)("renders the label for status %s", (status, label) => {
    render(<ConnectionStatusBadge status={status} />);

    expect(screen.getByText(label)).toBeDefined();
  });
});
