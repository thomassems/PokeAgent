"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { communityFetch, type Profile } from "@/lib/community";

type Lobby = {
  id: number;
  species_name: string;
  city: string;
  starts_at: string;
  status: string;
  host_name: string;
  seats: number;
  max_seats: number;
  limit_note: string;
  host_friend_code?: string;
};

type QueueRow = {
  user_id: number;
  trainer_name: string;
  raid_priority: string;
};

export default function RaidsPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [lobbies, setLobbies] = useState<Lobby[]>([]);
  const [speciesId, setSpeciesId] = useState("mewtwo");
  const [startsAt, setStartsAt] = useState("2026-11-21T18:00");
  const [city, setCity] = useState("");
  const [queue, setQueue] = useState<QueueRow[]>([]);
  const [openId, setOpenId] = useState<number | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    communityFetch<{ lobbies: Lobby[] }>("/api/raids")
      .then((body) => setLobbies(body.lobbies))
      .catch(() => setLobbies([]));
  };

  useEffect(() => {
    communityFetch<Profile>("/api/me")
      .then(setProfile)
      .catch(() => setProfile(null));
    load();
  }, []);

  return (
    <div className="min-h-screen bg-shell-950 text-ink-100">
      <AppHeader activePage="raids" />
      <main className="mx-auto flex max-w-xl flex-col gap-4 px-4 py-6">
        <h2 className="text-lg font-semibold">Remote raids</h2>
        <p className="text-sm text-ink-400">
          No chat. Friend codes are shown only after you opt in and the host
          accepts you. Paid is offered ahead of Free. Hosts are not paid, and
          passes are not sold. The remote-raid limit is yours to follow.
        </p>
        {profile ? (
          <button
            type="button"
            className="w-fit rounded-sm border border-shell-700 px-2 py-1 text-xs"
            onClick={() => {
              setError(null);
              communityFetch("/api/raids/opt-in", {
                method: "POST",
                body: JSON.stringify({ enabled: true }),
              })
                .then(() => setNotice("Opted in. Your code stays hidden until a host accepts you."))
                .catch((err: unknown) => {
                  setError(err instanceof Error ? err.message : "Request failed.");
                });
            }}
          >
            Opt in with my friend code
          </button>
        ) : (
          <p className="text-sm text-ink-500">Sign in to host or join.</p>
        )}
        <form
          className="flex flex-col gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            setError(null);
            communityFetch<Lobby>("/api/raids", {
              method: "POST",
              body: JSON.stringify({
                species_id: speciesId,
                starts_at: new Date(startsAt).toISOString(),
                city,
              }),
            })
              .then(() => load())
              .catch((err: unknown) => {
                setError(err instanceof Error ? err.message : "Request failed.");
              });
          }}
        >
          <input
            className="rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
            value={speciesId}
            onChange={(event) => setSpeciesId(event.target.value)}
            placeholder="species id"
          />
          <input
            type="datetime-local"
            className="rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
            value={startsAt}
            onChange={(event) => setStartsAt(event.target.value)}
          />
          <input
            className="rounded-sm border border-shell-700 bg-shell-950 px-2 py-1 text-sm"
            value={city}
            placeholder="City, optional. Blank uses yours, or Toronto."
            onChange={(event) => setCity(event.target.value)}
          />
          <button
            type="submit"
            className="w-fit rounded-sm bg-plasma-500 px-2 py-1 text-xs text-shell-950"
          >
            Host a lobby
          </button>
        </form>
        <ul className="flex flex-col gap-2">
          {lobbies.map((lobby) => (
            <li
              key={lobby.id}
              className="rounded-md border border-shell-800 bg-shell-900 p-3 text-sm"
            >
              <p>
                {lobby.species_name} · {lobby.city} · {lobby.status} ·{" "}
                {lobby.seats}/{lobby.max_seats}
              </p>
              <p className="text-xs text-ink-400">
                Host {lobby.host_name}. {lobby.limit_note}
              </p>
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  className="rounded-sm border border-shell-700 px-2 py-1 text-xs"
                  onClick={() => {
                    setError(null);
                    communityFetch(`/api/raids/${lobby.id}/join`, {
                      method: "POST",
                      body: "{}",
                    })
                      .then(() => setNotice("Asked for a seat."))
                      .catch((err: unknown) => {
                        setError(
                          err instanceof Error ? err.message : "Request failed.",
                        );
                      });
                  }}
                >
                  Ask for a seat
                </button>
                <button
                  type="button"
                  className="rounded-sm border border-shell-700 px-2 py-1 text-xs"
                  onClick={() => {
                    setOpenId(lobby.id);
                    communityFetch<{ queue: QueueRow[] }>(
                      `/api/raids/${lobby.id}/queue`,
                    )
                      .then((body) => setQueue(body.queue))
                      .catch(() => setQueue([]));
                  }}
                >
                  Host queue
                </button>
              </div>
              {openId === lobby.id
                ? queue.map((row) => (
                    <p key={row.user_id} className="mt-2 text-xs">
                      {row.trainer_name} · {row.raid_priority}{" "}
                      <button
                        type="button"
                        className="underline"
                        onClick={() => {
                          communityFetch<{ friend_code: string }>(
                            `/api/raids/${lobby.id}/accept`,
                            {
                              method: "POST",
                              body: JSON.stringify({ user_id: row.user_id }),
                            },
                          )
                            .then((body) => {
                              setNotice(`Friend code ${body.friend_code}`);
                              load();
                            })
                            .catch((err: unknown) => {
                              setError(
                                err instanceof Error
                                  ? err.message
                                  : "Request failed.",
                              );
                            });
                        }}
                      >
                        Accept
                      </button>
                    </p>
                  ))
                : null}
            </li>
          ))}
        </ul>
        {notice ? <p className="text-sm text-ink-300">{notice}</p> : null}
        {error ? <p className="text-sm text-red-300">{error}</p> : null}
      </main>
    </div>
  );
}
