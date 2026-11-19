"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { communityFetch, type Profile } from "@/lib/community";

type CollectionSummary = {
  id: string;
  title: string;
  summary: string;
  have: number;
  total: number;
};

export default function CollectionsPage() {
  const [profile, setProfile] = useState<Profile | null | undefined>(undefined);
  const [collections, setCollections] = useState<CollectionSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    communityFetch<Profile>("/api/me")
      .then(setProfile)
      .catch(() => setProfile(null));
    communityFetch<{ collections: CollectionSummary[] }>("/api/collections")
      .then((body) => setCollections(body.collections))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Request failed.");
      });
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-shell-950 text-ink-100">
      <AppHeader activePage="collections" />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 px-4 py-6">
        <div>
          <h2 className="text-lg font-semibold">Collections</h2>
          <p className="mt-1 text-sm text-ink-400">
            Have X of Y counts verified rows only. Checklists are free for now.
          </p>
        </div>
        {profile === null ? (
          <p className="text-sm">
            <Link href="/account" className="text-plasma-400 underline">
              Sign in
            </Link>{" "}
            to track a collection.
          </p>
        ) : null}
        {error ? <p className="text-sm text-plasma-300">{error}</p> : null}
        <ul className="flex flex-col gap-3">
          {collections.map((collection) => (
            <li key={collection.id}>
              <Link
                href={`/collections/${collection.id}`}
                className="block rounded-md border border-shell-800 bg-shell-900 p-3"
              >
                <p className="text-sm font-medium">{collection.title}</p>
                <p className="mt-1 text-sm text-ink-300">
                  Have {collection.have} of {collection.total}
                </p>
                <p className="mt-1 text-xs text-ink-500">{collection.summary}</p>
              </Link>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
