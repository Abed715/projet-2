import type { ConnectionStatus } from "@/hooks/use-chat-socket";

const LABELS: Record<ConnectionStatus, string> = {
  connecting: "Connecting…",
  open: "Connected",
  closed: "Disconnected",
  error: "Connection error",
};

const DOT_COLORS: Record<ConnectionStatus, string> = {
  connecting: "bg-amber-400",
  open: "bg-emerald-500",
  closed: "bg-zinc-400",
  error: "bg-red-500",
};

export function ConnectionStatusBadge({ status }: { status: ConnectionStatus }) {
  return (
    <span className="inline-flex items-center gap-2 text-xs font-medium text-zinc-600 dark:text-zinc-400">
      <span className={`h-2 w-2 rounded-full ${DOT_COLORS[status]}`} aria-hidden="true" />
      {LABELS[status]}
    </span>
  );
}
