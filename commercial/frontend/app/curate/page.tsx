"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { communityFetch, type Profile } from "@/lib/community";

type Report = {
  id: number;
  species_id: string;
  tag: string;
  note: string;
  trainer_name: string;
  created_at: string;
};

type Fact = {
  id: number;
  species_id: string;
  kind: string;
  value: string;
  source_url: string;
  verified_at: string;
  verified_by: string;
  status: string;
  notes: string;
};

export default function CuratePage() {
  const [profile, setProfile] = useState<Profile | null | undefined>(undefined);
  const [facts, setFacts] = useState<Fact[]>([]);
  const [denied, setDenied] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pasted, setPasted] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [verifiedAt, setVerifiedAt] = useState("2026-11-18");
  const [reports, setReports] = useState<Report[]>([]);

  const load = () => {
    communityFetch<{ facts: Fact[] }>("/api/curation")
      .then((body) => {
        setFacts(body.facts);
        setDenied(null);
      })
      .catch((err: unknown) => {
        setFacts([]);
        setDenied(err instanceof Error ? err.message : "Request failed.");
      });
    communityFetch<{ reports: Report[] }>("/api/reports")
      .then((body) => setReports(body.reports))
      .catch(() => setReports([]));
  };

  useEffect(() => {
    communityFetch<Profile>("/api/me")
      .then(setProfile)
      .catch(() => setProfile(null));
    load();
  }, []);

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

  const decide = async (id: number, status: "approve" | "reject") => {
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

  const drafts = facts.filter((fact) => fact.status === "draft");

  return (
    <div className="flex min-h-screen flex-col bg-shell-950 text-ink-100">
      <AppHeader activePage="curate" />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
        <div>
          <h2 className="text-lg font-semibold">Curate</h2>
          <p className="mt-1 text-sm text-ink-400">
            Paste an announcement. The model drafts rows from that text only.
            Nothing is public until you approve it. Every row keeps the source
            link and the date you checked it.
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
              className="w-fit rounded-sm bg-plasma-500 px-3 py-1 text-sm text-shell-950"
            >
              Draft rows
            </button>
          </form>
        ) : null}
        <section>
          <h3 className="text-sm font-medium">Reports</h3>
          <p className="mt-1 text-xs text-ink-500">
            Confirming opens a draft. It does not change Explorer until you
            approve that draft below.
          </p>
          {reports.length === 0 ? (
            <p className="mt-2 text-sm text-ink-500">No open reports.</p>
          ) : (
            <ul className="mt-2 flex flex-col gap-2">
              {reports.map((report) => (
                <li
                  key={report.id}
                  className="rounded-md border border-shell-800 bg-shell-900 p-3 text-sm"
                >
                  <p>
                    {report.species_id} · {report.tag} · {report.trainer_name}
                  </p>
                  <p className="text-xs text-ink-400">{report.note}</p>
                  <form
                    className="mt-2 flex flex-col gap-2"
                    onSubmit={(event) => {
                      event.preventDefault();
                      const form = event.currentTarget;
                      const data = new FormData(form);
                      setError(null);
                      communityFetch(`/api/reports/${report.id}/confirm`, {
                        method: "POST",
                        body: JSON.stringify({
                          kind: String(data.get("kind") || ""),
                          value: String(data.get("value") || ""),
                          source_url: String(data.get("source_url") || ""),
                          verified_at: String(data.get("verified_at") || ""),
                        }),
                      })
                        .then(() => load())
                        .catch((err: unknown) => {
                          setError(
                            err instanceof Error ? err.message : "Request failed.",
                          );
                        });
                    }}
                  >
                    <div className="flex flex-wrap gap-2">
                      <input
                        name="kind"
                        placeholder="kind"
                        className="w-28 rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-xs"
                      />
                      <input
                        name="value"
                        placeholder="value"
                        className="w-32 rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-xs"
                      />
                      <input
                        name="verified_at"
                        defaultValue="2026-11-20"
                        className="w-28 rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-xs"
                      />
                    </div>
                    <input
                      name="source_url"
                      placeholder="https:// source"
                      className="rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-xs"
                    />
                    <div className="flex gap-2">
                      <button
                        type="submit"
                        className="rounded-sm bg-plasma-500 px-2 py-1 text-xs text-shell-950"
                      >
                        Open draft
                      </button>
                      <button
                        type="button"
                        className="rounded-sm border border-shell-700 px-2 py-1 text-xs"
                        onClick={() => {
                          setError(null);
                          communityFetch(`/api/reports/${report.id}/reject`, {
                            method: "POST",
                            body: "{}",
                          })
                            .then(() => load())
                            .catch((err: unknown) => {
                              setError(
                                err instanceof Error
                                  ? err.message
                                  : "Request failed.",
                              );
                            });
                        }}
                      >
                        Reject
                      </button>
                    </div>
                  </form>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section>
          <h3 className="text-sm font-medium">Drafts</h3>
          {drafts.length === 0 ? (
            <p className="mt-2 text-sm text-ink-500">No drafts waiting.</p>
          ) : (
            <ul className="mt-2 flex flex-col gap-2">
              {drafts.map((fact) => (
                <li
                  key={fact.id}
                  className="rounded-md border border-shell-800 bg-shell-900 p-3 text-sm"
                >
                  <p>
                    {fact.species_id} · {fact.kind} · {fact.value}
                  </p>
                  <p className="text-xs text-ink-400">
                    {fact.verified_at} · {fact.source_url}
                  </p>
                  <div className="mt-2 flex gap-2">
                    <button
                      type="button"
                      className="rounded-sm bg-plasma-500 px-2 py-1 text-xs text-shell-950"
                      onClick={() => void decide(fact.id, "approve")}
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      className="rounded-sm border border-shell-700 px-2 py-1 text-xs"
                      onClick={() => void decide(fact.id, "reject")}
                    >
                      Reject
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section>
          <h3 className="text-sm font-medium">Already approved</h3>
          <ul className="mt-2 flex flex-col gap-2">
            {facts
              .filter((fact) => fact.status === "approved")
              .slice(0, 6)
              .map((fact) => (
                <li
                  key={fact.id}
                  className="rounded-md border border-shell-800 bg-shell-900 p-3 text-sm"
                >
                  <p>
                    {fact.species_id} · {fact.kind} · {fact.value}
                  </p>
                  <p className="break-all text-xs text-ink-400">
                    Checked {fact.verified_at} · {fact.source_url}
                  </p>
                </li>
              ))}
          </ul>
        </section>
      </main>
    </div>
  );
}
