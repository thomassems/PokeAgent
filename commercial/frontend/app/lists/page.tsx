"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { SpeciesRow } from "@/components/SpeciesRow";
import {
  EMPTY_VARIANT_FLAGS,
  VariantFields,
  type VariantFlags,
  type VariantOptions,
} from "@/components/VariantFields";
import { useAppName } from "@/lib/app-name";
import { communityFetch, type Profile } from "@/lib/community";
import type { TypeName } from "@/lib/types";

type Species = {
  id: string;
  dex: number;
  name: string;
  types: TypeName[];
  forms: string[];
  variants: VariantOptions;
};

type ListEntry = {
  id: number;
  kind: "want" | "have";
  species_id: string;
  dex: number;
  name: string;
  types: TypeName[];
  form: string;
  shiny: boolean;
  dynamax: boolean;
  gigantamax: boolean;
  shadow: boolean;
  purified: boolean;
  lucky: boolean;
  costume: boolean;
  notes: string;
  trade_notes: string[];
};

const FLAGS = [
  "shiny",
  "dynamax",
  "gigantamax",
  "shadow",
  "purified",
  "lucky",
  "costume",
] as const satisfies readonly (keyof VariantFlags)[];

function tags(entry: ListEntry): string {
  const on = FLAGS.filter((flag) => entry[flag]);
  const form = entry.form ? [entry.form] : [];
  return [...form, ...on].join(", ");
}

function matchesFilter(
  entry: ListEntry,
  speciesId: string,
  form: string,
  flags: VariantFlags,
): boolean {
  if (speciesId && entry.species_id !== speciesId) return false;
  if (form && entry.form !== form) return false;
  return FLAGS.every((flag) => !flags[flag] || entry[flag]);
}

export default function ListsPage() {
  const appName = useAppName();
  const [profile, setProfile] = useState<Profile | null | undefined>(undefined);
  const [catalog, setCatalog] = useState<Species[]>([]);
  const [entries, setEntries] = useState<ListEntry[]>([]);
  const [kind, setKind] = useState<"want" | "have">("want");
  const [speciesId, setSpeciesId] = useState("magikarp");
  const [speciesQuery, setSpeciesQuery] = useState("");
  const [form, setForm] = useState("");
  const [notes, setNotes] = useState("");
  const [flags, setFlags] = useState(EMPTY_VARIANT_FLAGS);
  const [filterSpeciesId, setFilterSpeciesId] = useState("");
  const [filterForm, setFilterForm] = useState("");
  const [filterFlags, setFilterFlags] = useState(EMPTY_VARIANT_FLAGS);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    communityFetch<{ entries: ListEntry[] }>("/api/lists")
      .then((body) => setEntries(body.entries))
      .catch(() => setEntries([]));
  };

  useEffect(() => {
    communityFetch<Profile>("/api/me")
      .then(setProfile)
      .catch(() => setProfile(null));
    communityFetch<Species[]>("/api/catalog").then((rows) => {
      setCatalog(rows);
      const preferred = rows.find((row) => row.id === "magikarp") ?? rows[0];
      if (preferred) setSpeciesId(preferred.id);
    });
    load();
  }, []);

  const add = async () => {
    setError(null);
    try {
      await communityFetch("/api/lists", {
        method: "POST",
        body: JSON.stringify({
          kind,
          species_id: speciesId,
          form,
          notes,
          ...flags,
        }),
      });
      setNotes("");
      setFlags(EMPTY_VARIANT_FLAGS);
      setForm("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    }
  };

  const remove = async (id: number) => {
    setError(null);
    await communityFetch(`/api/lists/${id}`, { method: "DELETE" });
    load();
  };

  return (
    <div className="flex min-h-screen flex-col bg-shell-950 text-ink-100">
      <AppHeader activePage="lists" />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
        <div>
          <h2 className="text-lg font-semibold">My lists</h2>
          <p className="mt-1 text-sm text-ink-400">
            Type what you want and what you have. {appName} does not read a
            Pokémon GO account, and it does not arrange account trades.
          </p>
        </div>
        {profile === null ? (
          <p className="text-sm">
            <Link href="/account" className="text-plasma-400 underline">
              Sign in
            </Link>{" "}
            to keep a list.
          </p>
        ) : null}
        {profile ? (
          <form
            className="flex flex-col gap-3 rounded-md border border-shell-800 bg-shell-900 p-4"
            onSubmit={(event) => {
              event.preventDefault();
              void add();
            }}
          >
            <div className="flex flex-wrap gap-3">
              <label className="text-xs text-ink-400">
                List
                <select
                  className="mt-1 block rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
                  value={kind}
                  onChange={(event) => setKind(event.target.value as "want" | "have")}
                >
                  <option value="want">Want</option>
                  <option value="have">Have</option>
                </select>
              </label>
              <label className="min-w-40 flex-1 text-xs text-ink-400">
                Pokémon
                <input
                  className="mt-1 block w-full rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
                  value={speciesQuery}
                  placeholder="Filter by name"
                  onChange={(event) => setSpeciesQuery(event.target.value)}
                />
                <select
                  className="mt-1 block w-full rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
                  value={speciesId}
                  onChange={(event) => {
                    setSpeciesId(event.target.value);
                    setFlags(EMPTY_VARIANT_FLAGS);
                    setForm("");
                  }}
                >
                  {(() => {
                    const needle = speciesQuery.trim().toLowerCase();
                    const matched = catalog.filter(
                      (species) =>
                        !needle ||
                        species.name.toLowerCase().includes(needle) ||
                        species.id.includes(needle),
                    );
                    const limited = matched.slice(0, 40);
                    const selected = catalog.find((species) => species.id === speciesId);
                    const options =
                      selected && !limited.some((species) => species.id === selected.id)
                        ? [selected, ...limited]
                        : limited;
                    return options.map((species) => (
                      <option key={species.id} value={species.id}>
                        {species.name}
                      </option>
                    ));
                  })()}
                </select>
              </label>
            </div>
            {(() => {
              const selected = catalog.find((species) => species.id === speciesId);
              if (!selected) return null;
              return (
                <VariantFields
                  variants={selected.variants}
                  flags={flags}
                  form={form}
                  onFlags={setFlags}
                  onForm={setForm}
                />
              );
            })()}
            <label className="text-xs text-ink-400">
              Notes
              <input
                className="mt-1 block w-full rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
              />
            </label>
            {error ? <p className="text-sm text-red-300">{error}</p> : null}
            <button
              type="submit"
              className="w-fit rounded-sm bg-plasma-500 px-3 py-1 text-sm text-shell-950"
            >
              Add
            </button>
          </form>
        ) : null}
        <section className="flex flex-col gap-3">
          <h3 className="text-sm font-medium">Filter this list</h3>
          <label className="text-xs text-ink-400">
            Pokémon
            <select
              className="mt-1 block w-full rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
              value={filterSpeciesId}
              onChange={(event) => {
                setFilterSpeciesId(event.target.value);
                setFilterFlags(EMPTY_VARIANT_FLAGS);
                setFilterForm("");
              }}
            >
              <option value="">Any Pokémon</option>
              {catalog.map((species) => (
                <option key={species.id} value={species.id}>
                  {species.name}
                </option>
              ))}
            </select>
          </label>
          {filterSpeciesId ? (
            <VariantFields
              variants={
                catalog.find((species) => species.id === filterSpeciesId)?.variants ?? {
                  shiny: false,
                  dynamax: false,
                  gigantamax: false,
                  shadow: false,
                  purified: false,
                  lucky: false,
                  costume: false,
                  forms: [],
                  costume_forms: [],
                }
              }
              flags={filterFlags}
              form={filterForm}
              onFlags={setFilterFlags}
              onForm={setFilterForm}
            />
          ) : (
            <p className="text-xs text-ink-500">
              Pick a Pokémon to filter by a variant it actually has.
            </p>
          )}
        </section>
        <ul className="flex flex-col gap-3">
          {entries
            .filter((entry) =>
              matchesFilter(entry, filterSpeciesId, filterForm, filterFlags),
            )
            .map((entry) => (
            <li
              key={entry.id}
              className="flex gap-3 rounded-md border border-shell-800 bg-shell-900 p-3"
            >
              <div className="min-w-0 flex-1">
                <p className="text-[11px] tracking-wide text-ink-500 uppercase">
                  {entry.kind}
                </p>
                <SpeciesRow
                  dex={entry.dex}
                  name={entry.name}
                  types={entry.types}
                  chips={tags(entry)
                    .split(", ")
                    .filter(Boolean)}
                />
                {entry.notes ? (
                  <p className="text-xs text-ink-400">{entry.notes}</p>
                ) : null}
                <ul className="mt-1 list-disc pl-4 text-xs text-ink-300">
                  {entry.trade_notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </div>
              <button
                type="button"
                className="text-xs text-ink-400 underline"
                onClick={() => void remove(entry.id)}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
