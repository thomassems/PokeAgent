"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { useAppName } from "@/lib/app-name";
import { communityFetch, type AccountConfig, type Profile } from "@/lib/community";

function browserZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

const inputClass =
  "mt-1 w-full rounded-sm border border-shell-700 bg-shell-900 px-2 py-1 text-ink-100";

export default function AccountPage() {
  const appName = useAppName();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [mode, setMode] = useState<"login" | "register">("register");
  const [step, setStep] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [trainerName, setTrainerName] = useState("");
  const [city, setCity] = useState("");
  const [friendCode, setFriendCode] = useState("");
  const [level, setLevel] = useState("");
  const [team, setTeam] = useState("");
  const [config, setConfig] = useState<AccountConfig | null>(null);
  const [ageConfirmed, setAgeConfirmed] = useState(false);

  const applyProfile = (me: Profile) => {
    setProfile(me);
    setTrainerName(me.trainer_name);
    setCity(me.city);
    setFriendCode(me.friend_code);
    setLevel(me.trainer_level == null ? "" : String(me.trainer_level));
    setTeam(me.team);
  };

  useEffect(() => {
    communityFetch<AccountConfig>("/api/config")
      .then(setConfig)
      .catch(() => setConfig(null));
    communityFetch<Profile>("/api/me")
      .then(applyProfile)
      .catch(() => setProfile(null));
  }, []);

  const register = async (code: string) => {
    setError(null);
    try {
      const me = await communityFetch<Profile>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          trainer_name: trainerName,
          city: "",
          friend_code: code,
          trainer_level: Number(level),
          team,
          timezone: browserZone(),
          age_confirmed: ageConfirmed,
        }),
      });
      applyProfile(me);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    }
  };

  const login = async () => {
    setError(null);
    try {
      const me = await communityFetch<Profile>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      applyProfile(me);
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
        }),
      });
      applyProfile(me);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    }
  };

  const signOut = async () => {
    await communityFetch("/api/auth/logout", { method: "POST", body: "{}" });
    setProfile(null);
    setPassword("");
    setStep(1);
  };

  const continueAccount = () => {
    setError(null);
    if (!email.includes("@") || password.length < 8) {
      setError("Enter an email and a password of at least 8 characters.");
      return;
    }
    if (!ageConfirmed) {
      setError("Trainermon is for trainers aged 13 and over.");
      return;
    }
    setStep(2);
  };

  const continueTrainer = () => {
    setError(null);
    const parsed = Number(level);
    const min = config?.trainer_level_min ?? 1;
    const max = config?.trainer_level_max ?? 80;
    if (!trainerName.trim() || !team || parsed < min || parsed > max) {
      setError(`Enter your trainer name, team, and a level from ${min} to ${max}.`);
      return;
    }
    setStep(3);
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
            <ProfileFields
              config={config}
              trainerName={trainerName}
              setTrainerName={setTrainerName}
              team={team}
              setTeam={setTeam}
              level={level}
              setLevel={setLevel}
              city={city}
              setCity={setCity}
              friendCode={friendCode}
              setFriendCode={setFriendCode}
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
          <div className="space-y-3">
            <div className="flex gap-2 text-sm">
              <button
                type="button"
                className={mode === "register" ? "text-ink-100" : "text-ink-500"}
                onClick={() => {
                  setMode("register");
                  setStep(1);
                  setError(null);
                }}
              >
                Create account
              </button>
              <button
                type="button"
                className={mode === "login" ? "text-ink-100" : "text-ink-500"}
                onClick={() => {
                  setMode("login");
                  setError(null);
                }}
              >
                Sign in
              </button>
            </div>
            {mode === "login" ? (
              <form
                className="space-y-3"
                onSubmit={(event) => {
                  event.preventDefault();
                  void login();
                }}
              >
                <EmailPassword
                  email={email}
                  setEmail={setEmail}
                  password={password}
                  setPassword={setPassword}
                  autoComplete="current-password"
                />
                <button type="submit" className="rounded-sm bg-plasma-600 px-3 py-1 text-sm text-ink-100">
                  Sign in
                </button>
              </form>
            ) : (
              <form
                className="space-y-3"
                onSubmit={(event) => {
                  event.preventDefault();
                  if (step === 1) continueAccount();
                  else if (step === 2) continueTrainer();
                  else void register(friendCode);
                }}
              >
                <p className="text-xs tracking-wide text-ink-500 uppercase">
                  Step {step} of 3
                </p>
                {step === 1 ? (
                  <>
                    <h3 className="text-base font-medium text-ink-100">Create your account</h3>
                    <EmailPassword
                      email={email}
                      setEmail={setEmail}
                      password={password}
                      setPassword={setPassword}
                      autoComplete="new-password"
                    />
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
                    <button type="submit" className="rounded-sm bg-plasma-600 px-3 py-1 text-sm text-ink-100">
                      Continue
                    </button>
                  </>
                ) : null}
                {step === 2 ? (
                  <>
                    <h3 className="text-base font-medium text-ink-100">Your trainer</h3>
                    <label className="block text-sm text-ink-300">
                      Trainer name
                      <input
                        className={inputClass}
                        value={trainerName}
                        onChange={(event) => setTrainerName(event.target.value)}
                      />
                    </label>
                    <TeamField config={config} team={team} setTeam={setTeam} />
                    <LevelField config={config} level={level} setLevel={setLevel} />
                    <div className="flex gap-2">
                      <button type="button" className="rounded-sm px-3 py-1 text-sm text-ink-300" onClick={() => setStep(1)}>
                        Back
                      </button>
                      <button type="submit" className="rounded-sm bg-plasma-600 px-3 py-1 text-sm text-ink-100">
                        Continue
                      </button>
                    </div>
                  </>
                ) : null}
                {step === 3 ? (
                  <>
                    <h3 className="text-base font-medium text-ink-100">Friend code</h3>
                    <p className="text-sm text-ink-400">
                      Optional. You can skip this and add it later. Other trainers
                      do not see it.
                    </p>
                    <label className="block text-sm text-ink-300">
                      Friend code
                      <input
                        className={inputClass}
                        value={friendCode}
                        onChange={(event) => setFriendCode(event.target.value)}
                        inputMode="numeric"
                      />
                    </label>
                    <div className="flex gap-2">
                      <button type="button" className="rounded-sm px-3 py-1 text-sm text-ink-300" onClick={() => setStep(2)}>
                        Back
                      </button>
                      <button
                        type="button"
                        className="rounded-sm px-3 py-1 text-sm text-ink-300"
                        onClick={() => {
                          setFriendCode("");
                          void register("");
                        }}
                      >
                        Skip
                      </button>
                      <button type="submit" className="rounded-sm bg-plasma-600 px-3 py-1 text-sm text-ink-100">
                        Finish
                      </button>
                    </div>
                  </>
                ) : null}
              </form>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function EmailPassword({
  email,
  setEmail,
  password,
  setPassword,
  autoComplete,
}: {
  email: string;
  setEmail: (value: string) => void;
  password: string;
  setPassword: (value: string) => void;
  autoComplete: string;
}) {
  return (
    <>
      <label className="block text-sm text-ink-300">
        Email
        <input
          className={inputClass}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
        />
      </label>
      <label className="block text-sm text-ink-300">
        Password
        <input
          type="password"
          className={inputClass}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete={autoComplete}
        />
      </label>
    </>
  );
}

function TeamField({
  config,
  team,
  setTeam,
}: {
  config: AccountConfig | null;
  team: string;
  setTeam: (value: string) => void;
}) {
  return (
    <label className="block text-sm text-ink-300">
      Team
      <select className={inputClass} value={team} onChange={(event) => setTeam(event.target.value)}>
        <option value="">Choose a team</option>
        {(config?.teams ?? []).map((item) => (
          <option key={item.id} value={item.id}>
            {item.name}
          </option>
        ))}
      </select>
    </label>
  );
}

function LevelField({
  config,
  level,
  setLevel,
}: {
  config: AccountConfig | null;
  level: string;
  setLevel: (value: string) => void;
}) {
  return (
    <label className="block text-sm text-ink-300">
      Trainer level ({config?.trainer_level_min ?? 1}-{config?.trainer_level_max ?? 80})
      <input
        className={inputClass}
        inputMode="numeric"
        value={level}
        onChange={(event) => setLevel(event.target.value.replace(/[^\d]/g, ""))}
      />
    </label>
  );
}

function ProfileFields({
  config,
  trainerName,
  setTrainerName,
  team,
  setTeam,
  level,
  setLevel,
  city,
  setCity,
  friendCode,
  setFriendCode,
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
  friendCode: string;
  setFriendCode: (value: string) => void;
}) {
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
      <TeamField config={config} team={team} setTeam={setTeam} />
      <LevelField config={config} level={level} setLevel={setLevel} />
      <label className="block text-sm text-ink-300">
        City
        <input
          className={inputClass}
          value={city}
          placeholder="Used when you search trades"
          onChange={(event) => setCity(event.target.value)}
        />
      </label>
      <p className="text-xs text-ink-500">
        Optional. Trade search uses this city. You can leave it blank until you need it.
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
