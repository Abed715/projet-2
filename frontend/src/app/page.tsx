import Link from "next/link";

interface ModuleStatus {
  name: string;
  href: string;
  status: "live" | "coming-soon";
  description: string;
}

const MODULES: ModuleStatus[] = [
  {
    name: "Chat",
    href: "/chat",
    status: "live",
    description: "Talk to the Coordinator agent over WS /ws/chat.",
  },
  {
    name: "Memory",
    href: "/memory",
    status: "coming-soon",
    description:
      "Short-term, episodic, and semantic memory are implemented in the backend, but jarvis.api has no REST surface to browse them from yet.",
  },
  {
    name: "Tasks",
    href: "/tasks",
    status: "coming-soon",
    description:
      "The Task Engine (queue, workers, scheduler) is implemented in the backend, but jarvis.api has no REST surface to submit or inspect tasks from yet.",
  },
  {
    name: "Plugins",
    href: "/plugins",
    status: "coming-soon",
    description:
      "The plugin loader and a reference GitHub plugin are implemented, but jarvis.api has no REST surface to list or manage them from yet.",
  },
  {
    name: "System",
    href: "/system",
    status: "coming-soon",
    description:
      "CPU/RAM/GPU/network status isn't exposed by jarvis.api yet — automation.ProcessService can list processes, but there's no system-metrics endpoint.",
  },
];

export default function OverviewPage() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
          JARVIS Dashboard
        </h1>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Just A Rather Very Intelligent System — this dashboard talks to the
          backend only through its public REST/WebSocket API, never by
          importing backend code.
        </p>
      </div>
      <ul className="flex flex-col gap-3">
        {MODULES.map((module) => (
          <li
            key={module.name}
            className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800"
          >
            <div className="flex items-center justify-between">
              <h2 className="font-medium text-zinc-900 dark:text-zinc-50">
                {module.status === "live" ? (
                  <Link href={module.href} className="hover:underline">
                    {module.name}
                  </Link>
                ) : (
                  module.name
                )}
              </h2>
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-medium tracking-wide uppercase ${
                  module.status === "live"
                    ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
                    : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                }`}
              >
                {module.status === "live" ? "Live" : "Coming soon"}
              </span>
            </div>
            <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
              {module.description}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
