import { ComingSoon } from "@/components/layout/coming-soon";

export default function SystemPage() {
  return (
    <ComingSoon
      title="System"
      explanation="jarvis.automation.ProcessService can list/open/close OS processes, but there's no system-metrics (CPU/RAM/GPU/network) endpoint in jarvis.api yet, so there's nothing for this page to show."
    />
  );
}
