import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Turbopack infers the project root by walking up for a lockfile, which finds an
  // unrelated package-lock.json in the home directory. Pin it to frontend/ so the
  // backend and the rest of the repo stay outside the module-resolution and
  // file-watching scope.
  turbopack: {
    root: import.meta.dirname,
  },

  // In production, Vercel routes /api/* to the backend service via the top-level
  // rewrites in vercel.json, so this must not apply there — it would shadow that
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
