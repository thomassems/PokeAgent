"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { SpeciesRow } from "@/components/SpeciesRow";
import { communityFetch } from "@/lib/community";
import type { TypeName } from "@/lib/types";

type Species = {
  id: string;
  dex: number;
  name: string;
  checked_on?: string | null;
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
  return [...species.forms, ...on].map(
    (chip) => chip.charAt(0).toUpperCase() + chip.slice(1),
  );
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
            Species names, dex numbers, and types come from PvPoke (MIT) and
            PokéAPI (BSD). Shiny, Dynamax, Gigantamax, and costume marks are a
            hand-checked layer and do not cover the whole dex.
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
              <div className="min-w-0 flex-1">
                <SpeciesRow
                  dex={row.dex}
                  name={row.name}
                  types={row.types}
                  chips={chips(row)}
                />
                {row.checked_on ? (
                  <p className="mt-1 pl-[4.25rem] text-[11px] text-ink-500">
                    Checked {row.checked_on}
                  </p>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
