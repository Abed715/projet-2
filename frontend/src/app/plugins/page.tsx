import { ComingSoon } from "@/components/layout/coming-soon";

export default function PluginsPage() {
  return (
    <ComingSoon
      title="Plugins"
      explanation="The plugin manifest/loader and a working GitHub reference plugin are implemented in the backend's jarvis.plugins module, but jarvis.api has no REST endpoints to list or manage plugins from a dashboard yet."
    />
  );
}
