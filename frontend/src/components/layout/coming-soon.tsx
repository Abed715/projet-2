interface ComingSoonProps {
  title: string;
  explanation: string;
}

export function ComingSoon({ title, explanation }: ComingSoonProps) {
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-3">
      <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">{title}</h1>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">{explanation}</p>
      <p className="text-sm text-zinc-500 dark:text-zinc-500">
        See{" "}
        <code className="rounded bg-zinc-100 px-1 py-0.5 dark:bg-zinc-800">ROADMAP.md</code> for
        what&apos;s built vs. planned in the backend, and the module&apos;s{" "}
        <code className="rounded bg-zinc-100 px-1 py-0.5 dark:bg-zinc-800">README.md</code> for
        design notes.
      </p>
    </div>
  );
}
