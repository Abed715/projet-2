import { ComingSoon } from "@/components/layout/coming-soon";

export default function TasksPage() {
  return (
    <ComingSoon
      title="Tasks"
      explanation="The Task Engine (Redis Streams job queue, workers, interval scheduler, retry/pause/resume/cancel) is implemented in the backend's jarvis.tasks module, but jarvis.api has no REST endpoints to submit or inspect tasks from a dashboard yet."
    />
  );
}
