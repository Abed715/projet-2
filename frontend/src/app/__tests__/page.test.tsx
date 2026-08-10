import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import OverviewPage from "@/app/page";

describe("OverviewPage", () => {
  test("renders the dashboard heading", () => {
    render(<OverviewPage />);

    expect(screen.getByRole("heading", { level: 1, name: "JARVIS Dashboard" })).toBeDefined();
  });

  test("links the live Chat module but not the coming-soon ones", () => {
    render(<OverviewPage />);

    expect(screen.getByRole("link", { name: "Chat" })).toHaveAttribute("href", "/chat");
    expect(screen.queryByRole("link", { name: "Memory" })).toBeNull();
    expect(screen.getByText("Memory")).toBeDefined();
  });
});
