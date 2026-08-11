import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Minimal self-contained server bundle for infra/docker/frontend.Dockerfile
  // - see https://nextjs.org/docs/app/guides/self-hosting.
  output: "standalone",
};

export default nextConfig;
