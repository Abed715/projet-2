import { app, BrowserWindow, globalShortcut, Menu, nativeImage, Tray } from "electron";
import path from "node:path";
import { resolveAppUrl } from "./resolve-app-url";

const TOGGLE_WINDOW_SHORTCUT = "CommandOrControl+Shift+J";
const ICON_PATH = path.join(__dirname, "..", "assets", "icon.png");

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    title: "JARVIS",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  const url = resolveAppUrl(process.env);
  void mainWindow.loadURL(url);

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function createTray(): void {
  const icon = nativeImage.createFromPath(ICON_PATH);
  tray = new Tray(icon.isEmpty() ? nativeImage.createEmpty() : icon);
  tray.setToolTip("JARVIS");
  tray.setContextMenu(
    Menu.buildFromTemplate([
      {
        label: "Show JARVIS",
        click: () => {
          mainWindow?.show();
          mainWindow?.focus();
        },
      },
      { type: "separator" },
      { label: "Quit", click: () => app.quit() },
    ]),
  );
  tray.on("click", () => {
    mainWindow?.show();
    mainWindow?.focus();
  });
}

function registerGlobalShortcut(): void {
  // Toggles window visibility only - this is NOT the voice wake word.
  // Wiring a hotkey to actual wake-word listening needs a continuous
  // microphone-capture loop that doesn't exist on any client yet; see
  // voice/README.md and desktop/README.md for why that's deferred.
  globalShortcut.register(TOGGLE_WINDOW_SHORTCUT, () => {
    if (mainWindow === null) {
      return;
    }
    if (mainWindow.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

app.whenReady().then(() => {
  createWindow();
  createTray();
  registerGlobalShortcut();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
});
