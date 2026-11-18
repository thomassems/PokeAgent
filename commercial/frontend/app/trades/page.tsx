"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { SpeciesRow } from "@/components/SpeciesRow";
import { communityFetch, type Profile } from "@/lib/community";
import type { TypeName } from "@/lib/types";

type Matched = {
  id: number;
  dex: number;
  name: string;
  types: TypeName[];
  form: string;
  shiny: boolean;
  dynamax: boolean;
  gigantamax: boolean;
  shadow: boolean;
  costume: boolean;
  lucky: boolean;
};

type Match = {
  trainer_name: string;
  city: string;
  they_have: Matched[];
  i_have: Matched[];
};

function chips(row: Matched): string[] {
  return [
    row.form,
    row.shiny ? "Shiny" : "",
    row.dynamax ? "Dynamax" : "",
    row.gigantamax ? "Gigantamax" : "",
    row.shadow ? "Shadow" : "",
    row.costume ? "Costume" : "",
    row.lucky ? "Lucky" : "",
  ].filter(Boolean);
}

export default function TradesPage() {
  const [profile, setProfile] = useState<Profile | null | undefined>(undefined);
  const [city, setCity] = useState("Toronto");
  const [matches, setMatches] = useState<Match[]>([]);
  const [error, setError] = useState<string | null>(null);

  const search = async (nextCity: string) => {
    setError(null);
    try {
      const body = await communityFetch<{ matches: Match[] }>(
        `/api/trades/search?city=${encodeURIComponent(nextCity)}`,
      );
      setMatches(body.matches);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    }
  };

  useEffect(() => {
    communityFetch<Profile>("/api/me")
      .then((me) => {
        setProfile(me);
        const next = me.city || "Toronto";
        setCity(next);
        void search(next);
      })
      .catch(() => setProfile(null));
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-shell-950 text-ink-100">
      <AppHeader activePage="trades" />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
        <div>
          <h2 className="text-lg font-semibold">Trades</h2>
          <p className="mt-1 text-sm text-ink-400">
            This is a filter, not an assistant. It shows trainers whose have
            list matches your want list, or the other way around. No friend
            codes, and no account trading.
          </p>
        </div>
        {profile === null ? (
          <p className="text-sm">
            <Link href="/account" className="text-plasma-400 underline">
              Sign in
            </Link>{" "}
            to search.
          </p>
        ) : null}
        {profile ? (
          <form
            className="flex items-end gap-3"
            onSubmit={(event) => {
              event.preventDefault();
              void search(city);
            }}
          >
            <label className="text-xs text-ink-400">
              City
              <input
                className="mt-1 block rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
                value={city}
                onChange={(event) => setCity(event.target.value)}
              />
            </label>
            <button
              type="submit"
              className="rounded-sm bg-plasma-500 px-3 py-1 text-sm text-shell-950"
            >
              Search
            </button>
            <button
              type="button"
              className="rounded-sm border border-shell-700 px-3 py-1 text-sm"
              onClick={() => {
                setCity("all");
                void search("all");
              }}
            >
              Every city
            </button>
          </form>
        ) : null}
        {error ? <p className="text-sm text-red-300">{error}</p> : null}
        {profile && matches.length === 0 && !error ? (
          <p className="text-sm text-ink-400">No overlapping lists in {city}.</p>
        ) : null}
        <ul className="flex flex-col gap-3">
          {matches.map((match) => (
            <li
              key={`${match.trainer_name}-${match.city}`}
              className="rounded-md border border-shell-800 bg-shell-900 p-4"
            >
              <p className="text-sm font-medium">
                {match.trainer_name} · {match.city}
              </p>
              {match.they_have.length ? (
                <div className="mt-3">
                  <p className="text-xs text-ink-400">They have what you want</p>
                  <ul className="mt-2 flex flex-col gap-2">
                    {match.they_have.map((row) => (
                      <li key={row.id}>
                        <SpeciesRow
                          dex={row.dex}
                          name={row.name}
                          types={row.types}
                          chips={chips(row)}
                        />
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {match.i_have.length ? (
                <div className="mt-3">
                  <p className="text-xs text-ink-400">You have what they want</p>
                  <ul className="mt-2 flex flex-col gap-2">
                    {match.i_have.map((row) => (
                      <li key={row.id}>
                        <SpeciesRow
                          dex={row.dex}
                          name={row.name}
                          types={row.types}
                          chips={chips(row)}
                        />
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
