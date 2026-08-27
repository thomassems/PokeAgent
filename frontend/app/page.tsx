"use client";

import { useEffect, useState } from "react";

type Health = {
  status: string;
  service: string;
};

// Scaffold-only page. It fetches a relative path from the browser specifically to
// prove the dev proxy in next.config.ts reaches FastAPI — a server-side fetch would
// need an absolute URL and so would not exercise the same route.
export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((response) => {
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return response.json() as Promise<Health>;
      })
      .then(setHealth)
      .catch((cause: Error) => setError(cause.message));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8 font-mono">
      <h1 className="text-lg font-semibold">PokeAgent</h1>
      <p className="text-sm text-gray-500">frontend → /api/health → backend</p>
      {health && (
        <pre className="rounded border border-green-600 px-4 py-2 text-sm text-green-700">
          {JSON.stringify(health, null, 2)}
        </pre>
      )}
      {error && (
        <pre className="rounded border border-red-600 px-4 py-2 text-sm text-red-700">
          backend unreachable: {error}
        </pre>
      )}
      {!health && !error && <p className="text-sm text-gray-400">checking…</p>}
    </main>
  );
}
