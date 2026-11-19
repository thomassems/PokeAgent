"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { useAppName } from "@/lib/app-name";
import { communityFetch, type AccountConfig, type Profile } from "@/lib/community";

export default function AccountPage() {
  const appName = useAppName();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [mode, setMode] = useState<"login" | "register">("register");
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [trainerName, setTrainerName] = useState("");
  const [city, setCity] = useState("Toronto");
  const [friendCode, setFriendCode] = useState("");
  const [level, setLevel] = useState("");
  const [team, setTeam] = useState("");
  const [timezone, setTimezone] = useState("America/Toronto");
  const [config, setConfig] = useState<AccountConfig | null>(null);
  const [ageConfirmed, setAgeConfirmed] = useState(false);

  useEffect(() => {
    communityFetch<AccountConfig>("/api/config")
      .then(setConfig)
      .catch(() => setConfig(null));
    communityFetch<Profile>("/api/me")
      .then((me) => {
        setProfile(me);
        setTrainerName(me.trainer_name);
        setCity(me.city);
        setFriendCode(me.friend_code);
        setLevel(me.trainer_level == null ? "" : String(me.trainer_level));
        setTeam(me.team);
        if (me.timezone) setTimezone(me.timezone);
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
              trainer_level: Number(level),
              team,
              timezone,
              age_confirmed: ageConfirmed,
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
      setLevel(me.trainer_level == null ? "" : String(me.trainer_level));
      setTeam(me.team);
      if (me.timezone) setTimezone(me.timezone);
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
          trainer_level: Number(level),
          team,
          timezone,
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
          {appName} does not read Pokémon GO accounts. You type your own lists. Selling
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
            <TrainerFields
              config={config}
              trainerName={trainerName}
              setTrainerName={setTrainerName}
              team={team}
              setTeam={setTeam}
              level={level}
              setLevel={setLevel}
              city={city}
              setCity={setCity}
              timezone={timezone}
              setTimezone={setTimezone}
              friendCode={friendCode}
              setFriendCode={setFriendCode}
              region={profile.region}
            />
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
              <TrainerFields
                config={config}
                trainerName={trainerName}
                setTrainerName={setTrainerName}
                team={team}
                setTeam={setTeam}
                level={level}
                setLevel={setLevel}
                city={city}
                setCity={setCity}
                timezone={timezone}
                setTimezone={setTimezone}
                friendCode={friendCode}
                setFriendCode={setFriendCode}
                region=""
              />
            )}
            {mode === "register" ? (
              <label className="flex items-start gap-2 text-sm text-ink-300">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={ageConfirmed}
                  onChange={(event) => setAgeConfirmed(event.target.checked)}
                />
                <span>
                  I am 13 or older. {appName} does not offer accounts to anyone
                  younger. Read the{" "}
                  <Link href="/privacy" className="underline">
                    privacy draft
                  </Link>{" "}
                  and{" "}
                  <Link href="/terms" className="underline">
                    terms draft
                  </Link>
                  .
                </span>
              </label>
            ) : null}
            <button type="submit" className="rounded-sm bg-plasma-600 px-3 py-1 text-sm text-ink-100">
              {mode === "register" ? "Create account" : "Sign in"}
            </button>
          </form>
        )}
      </main>
    </div>
  );
}

function TrainerFields({
  config,
  trainerName,
  setTrainerName,
  team,
  setTeam,
  level,
  setLevel,
  city,
  setCity,
  timezone,
  setTimezone,
  friendCode,
  setFriendCode,
  region,
}: {
  config: AccountConfig | null;
  trainerName: string;
  setTrainerName: (value: string) => void;
  team: string;
  setTeam: (value: string) => void;
  level: string;
  setLevel: (value: string) => void;
  city: string;
  setCity: (value: string) => void;
  timezone: string;
  setTimezone: (value: string) => void;
  friendCode: string;
  setFriendCode: (value: string) => void;
  region: string;
}) {
  const inputClass =
    "mt-1 w-full rounded-sm border border-shell-700 bg-shell-900 px-2 py-1 text-ink-100";
  const chosen = config?.timezones.find((zone) => zone.id === timezone);
  return (
    <>
      <label className="block text-sm text-ink-300">
        Trainer name
        <input
          className={inputClass}
          value={trainerName}
          onChange={(event) => setTrainerName(event.target.value)}
        />
      </label>
      <label className="block text-sm text-ink-300">
        Team
        <select
          className={inputClass}
          value={team}
          onChange={(event) => setTeam(event.target.value)}
        >
          <option value="">Choose a team</option>
          {(config?.teams ?? []).map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
      </label>
      <label className="block text-sm text-ink-300">
        Trainer level ({config?.trainer_level_min ?? 1}-{config?.trainer_level_max ?? 80})
        <input
          className={inputClass}
          inputMode="numeric"
          value={level}
          onChange={(event) => setLevel(event.target.value.replace(/[^\d]/g, ""))}
        />
      </label>
      <label className="block text-sm text-ink-300">
        City
        <input className={inputClass} value={city} onChange={(event) => setCity(event.target.value)} />
      </label>
      <label className="block text-sm text-ink-300">
        Region and timezone
        <select
          className={inputClass}
          value={timezone}
          onChange={(event) => setTimezone(event.target.value)}
        >
          {(config?.timezones ?? []).map((zone) => (
            <option key={zone.id} value={zone.id}>
              {zone.region}: {zone.label}
            </option>
          ))}
        </select>
      </label>
      <p className="text-xs text-ink-500">
        Saved for later raid hours. Current region: {region || chosen?.region || "not set yet"}.
      </p>
      <label className="block text-sm text-ink-300">
        Friend code (optional)
        <input
          className={inputClass}
          value={friendCode}
          onChange={(event) => setFriendCode(event.target.value)}
          inputMode="numeric"
        />
      </label>
      <p className="text-xs text-ink-500">
        Optional, 12 digits or blank. It stays on your account.
        {config?.share_friend_codes
          ? " The share switch is on, and this build still does not show the code to other trainers."
          : " Other trainers do not see it."}
      </p>
    </>
  );
}
