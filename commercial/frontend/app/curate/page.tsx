"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { communityFetch, type Profile } from "@/lib/community";

type Fact = {
  id: number;
  species_id: string;
  species_name?: string;
  kind: string;
  kind_label?: string;
  value: string;
  label?: string;
  source_url: string;
  verified_at: string;
  verified_by: string;
  status: string;
  notes: string;
  source_type?: string;
  community_source_url?: string;
  aliases?: string[];
  merged_into?: string;
  shiny?: "confirmed" | "unknown" | null;
  verification?: {
    verdict: string;
    confidence: string;
    sources: string[];
    urls: string[];
    checked_at: string;
    reason: string;
  } | null;
};

type SourceFilter = "all" | "official" | "community";
type StatusFilter = "all" | "draft" | "approved" | "rejected" | "merged";
type Pending = "approved" | "rejected" | null;

const inputClass =
  "mt-1 block w-full rounded-sm border border-shell-700 bg-shell-950 px-2 py-2 text-sm";

export default function CuratePage() {
  const [profile, setProfile] = useState<Profile | null | undefined>(undefined);
  const [facts, setFacts] = useState<Fact[]>([]);
  const [denied, setDenied] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pasted, setPasted] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [verifiedAt, setVerifiedAt] = useState("2026-11-18");
  const [speciesQuery, setSpeciesQuery] = useState("");
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("draft");
  const [selected, setSelected] = useState<number[]>([]);
  const [pending, setPending] = useState<Pending>(null);

  const load = () => {
    communityFetch<{ facts: Fact[] }>("/api/curation")
      .then((body) => {
        setFacts(body.facts);
        setDenied(null);
        setSelected([]);
        setPending(null);
      })
      .catch((err: unknown) => {
        setFacts([]);
        setDenied(err instanceof Error ? err.message : "Request failed.");
      });
  };

  useEffect(() => {
    communityFetch<Profile>("/api/me")
      .then(setProfile)
      .catch(() => setProfile(null));
    load();
  }, []);

  const speciesOptions = useMemo(() => {
    const names = new Map<string, string>();
    for (const fact of facts) {
      names.set(fact.species_id, fact.species_name || fact.species_id);
    }
    return [...names.entries()].sort((a, b) => a[1].localeCompare(b[1]));
  }, [facts]);

  const filtered = useMemo(() => {
    const needle = speciesQuery.trim().toLowerCase();
    return facts.filter((fact) => {
      if (needle) {
        const id = fact.species_id.toLowerCase();
        const name = (fact.species_name || "").toLowerCase();
        if (!id.includes(needle) && !name.includes(needle)) return false;
      }
      const source = fact.source_type === "community" ? "community" : "official";
      if (sourceFilter !== "all" && source !== sourceFilter) return false;
      if (statusFilter !== "all" && fact.status !== statusFilter) return false;
      return true;
    });
  }, [facts, speciesQuery, sourceFilter, statusFilter]);

  const actionable = filtered.filter((fact) => fact.status !== "merged");
  const selectedHere = actionable.filter((fact) => selected.includes(fact.id));
  const allSelected =
    actionable.length > 0 && selectedHere.length === actionable.length;

  const draft = async () => {
    setError(null);
    setNotice(null);
    try {
      const body = await communityFetch<{ facts: Fact[] }>("/api/curation/draft", {
        method: "POST",
        body: JSON.stringify({
          pasted,
          source_url: sourceUrl,
          verified_at: verifiedAt,
        }),
      });
      const waiting = body.facts.filter((fact) => fact.status === "draft");
      setNotice(
        waiting.length > 0
          ? "Drafts are waiting below. They stay off Explorer until you approve them."
          : "Nothing new is waiting. Those rows are already on file.",
      );
      setPasted("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    }
  };

  const decide = async (id: number, status: "approve" | "reject" | "unapprove") => {
    setError(null);
    try {
      await communityFetch(`/api/curation/${id}/${status}`, {
        method: "POST",
        body: "{}",
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    }
  };

  const toggle = (id: number) => {
    setPending(null);
    setSelected((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  };

  const toggleAll = () => {
    setPending(null);
    setSelected(allSelected ? [] : actionable.map((fact) => fact.id));
  };

  const confirmBulk = async () => {
    if (!pending || selectedHere.length === 0) return;
    setError(null);
    try {
      await communityFetch("/api/curation/bulk", {
        method: "POST",
        body: JSON.stringify({
          ids: selectedHere.map((fact) => fact.id),
          status: pending,
        }),
      });
      setNotice(
        pending === "approved"
          ? "Those rows are approved. Your email is the check on each one."
          : "Those rows are rejected.",
      );
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-shell-950 text-ink-100">
      <AppHeader activePage="curate" />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
        <div>
          <h2 className="text-lg font-semibold">Curate</h2>
          <p className="mt-1 text-sm text-ink-400">
            Paste an announcement and the model drafts rows from that text only.
            The costume verifier approves a row when an official Pokémon GO post
            is already cited, or when the game data and a second source agree.
            Needs you is what it could not corroborate.
          </p>
        </div>
        {profile === null ? (
          <p className="text-sm">
            <Link href="/account" className="text-plasma-400 underline">
              Sign in
            </Link>{" "}
            with an admin account.
          </p>
        ) : null}
        {denied ? <p className="text-sm text-ink-300">{denied}</p> : null}
        {profile && !denied ? (
          <form
            className="flex flex-col gap-3 rounded-md border border-shell-800 bg-shell-900 p-4"
            onSubmit={(event) => {
              event.preventDefault();
              void draft();
            }}
          >
            <label className="text-xs text-ink-400">
              Pasted announcement
              <textarea
                className="mt-1 block min-h-28 w-full rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
                value={pasted}
                onChange={(event) => setPasted(event.target.value)}
              />
            </label>
            <label className="text-xs text-ink-400">
              Source link
              <input
                className="mt-1 block w-full rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
                value={sourceUrl}
                onChange={(event) => setSourceUrl(event.target.value)}
                placeholder="https://"
              />
            </label>
            <label className="text-xs text-ink-400">
              Date checked
              <input
                className="mt-1 block rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
                value={verifiedAt}
                onChange={(event) => setVerifiedAt(event.target.value)}
              />
            </label>
            {notice ? <p className="text-sm text-ink-300">{notice}</p> : null}
            {error ? <p className="text-sm text-red-300">{error}</p> : null}
            <button
              type="submit"
              className="min-h-11 w-fit rounded-sm bg-plasma-500 px-3 py-1 text-sm text-shell-950"
            >
              Draft rows
            </button>
          </form>
        ) : null}

        <section id="curate-filters" className="flex flex-col gap-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <label className="text-xs text-ink-400">
              Pokémon
              <input
                className={inputClass}
                list="curate-species"
                value={speciesQuery}
                placeholder="pikachu"
                onChange={(event) => {
                  setSpeciesQuery(event.target.value);
                  setSelected([]);
                  setPending(null);
                }}
              />
              <datalist id="curate-species">
                {speciesOptions.map(([id, name]) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                ))}
              </datalist>
            </label>
            <label className="text-xs text-ink-400">
              Source
              <select
                className={inputClass}
                value={sourceFilter}
                onChange={(event) => {
                  setSourceFilter(event.target.value as SourceFilter);
                  setSelected([]);
                  setPending(null);
                }}
              >
                <option value="all">All sources</option>
                <option value="official">Official</option>
                <option value="community">Community</option>
              </select>
            </label>
            <label className="text-xs text-ink-400">
              Status
              <select
                className={inputClass}
                value={statusFilter}
                onChange={(event) => {
                  setStatusFilter(event.target.value as StatusFilter);
                  setSelected([]);
                  setPending(null);
                }}
              >
                <option value="draft">Needs you</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="merged">Merged aliases</option>
                <option value="all">All statuses</option>
              </select>
            </label>
          </div>
          <p className="text-sm text-ink-300">
            Showing {filtered.length} of {facts.length}
          </p>
          {profile && !denied ? (
            <div className="flex flex-col gap-2 rounded-md border border-shell-800 bg-shell-900 p-3">
              <label className="flex min-h-11 items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  className="h-4 w-4"
                  checked={allSelected}
                  onChange={toggleAll}
                  disabled={actionable.length === 0}
                />
                Select all in this filter ({actionable.length})
              </label>
              {pending ? (
                <div className="flex flex-col gap-2">
                  <p className="text-sm">
                    {pending === "approved" ? "Approve" : "Reject"} {selectedHere.length}{" "}
                    selected {selectedHere.length === 1 ? "row" : "rows"}? Approval
                    writes your admin email on each row, the same as the button on
                    a single row.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="min-h-11 rounded-sm bg-plasma-500 px-3 text-sm text-shell-950"
                      onClick={() => void confirmBulk()}
                    >
                      Confirm {pending === "approved" ? "approve" : "reject"}
                    </button>
                    <button
                      type="button"
                      className="min-h-11 rounded-sm border border-shell-700 px-3 text-sm"
                      onClick={() => setPending(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="min-h-11 rounded-sm bg-plasma-500 px-3 text-sm text-shell-950 disabled:opacity-40"
                    disabled={selectedHere.length === 0}
                    onClick={() => setPending("approved")}
                  >
                    Approve selected
                  </button>
                  <button
                    type="button"
                    className="min-h-11 rounded-sm border border-shell-700 px-3 text-sm disabled:opacity-40"
                    disabled={selectedHere.length === 0}
                    onClick={() => setPending("rejected")}
                  >
                    Reject selected
                  </button>
                </div>
              )}
            </div>
          ) : null}
          {filtered.length === 0 ? (
            <p className="text-sm text-ink-500">No rows match this filter.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {filtered.map((fact) => (
                <li
                  key={fact.id}
                  className="rounded-md border border-shell-800 bg-shell-900 p-3 text-sm"
                >
                  <div className="flex items-start gap-3">
                    {fact.status !== "merged" ? (
                      <label className="flex min-h-11 min-w-11 items-center">
                        <input
                          type="checkbox"
                          className="h-4 w-4"
                          aria-label={`Select ${fact.species_name || fact.species_id} ${fact.label || fact.value}`}
                          checked={selected.includes(fact.id)}
                          onChange={() => toggle(fact.id)}
                        />
                      </label>
                    ) : null}
                    <div className="min-w-0 flex-1">
                      <p className="font-medium">
                        {fact.species_name || fact.species_id} ·{" "}
                        {fact.kind_label || fact.kind} · {fact.label || fact.value}
                        {fact.verified_by === "auto-verifier" &&
                        fact.status === "approved" ? (
                          <span className="ml-2 rounded-sm bg-plasma-500 px-1.5 py-0.5 text-xs font-medium text-shell-950">
                            Auto-verified
                          </span>
                        ) : null}
                      </p>
                      <p className="text-xs text-ink-500">{fact.value}</p>
                      {fact.verification?.reason ? (
                        <p className="text-xs text-ink-300">{fact.verification.reason}</p>
                      ) : null}
                      {fact.verification?.urls?.length ? (
                        <ul className="mt-1 flex flex-col gap-1">
                          {fact.verification.urls.map((url) => (
                            <li key={url}>
                              <a
                                href={url}
                                className="break-all text-xs text-plasma-400 underline"
                                target="_blank"
                                rel="noreferrer"
                              >
                                {url}
                              </a>
                            </li>
                          ))}
                        </ul>
                      ) : null}
                      {fact.aliases && fact.aliases.length > 0 ? (
                        <p className="text-xs text-ink-400">
                          Community code: {fact.aliases.join(", ")}
                        </p>
                      ) : null}
                      {fact.merged_into ? (
                        <p className="text-xs text-ink-400">
                          Merged into {fact.merged_into}
                        </p>
                      ) : null}
                      {fact.shiny ? (
                        <p className="text-xs text-ink-400">
                          Shiny: {fact.shiny === "confirmed" ? "confirmed" : "unknown"}
                        </p>
                      ) : null}
                      <p className="break-all text-xs text-ink-400">
                        {fact.source_type === "community" ? "Community" : "Official"}{" "}
                        {fact.status} · {fact.verified_at} · {fact.source_url}
                      </p>
                      {fact.status !== "merged" ? (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {fact.status !== "approved" ? (
                            <button
                              type="button"
                              className="min-h-11 rounded-sm bg-plasma-500 px-2 text-xs text-shell-950"
                              onClick={() => void decide(fact.id, "approve")}
                            >
                              Approve
                            </button>
                          ) : (
                            <button
                              type="button"
                              className="min-h-11 rounded-sm border border-shell-700 px-2 text-xs"
                              onClick={() => void decide(fact.id, "unapprove")}
                            >
                              Return to draft
                            </button>
                          )}
                          <button
                            type="button"
                            className="min-h-11 rounded-sm border border-shell-700 px-2 text-xs"
                            onClick={() => void decide(fact.id, "reject")}
                          >
                            Reject
                          </button>
                        </div>
                      ) : null}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
