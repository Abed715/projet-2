# jarvis.automation

**Status:** implemented (Phase 4). Depends on `jarvis.core`, `jarvis.security`
(risk levels only — automation actions are not workspace-confined), and
`jarvis.brain` (to register tools into `ToolRegistry`).

## Public interface

```python
from jarvis.automation import (
    ProcessService, ProcessInfo,
    ClipboardService, ClipboardBackend, PyperclipClipboardBackend,
    NotificationService, NotificationBackend, DesktopNotificationBackend,
    InputService, InputBackend, PyAutoGuiInputBackend,
    register_automation_tools,
)
```

- **`ProcessService`** — `open_application(command)`, `close_application(pid,
  force=False)`, `list_processes()`. Built on `psutil`/`subprocess`, which
  are headless-safe (no display required), so this talks to them directly
  rather than through a backend Protocol.
- **`ClipboardService(backend)`** — `read()`/`write(text)` over a
  `ClipboardBackend` Protocol. `PyperclipClipboardBackend` is the real
  implementation.
- **`NotificationService(backend)`** — `send(title=..., message=...)` over a
  `NotificationBackend` Protocol. `DesktopNotificationBackend` shells out to
  `notify-send` (Linux/libnotify only for now).
- **`InputService(backend)`** — `move_mouse(x, y)`, `click()`,
  `type_text(text)`, `press_key(key)` over an `InputBackend` Protocol.
  `PyAutoGuiInputBackend` is the real implementation.
- **`register_automation_tools(registry, *, process, clipboard,
  notifications, input_service)`** — registers `list_processes` (`SAFE`),
  `open_application`/`close_application` (`DANGEROUS`), `clipboard_read`/
  `clipboard_write` (`SENSITIVE`), `send_notification` (`SAFE`),
  `mouse_move` (`SENSITIVE`), `mouse_click`/`type_text`/`press_key`
  (`DANGEROUS`).

## Design notes: headless environments

Three of these four services depend on a display, clipboard mechanism, or
notification daemon that may not exist — e.g. in CI or a server deployment.
Each was empirically verified against this constraint before being built:

- **`pyautogui`** raises `KeyError('DISPLAY')` at *import* time (not just
  construction) when no `$DISPLAY` is set — one of its submodules
  eagerly opens an X11 `Display` handle. `PyAutoGuiInputBackend.__init__`
  therefore imports it lazily, inside the constructor, and translates any
  exception into `ConfigurationError`. It is never imported at module scope.
- **`pyperclip`** is safe to import at module scope, but `copy()`/`paste()`
  raise `PyperclipException` when no clipboard mechanism (xclip, xsel,
  wl-clipboard) is installed. `PyperclipClipboardBackend` wraps both calls.
- **`notify-send`** may simply not be installed. `DesktopNotificationBackend`
  checks `shutil.which("notify-send")` up front and raises
  `ConfigurationError` rather than letting `subprocess.run` fail opaquely.
- **`psutil`/`subprocess`** (process management) need no display and work
  in any environment, so `ProcessService` has no backend Protocol — there is
  nothing to swap for headless safety.

Every backend is still swappable via its Protocol for testing: unit tests
inject fakes, never the real OS-touching implementations.

## Known limitations

- `open_application` does not retain a reference to the spawned
  `subprocess.Popen` object, so nothing calls `.wait()` on it. Short-lived
  child processes may become zombies until this process exits. Acceptable
  for this phase; revisit if/when the task engine (Phase 6) needs to track
  child processes.
- `DesktopNotificationBackend` is Linux/libnotify only. macOS
  (`osascript`/`terminal-notifier`) and Windows (`win10toast`/WinRT) backends
  are deferred until there's a target platform to test against.
- No macOS/Windows clipboard or input backends beyond what `pyperclip`/
  `pyautogui` already provide cross-platform — those two libraries handle
  the OS differences internally; only the headless-Linux failure mode
  required first-class handling here.
