"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { SpeciesRow } from "@/components/SpeciesRow";
import {
  EMPTY_VARIANT_FLAGS,
  VariantFields,
  type VariantFlags,
  type VariantOptions,
} from "@/components/VariantFields";
import { communityFetch, type Profile } from "@/lib/community";
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
  variants?: VariantOptions;
};

const TAGS = [
  "shiny",
  "dynamax",
  "gigantamax",
  "shadow",
  "costume",
  "purified",
  "lucky",
  "regional",
  "mythical",
  "legendary",
] as const;

type Tag = (typeof TAGS)[number];

function chips(species: Species): string[] {
  const chipTags = [
    "shiny",
    "dynamax",
    "gigantamax",
    "shadow",
    "costume",
    "regional",
    "mythical",
    "legendary",
  ] as const;
  const on: string[] = chipTags.filter((tag) => species[tag]);
  if (!species.tradable) on.push("untradable");
  return [...species.forms, ...on].map(
    (chip) => chip.charAt(0).toUpperCase() + chip.slice(1),
  );
}

export default function ExplorerPage() {
  const [catalog, setCatalog] = useState<Species[]>([]);
  const [query, setQuery] = useState("");
  const [speciesId, setSpeciesId] = useState("");
  const [form, setForm] = useState("");
  const [background, setBackground] = useState("");
  const [flags, setFlags] = useState<VariantFlags>(EMPTY_VARIANT_FLAGS);
  const [unverified, setUnverified] = useState<string[]>([]);
  const [tags, setTags] = useState<Record<Tag, boolean>>({
    shiny: false,
    dynamax: false,
    gigantamax: false,
    shadow: false,
    costume: false,
    purified: false,
    lucky: false,
    regional: false,
    mythical: false,
    legendary: false,
  });
  const [species, setSpecies] = useState<Species[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [reportTag, setReportTag] = useState<"wrong" | "missing">("missing");
  const [reportNote, setReportNote] = useState("");
  const [reportNotice, setReportNotice] = useState<string | null>(null);

  useEffect(() => {
    communityFetch<Species[]>("/api/catalog")
      .then(setCatalog)
      .catch(() => setCatalog([]));
    communityFetch<Profile>("/api/me")
      .then(setProfile)
      .catch(() => setProfile(null));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (speciesId) {
      params.set("species_id", speciesId);
      if (form) params.set("form", form);
      if (background) params.set("background", background);
      for (const [name, on] of Object.entries(flags)) {
        if (on) params.set(name, "true");
      }
    } else {
      if (query.trim()) params.set("query", query.trim());
      for (const tag of TAGS) {
        if (tags[tag]) params.set(tag, "true");
      }
    }
    communityFetch<{ species: Species[]; unverified?: string[] }>(
      `/api/explorer?${params.toString()}`,
    )
      .then((body) => {
        setSpecies(body.species);
        setUnverified(body.unverified ?? []);
        setError(null);
      })
      .catch((err: unknown) => {
        setSpecies([]);
        setError(err instanceof Error ? err.message : "Request failed.");
      });
  }, [query, tags, speciesId, form, flags, background]);

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
            placeholder="Filter the Pokémon list"
            onChange={(event) => setQuery(event.target.value)}
          />
          <label className="text-xs text-ink-400">
            Pokémon
            <select
              className="mt-1 block w-full rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
              value={speciesId}
              onChange={(event) => {
                setSpeciesId(event.target.value);
                setFlags(EMPTY_VARIANT_FLAGS);
                setForm("");
                setBackground("");
              }}
            >
              <option value="">Any Pokémon</option>
              {catalog
                .filter((row) => {
                  const needle = query.trim().toLowerCase();
                  return (
                    !needle ||
                    row.name.toLowerCase().includes(needle) ||
                    row.id.includes(needle)
                  );
                })
                .slice(0, 40)
                .map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.name}
                  </option>
                ))}
            </select>
          </label>
          {speciesId && catalog.find((row) => row.id === speciesId)?.variants ? (
            <VariantFields
              variants={catalog.find((row) => row.id === speciesId)!.variants!}
              flags={flags}
              form={form}
              background={background}
              onFlags={setFlags}
              onForm={setForm}
              onBackground={setBackground}
            />
          ) : (
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
          )}
          {unverified.length > 0 ? (
            <p className="text-xs text-ink-500">
              Not yet verified: {unverified.join(", ")}. You can still filter
              by it.
            </p>
          ) : null}
          {error ? <p className="text-sm text-red-300">{error}</p> : null}
          {speciesId ? (
            <form
              className="flex flex-col gap-2 rounded-md border border-shell-800 bg-shell-900 p-3"
              onSubmit={(event) => {
                event.preventDefault();
                setReportNotice(null);
                communityFetch("/api/reports", {
                  method: "POST",
                  body: JSON.stringify({
                    species_id: speciesId,
                    tag: reportTag,
                    note: reportNote,
                  }),
                })
                  .then(() => {
                    setReportNote("");
                    setReportNotice("Sent. It waits for review and is not public.");
                  })
                  .catch((err: unknown) => {
                    setReportNotice(
                      err instanceof Error ? err.message : "Request failed.",
                    );
                  });
              }}
            >
              <p className="text-xs text-ink-400">
                Flag this Pokémon as wrong or missing. An admin reviews it.
                Nothing changes on this page until that review is approved.
              </p>
              {profile ? (
                <>
                  <div className="flex gap-3 text-xs">
                    <label className="flex items-center gap-1">
                      <input
                        type="radio"
                        checked={reportTag === "missing"}
                        onChange={() => setReportTag("missing")}
                      />
                      Missing
                    </label>
                    <label className="flex items-center gap-1">
                      <input
                        type="radio"
                        checked={reportTag === "wrong"}
                        onChange={() => setReportTag("wrong")}
                      />
                      Wrong
                    </label>
                  </div>
                  <input
                    className="rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
                    value={reportNote}
                    placeholder="Short note"
                    onChange={(event) => setReportNote(event.target.value)}
                  />
                  <button
                    type="submit"
                    className="w-fit rounded-sm border border-shell-700 px-2 py-1 text-xs"
                  >
                    Send report
                  </button>
                </>
              ) : (
                <p className="text-xs text-ink-500">Sign in to send a report.</p>
              )}
              {reportNotice ? (
                <p className="text-xs text-ink-300">{reportNotice}</p>
              ) : null}
            </form>
          ) : null}
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
