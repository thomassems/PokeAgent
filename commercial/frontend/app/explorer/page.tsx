"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { SpeciesBadge } from "@/components/SpeciesBadge";
import { communityFetch } from "@/lib/community";
import type { TypeName } from "@/lib/types";

type Species = {
  id: string;
  name: string;
  types: TypeName[];
  forms: string[];
  shiny: boolean;
  dynamax: boolean;
  gigantamax: boolean;
  shadow: boolean;
  costume: boolean;
  regional: boolean;
  mythical: boolean;
  legendary: boolean;
  tradable: boolean;
};

const TAGS = [
  "shiny",
  "dynamax",
  "gigantamax",
  "shadow",
  "costume",
  "regional",
  "mythical",
  "legendary",
] as const;

type Tag = (typeof TAGS)[number];

function chips(species: Species): string[] {
  const on: string[] = TAGS.filter((tag) => species[tag]);
  if (!species.tradable) on.push("untradable");
  return [...species.forms, ...on];
}

export default function ExplorerPage() {
  const [query, setQuery] = useState("");
  const [tags, setTags] = useState<Record<Tag, boolean>>({
    shiny: false,
    dynamax: false,
    gigantamax: false,
    shadow: false,
    costume: false,
    regional: false,
    mythical: false,
    legendary: false,
  });
  const [species, setSpecies] = useState<Species[]>([]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (query.trim()) params.set("query", query.trim());
    for (const tag of TAGS) {
      if (tags[tag]) params.set(tag, "true");
    }
    communityFetch<{ species: Species[] }>(`/api/explorer?${params.toString()}`).then(
      (body) => setSpecies(body.species),
    );
  }, [query, tags]);

  return (
    <div className="flex min-h-screen flex-col bg-shell-950 text-ink-100">
      <AppHeader activePage="explorer" />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
        <div>
          <h2 className="text-lg font-semibold">Explorer</h2>
          <p className="mt-1 text-sm text-ink-400">
            This is a hand-kept seed, not a live dex. It is incomplete on
            purpose until a catalog with a written commercial licence covers
            shiny, Dynamax, Gigantamax, costume, and tradability.
          </p>
        </div>
        <div className="flex flex-col gap-3">
          <input
            className="rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
            value={query}
            placeholder="Name"
            onChange={(event) => setQuery(event.target.value)}
          />
          <div className="flex flex-wrap gap-3 text-xs">
            {TAGS.map((tag) => (
              <label key={tag} className="flex items-center gap-1">
                <input
                  type="checkbox"
                  checked={tags[tag]}
                  onChange={(event) =>
                    setTags({ ...tags, [tag]: event.target.checked })
                  }
                />
                {tag}
              </label>
            ))}
          </div>
        </div>
        <ul className="flex flex-col gap-2">
          {species.map((row) => (
            <li
              key={row.id}
              className="flex items-center gap-3 rounded-md border border-shell-800 bg-shell-900 p-3"
            >
              <SpeciesBadge name={row.name} types={row.types} />
              <div>
                <p className="text-sm font-medium">{row.name}</p>
                <p className="text-xs text-ink-400">{chips(row).join(", ")}</p>
              </div>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
