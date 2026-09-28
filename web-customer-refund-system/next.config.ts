import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a self-contained .next/standalone build with only the
  // dependencies actually used at runtime traced in - keeps the Docker
  // image from having to ship the full node_modules tree.
  output: "standalone",
};

export default nextConfig;
