"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { SpeciesRow } from "@/components/SpeciesRow";
import { communityFetch, type Profile } from "@/lib/community";
import type { TypeName } from "@/lib/types";

type CollectionItem = {
  kind: "costume" | "background";
  value: string;
  label: string;
  dex: number;
  name: string;
  types: TypeName[];
  owned: boolean;
  shiny: boolean;
  shiny_released: boolean;
};

type Collection = {
  id: string;
  title: string;
  summary: string;
  have: number;
  total: number;
  items: CollectionItem[];
};

type Filter = "all" | "have" | "missing";

export default function CollectionPage() {
  const params = useParams<{ id: string }>();
  const [profile, setProfile] = useState<Profile | null | undefined>(undefined);
  const [collection, setCollection] = useState<Collection | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    communityFetch<Collection>(`/api/collections/${params.id}`)
      .then((body) => {
        setCollection(body);
        setError(null);
      })
      .catch((err: unknown) => {
        setCollection(null);
        setError(err instanceof Error ? err.message : "Request failed.");
      });
  }, [params.id]);

  useEffect(() => {
    communityFetch<Profile>("/api/me")
      .then(setProfile)
      .catch(() => setProfile(null));
    load();
  }, [load]);

  const mark = async (item: CollectionItem, owned: boolean, shiny: boolean) => {
    setBusy(true);
    setError(null);
    try {
      const body = await communityFetch<Collection>(
        `/api/collections/${params.id}/items`,
        {
          method: "POST",
          body: JSON.stringify({
            kind: item.kind,
            value: item.value,
            owned,
            shiny,
          }),
        },
      );
      setCollection(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setBusy(false);
    }
  };

  const addMissing = async () => {
    setBusy(true);
    setError(null);
    try {
      const body = await communityFetch<Collection>(
        `/api/collections/${params.id}/wants`,
        { method: "POST", body: "{}" },
      );
      setCollection(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setBusy(false);
    }
  };

  const items =
    collection?.items.filter((item) => {
      if (filter === "have") return item.owned;
      if (filter === "missing") return !item.owned;
      return true;
    }) ?? [];
  const missing = collection ? collection.total - collection.have : 0;

  return (
    <div className="flex min-h-screen flex-col bg-shell-950 text-ink-100">
      <AppHeader activePage="collections" />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 px-4 py-6">
        <div>
          <p className="text-xs text-ink-500">
            <Link href="/collections" className="underline">
              Collections
            </Link>
          </p>
          <h2 className="mt-1 text-lg font-semibold">
            {collection?.title ?? "Collection"}
          </h2>
          {collection ? (
            <p className="mt-1 text-sm text-ink-100">
              Have {collection.have} of {collection.total}
            </p>
          ) : null}
          <p className="mt-1 text-xs text-ink-500">
            The total is verified rows only. Anything still not yet verified
            stays off this list.
          </p>
        </div>
        {profile === null ? (
          <p className="text-sm">
            <Link href="/account" className="text-plasma-400 underline">
              Sign in
            </Link>{" "}
            to mark what you own.
          </p>
        ) : null}
        {error ? <p className="text-sm text-plasma-300">{error}</p> : null}
        {collection ? (
          <>
            <div className="flex flex-wrap gap-2">
              {(
                [
                  ["all", "All"],
                  ["have", "Have"],
                  ["missing", "Missing"],
                ] as const
              ).map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setFilter(id)}
                  className={`min-h-11 rounded-sm border px-3 text-sm ${
                    filter === id
                      ? "border-plasma-500 bg-shell-800 text-ink-100"
                      : "border-shell-700 text-ink-400"
                  }`}
                >
                  {label}
                </button>
              ))}
              <button
                type="button"
                disabled={busy || missing === 0 || profile === null}
                onClick={() => void addMissing()}
                className="min-h-11 rounded-sm bg-plasma-500 px-3 text-sm text-shell-950 disabled:opacity-40"
              >
                Add missing to want list
              </button>
            </div>
            <ul className="flex flex-col gap-2">
              {items.map((item) => (
                <li
                  key={`${item.kind}:${item.value}`}
                  className="rounded-md border border-shell-800 bg-shell-900 p-3"
                >
                  <SpeciesRow
                    dex={item.dex}
                    name={item.label}
                    types={item.types}
                    chips={[
                      item.kind === "costume" ? "Costume" : "Background",
                      ...(item.shiny_released ? ["Shiny released"] : []),
                    ]}
                  />
                  <div className="mt-2 flex flex-wrap gap-4 pl-14">
                    <label className="flex min-h-11 items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        className="size-4"
                        checked={item.owned}
                        disabled={busy || profile == null}
                        onChange={(event) =>
                          void mark(item, event.target.checked, item.shiny && event.target.checked)
                        }
                      />
                      Owned
                    </label>
                    <label className="flex min-h-11 items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        className="size-4"
                        checked={item.owned && item.shiny}
                        disabled={busy || profile == null}
                        onChange={(event) => void mark(item, true, event.target.checked)}
                      />
                      Shiny
                    </label>
                  </div>
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </main>
    </div>
  );
}
