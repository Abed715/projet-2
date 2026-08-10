/** Decides which URL the main window loads. Pulled out of `main.ts` as a
 * pure function so it's unit-testable without mocking Electron itself -
 * `main.ts`'s own app-lifecycle wiring is left to manual/E2E verification
 * (see desktop/README.md).
 */

const DEFAULT_DEV_URL = "http://localhost:3000";

export interface AppUrlEnv {
  JARVIS_FRONTEND_URL?: string;
  NODE_ENV?: string;
}

export function resolveAppUrl(env: AppUrlEnv): string {
  if (env.JARVIS_FRONTEND_URL) {
    return env.JARVIS_FRONTEND_URL;
  }
  if (env.NODE_ENV === "production") {
    throw new Error(
      "JARVIS_FRONTEND_URL must be set in production - there is no bundled/static " +
        "frontend build packaged into the app yet, see desktop/README.md",
    );
  }
  return DEFAULT_DEV_URL;
}
