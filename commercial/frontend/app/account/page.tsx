"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { communityFetch, type Profile } from "@/lib/community";

export default function AccountPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [mode, setMode] = useState<"login" | "register">("register");
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [trainerName, setTrainerName] = useState("");
  const [city, setCity] = useState("Toronto");
  const [friendCode, setFriendCode] = useState("");

  useEffect(() => {
    communityFetch<Profile>("/api/me")
      .then((me) => {
        setProfile(me);
        setTrainerName(me.trainer_name);
        setCity(me.city);
        setFriendCode(me.friend_code);
      })
      .catch(() => setProfile(null));
  }, []);

  const submit = async () => {
    setError(null);
    try {
      const path = mode === "register" ? "/api/auth/register" : "/api/auth/login";
      const payload =
        mode === "register"
          ? {
              email,
              password,
              trainer_name: trainerName,
              city,
              friend_code: friendCode,
            }
          : { email, password };
      const me = await communityFetch<Profile>(path, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setProfile(me);
      setTrainerName(me.trainer_name);
      setCity(me.city);
      setFriendCode(me.friend_code);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    }
  };

  const save = async () => {
    setError(null);
    try {
      const me = await communityFetch<Profile>("/api/me", {
        method: "PATCH",
        body: JSON.stringify({
          trainer_name: trainerName,
          city,
          friend_code: friendCode,
        }),
      });
      setProfile(me);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    }
  };

  const signOut = async () => {
    await communityFetch("/api/auth/logout", { method: "POST", body: "{}" });
    setProfile(null);
    setPassword("");
  };

  return (
    <div className="min-h-screen">
      <AppHeader activePage="account" />
      <main className="mx-auto max-w-lg space-y-4 px-4 py-8">
        <h2 className="text-lg font-semibold text-ink-100">Account</h2>
        <p className="text-sm text-ink-300">
          Trainermon does not read Pokémon GO accounts. You type your own lists. Selling
          or trading accounts is not part of this app.
        </p>
        {error && <p className="text-sm text-plasma-300">{error}</p>}
        {profile ? (
          <form
            className="space-y-3"
            onSubmit={(event) => {
              event.preventDefault();
              void save();
            }}
          >
            <p className="text-sm text-ink-300">Signed in as {profile.email}</p>
            <label className="block text-sm text-ink-300">
              Trainer name
              <input
                className="mt-1 w-full rounded-sm border border-shell-700 bg-shell-900 px-2 py-1 text-ink-100"
                value={trainerName}
                onChange={(event) => setTrainerName(event.target.value)}
              />
            </label>
            <label className="block text-sm text-ink-300">
              City
              <input
                className="mt-1 w-full rounded-sm border border-shell-700 bg-shell-900 px-2 py-1 text-ink-100"
                value={city}
                onChange={(event) => setCity(event.target.value)}
              />
            </label>
            <label className="block text-sm text-ink-300">
              Friend code
              <input
                className="mt-1 w-full rounded-sm border border-shell-700 bg-shell-900 px-2 py-1 text-ink-100"
                value={friendCode}
                onChange={(event) => setFriendCode(event.target.value)}
                inputMode="numeric"
              />
            </label>
            <p className="text-xs text-ink-500">
              Your friend code is stored and is not shown to other trainers. How people
              contact each other is not decided yet.
            </p>
            <div className="flex gap-2">
              <button type="submit" className="rounded-sm bg-plasma-600 px-3 py-1 text-sm text-ink-100">
                Save
              </button>
              <button type="button" className="rounded-sm px-3 py-1 text-sm text-ink-300" onClick={() => void signOut()}>
                Sign out
              </button>
            </div>
          </form>
        ) : (
          <form
            className="space-y-3"
            onSubmit={(event) => {
              event.preventDefault();
              void submit();
            }}
          >
            <div className="flex gap-2 text-sm">
              <button type="button" className={mode === "register" ? "text-ink-100" : "text-ink-500"} onClick={() => setMode("register")}>
                Create account
              </button>
              <button type="button" className={mode === "login" ? "text-ink-100" : "text-ink-500"} onClick={() => setMode("login")}>
                Sign in
              </button>
            </div>
            <label className="block text-sm text-ink-300">
              Email
              <input
                className="mt-1 w-full rounded-sm border border-shell-700 bg-shell-900 px-2 py-1 text-ink-100"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
              />
            </label>
            <label className="block text-sm text-ink-300">
              Password
              <input
                type="password"
                className="mt-1 w-full rounded-sm border border-shell-700 bg-shell-900 px-2 py-1 text-ink-100"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete={mode === "register" ? "new-password" : "current-password"}
              />
            </label>
            {mode === "register" && (
              <>
                <label className="block text-sm text-ink-300">
                  Trainer name
                  <input
                    className="mt-1 w-full rounded-sm border border-shell-700 bg-shell-900 px-2 py-1 text-ink-100"
                    value={trainerName}
                    onChange={(event) => setTrainerName(event.target.value)}
                  />
                </label>
                <label className="block text-sm text-ink-300">
                  City
                  <input
                    className="mt-1 w-full rounded-sm border border-shell-700 bg-shell-900 px-2 py-1 text-ink-100"
                    value={city}
                    onChange={(event) => setCity(event.target.value)}
                  />
                </label>
              </>
            )}
            <button type="submit" className="rounded-sm bg-plasma-600 px-3 py-1 text-sm text-ink-100">
              {mode === "register" ? "Create account" : "Sign in"}
            </button>
          </form>
        )}
      </main>
    </div>
  );
}
