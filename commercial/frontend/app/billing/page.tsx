"use client";

import { useEffect, useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { communityFetch, type Profile } from "@/lib/community";

type Billing = {
  plan: "free" | "paid";
  raid_priority: string;
  assistant_cap: number;
  portal_url: string;
  test_mode: boolean;
  monthly_usd: string;
  yearly_usd: string;
};

export default function BillingPage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [billing, setBilling] = useState<Billing | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    communityFetch<Profile>("/api/me")
      .then((me) => {
        setProfile(me);
        return communityFetch<Billing>("/api/billing");
      })
      .then(setBilling)
      .catch(() => {
        setProfile(null);
        setBilling(null);
      });
  }, []);

  const checkout = (interval: "month" | "year") => {
    setError(null);
    communityFetch<{ url: string }>("/api/billing/checkout", {
      method: "POST",
      body: JSON.stringify({ interval }),
    })
      .then((body) => {
        window.location.href = body.url;
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Request failed.");
      });
  };

  return (
    <div className="min-h-screen bg-shell-950 text-ink-100">
      <AppHeader activePage="billing" />
      <main className="mx-auto flex max-w-xl flex-col gap-4 px-4 py-6">
        <h2 className="text-lg font-semibold">Paid</h2>
        <p className="text-sm text-ink-400">
          Test mode only. Checkout is a Lemon Squeezy test page. This app
          does not charge a card, and a live key is refused.
        </p>
        {profile && billing ? (
          <>
            <p className="text-sm">
              {profile.trainer_name} is on {billing.plan}. Raid priority is{" "}
              {billing.raid_priority}. Assistant cap is {billing.assistant_cap}{" "}
              runs a day.
            </p>
            <p className="text-sm text-ink-300">
              ${billing.monthly_usd} a month, or ${billing.yearly_usd} a year.
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                className="rounded-sm bg-plasma-500 px-3 py-1 text-sm text-shell-950"
                onClick={() => checkout("month")}
              >
                Monthly test checkout
              </button>
              <button
                type="button"
                className="rounded-sm border border-shell-700 px-3 py-1 text-sm"
                onClick={() => checkout("year")}
              >
                Yearly test checkout
              </button>
            </div>
            {billing.portal_url ? (
              <a className="text-sm text-plasma-300" href={billing.portal_url}>
                Customer portal
              </a>
            ) : null}
          </>
        ) : (
          <p className="text-sm text-ink-500">Sign in to see Paid.</p>
        )}
        {error ? <p className="text-sm text-red-300">{error}</p> : null}
      </main>
    </div>
  );
}
