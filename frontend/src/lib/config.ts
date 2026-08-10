const DEFAULT_API_BASE_URL = "http://localhost:8000";

/** The backend's HTTP base URL. Frontend talks to the backend only through
 * its public REST/WebSocket API — see frontend/README.md.
 */
export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

/** Builds a `ws(s)://` URL for a backend WebSocket route (e.g. `/ws/chat`)
 * from the same base URL `getApiBaseUrl()` returns, so only one env var
 * needs configuring.
 */
export function getWsUrl(path: string): string {
  const httpUrl = new URL(path, getApiBaseUrl());
  httpUrl.protocol = httpUrl.protocol === "https:" ? "wss:" : "ws:";
  return httpUrl.toString();
}
