import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { NextConfig } from "next";

// The display name lives in commercial/.env with the other server config.
// Next only auto-loads frontend/.env*, and that file must not hold keys, so
// this copies APP_NAME and nothing else. A missing file keeps the default.
function readAppName(envPath: string): void {
  if (process.env.APP_NAME?.trim()) return;
  let text: string;
  try {
    text = readFileSync(envPath, "utf8");
  } catch (error) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") return;
    throw error;
  }
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed.startsWith("APP_NAME=")) continue;
    const value = trimmed.slice("APP_NAME=".length).trim().replace(/^["']|["']$/g, "");
    if (value) process.env.APP_NAME = value;
    return;
  }
}

readAppName(join(import.meta.dirname, "..", ".env"));

const nextConfig: NextConfig = {
  // Turbopack infers the project root by walking up for a lockfile, which finds an
  // unrelated package-lock.json in the home directory. Pin it to frontend/ so the
  // backend and the rest of the repo stay outside the module-resolution and
  // file-watching scope.
  turbopack: {
    root: import.meta.dirname,
  },

  // In production, Vercel routes /api/* to the backend service via the top-level
  // rewrites in vercel.json, so this must not apply there - it would shadow that
  // route table. It exists only to reproduce the same single-origin routing
  // against a local uvicorn, which keeps the browser free of CORS entirely.
  async rewrites() {
    if (process.env.NODE_ENV === "production") return [];
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
