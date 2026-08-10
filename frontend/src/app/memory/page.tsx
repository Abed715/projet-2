import { ComingSoon } from "@/components/layout/coming-soon";

export default function MemoryPage() {
  return (
    <ComingSoon
      title="Memory"
      explanation="Short-term (Redis), episodic (Postgres), and semantic (ChromaDB) memory are all implemented in the backend's jarvis.memory module, but jarvis.api has no REST endpoints to browse them from a dashboard yet."
    />
  );
}
