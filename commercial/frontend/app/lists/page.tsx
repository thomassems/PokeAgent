"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { SpeciesBadge } from "@/components/SpeciesBadge";
import { communityFetch, type Profile } from "@/lib/community";
import type { TypeName } from "@/lib/types";

type Species = {
  id: string;
  name: string;
  types: TypeName[];
  forms: string[];
};

type ListEntry = {
  id: number;
  kind: "want" | "have";
  species_id: string;
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
] as const;

type Flag = (typeof FLAGS)[number];

const EMPTY_FLAGS: Record<Flag, boolean> = {
  shiny: false,
  dynamax: false,
  gigantamax: false,
  shadow: false,
  purified: false,
  lucky: false,
  costume: false,
};

function tags(entry: ListEntry): string {
  const on = FLAGS.filter((flag) => entry[flag]);
  const form = entry.form ? [entry.form] : [];
  return [...form, ...on].join(", ");
}

export default function ListsPage() {
  const [profile, setProfile] = useState<Profile | null | undefined>(undefined);
  const [catalog, setCatalog] = useState<Species[]>([]);
  const [entries, setEntries] = useState<ListEntry[]>([]);
  const [kind, setKind] = useState<"want" | "have">("want");
  const [speciesId, setSpeciesId] = useState("magikarp");
  const [form, setForm] = useState("");
  const [notes, setNotes] = useState("");
  const [flags, setFlags] = useState(EMPTY_FLAGS);
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
      if (rows[0]) setSpeciesId(rows[0].id);
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
      setFlags(EMPTY_FLAGS);
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
            Type what you want and what you have. Trainermon does not read a
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
              <label className="text-xs text-ink-400">
                Pokémon
                <select
                  className="mt-1 block rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
                  value={speciesId}
                  onChange={(event) => setSpeciesId(event.target.value)}
                >
                  {catalog.map((species) => (
                    <option key={species.id} value={species.id}>
                      {species.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-xs text-ink-400">
                Form
                <input
                  className="mt-1 block rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
                  value={form}
                  onChange={(event) => setForm(event.target.value)}
                  placeholder="blank is the base form"
                />
              </label>
            </div>
            <div className="flex flex-wrap gap-3 text-xs">
              {FLAGS.map((flag) => (
                <label key={flag} className="flex items-center gap-1">
                  <input
                    type="checkbox"
                    checked={flags[flag]}
                    onChange={(event) =>
                      setFlags({ ...flags, [flag]: event.target.checked })
                    }
                  />
                  {flag}
                </label>
              ))}
            </div>
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
        <ul className="flex flex-col gap-3">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className="flex gap-3 rounded-md border border-shell-800 bg-shell-900 p-3"
            >
              <SpeciesBadge name={entry.name} types={entry.types} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">
                  {entry.kind === "want" ? "Want" : "Have"} {entry.name}
                  {tags(entry) ? ` (${tags(entry)})` : ""}
                </p>
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
