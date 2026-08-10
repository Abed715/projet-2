import { describe, expect, test } from "vitest";
import { resolveAppUrl } from "../resolve-app-url";

describe("resolveAppUrl", () => {
  test("defaults to the local dev server when nothing is configured", () => {
    expect(resolveAppUrl({})).toBe("http://localhost:3000");
  });

  test("prefers an explicit JARVIS_FRONTEND_URL over the default", () => {
    expect(resolveAppUrl({ JARVIS_FRONTEND_URL: "http://localhost:4000" })).toBe(
      "http://localhost:4000",
    );
  });

  test("prefers an explicit JARVIS_FRONTEND_URL even in production", () => {
    expect(
      resolveAppUrl({ JARVIS_FRONTEND_URL: "https://dashboard.example.com", NODE_ENV: "production" }),
    ).toBe("https://dashboard.example.com");
  });

  test("refuses to fall back to localhost in production with no URL configured", () => {
    expect(() => resolveAppUrl({ NODE_ENV: "production" })).toThrow(
      /JARVIS_FRONTEND_URL must be set/,
    );
  });
});
