/** Preload script: the only bridge between the renderer (the Next.js
 * dashboard) and Node/Electron APIs. `contextIsolation` is on and
 * `nodeIntegration` is off (see main.ts), so this is deliberately the
 * *only* place Node globals are reachable from the loaded page - and even
 * here, only a small, explicit surface is exposed via `contextBridge`,
 * never `require`/`process` themselves.
 */

import { contextBridge } from "electron";

const jarvisBridge = {
  platform: process.platform,
  versions: {
    electron: process.versions.electron,
    chrome: process.versions.chrome,
  },
};

export type JarvisBridge = typeof jarvisBridge;

contextBridge.exposeInMainWorld("jarvis", jarvisBridge);
