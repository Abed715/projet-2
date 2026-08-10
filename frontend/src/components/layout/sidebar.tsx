"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/theme/theme-toggle";

interface NavItem {
  href: string;
  label: string;
  comingSoon?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Overview" },
  { href: "/chat", label: "Chat" },
  { href: "/memory", label: "Memory", comingSoon: true },
  { href: "/tasks", label: "Tasks", comingSoon: true },
  { href: "/plugins", label: "Plugins", comingSoon: true },
  { href: "/system", label: "System", comingSoon: true },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="mb-6 px-2">
        <span className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">JARVIS</span>
      </div>
      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-zinc-900 text-zinc-50 dark:bg-zinc-50 dark:text-zinc-900"
                  : "text-zinc-700 hover:bg-zinc-200 dark:text-zinc-300 dark:hover:bg-zinc-800"
              }`}
            >
              <span>{item.label}</span>
              {item.comingSoon && (
                <span className="rounded-full bg-zinc-200 px-2 py-0.5 text-[10px] font-normal tracking-wide text-zinc-600 uppercase dark:bg-zinc-800 dark:text-zinc-400">
                  Soon
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="mt-4">
        <ThemeToggle />
      </div>
    </aside>
  );
}
