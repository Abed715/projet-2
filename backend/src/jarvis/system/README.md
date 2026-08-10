# jarvis.system

**Status:** implemented (Phase 3). Depends on `jarvis.core`,
`jarvis.security` (for `SandboxExecutor`), and `jarvis.brain` (to register
tools into `ToolRegistry`).

## Public interface

```python
from jarvis.system import FilesystemService, ShellService, register_system_tools
```

- **`FilesystemService`** — read/write/list/move/delete confined to a
  workspace directory. Every path is resolved and checked to remain inside
  the workspace root before touching disk (catches `..` traversal and
  absolute-path inputs alike — see the class docstring for why the naive
  `workspace / "/etc/passwd"` join is still safe here).
- **`ShellService`** — thin wrapper over `security.SandboxExecutor`: runs a
  command as argv (never a shell string), confined to the workspace, with
  a timeout.
- **`register_system_tools(registry, *, filesystem, shell)`** — registers
  `read_file`/`list_dir` (`SAFE`), `write_file`/`move_file` (`SENSITIVE`),
  and `delete_file`/`run_shell_command` (`DANGEROUS`, requires confirmation
  for non-owner-granted sessions) into a `brain.ToolRegistry`.

## Design notes

- Risk tagging follows ARCHITECTURE.md §8: read-only and additive actions
  are `SAFE`/`SENSITIVE`; anything destructive or capable of running
  arbitrary code is `DANGEROUS`.
- `run_shell_command` takes a JSON array of argv strings, never a single
  command string — this is the same "no shell interpolation" guarantee
  `SandboxExecutor` provides, surfaced all the way to the tool schema so
  the model (and anyone reading the schema) can see there's no shell to
  inject into.
- No process management (open/close applications) yet — ARCHITECTURE.md's
  "computer control" list also includes that, but it needs `automation`'s
  OS-level primitives (Phase 4) more than it needs `system`'s.
