import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The repo root also has a package.json (dev orchestration only, see
  // /package.json) with its own lockfile, which makes Turbopack guess at
  // the workspace root. Pin it explicitly to this directory.
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
