import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";

export default function TermsDraftPage() {
  return (
    <div className="flex min-h-screen flex-col bg-shell-950 text-ink-100">
      <AppHeader activePage="account" />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 text-sm leading-6 text-ink-300">
        <p className="text-xs font-semibold tracking-wide text-plasma-400 uppercase">
          Draft, pending lawyer review
        </p>
        <h2 className="mt-2 text-lg font-semibold text-ink-100">Terms draft</h2>
        <p className="mt-3">
          This is not a finished terms of service and not legal advice. A
          refund sentence is intentionally blank until charging is approved.
        </p>
        <h3 className="mt-6 font-medium text-ink-100">Not the official game</h3>
        <p className="mt-2">
          Trainermon is not affiliated with Nintendo, The Pokémon Company, Game
          Freak, Scopely, or Niantic. Pokémon names are used so you can find
          the creatures you mean.
        </p>
        <h3 className="mt-6 font-medium text-ink-100">Your lists</h3>
        <p className="mt-2">
          You type your own want and have rows. You do not connect a game
          account. Selling or trading accounts is not allowed, and the app
          will not help you do it. You let Trainermon store and show the rows
          you submit, including to other trainers when a list overlaps.
        </p>
        <h3 className="mt-6 font-medium text-ink-100">Age</h3>
        <p className="mt-2">
          You must be 13 or older. If you are under 13, you may not create an
          account.
        </p>
        <h3 className="mt-6 font-medium text-ink-100">Accuracy</h3>
        <p className="mt-2">
          Catalog flags and assistant answers can be wrong. A curated row shows
          the date it was checked and keeps a source link for the admin who
          approved it. That is not a promise the game still works that way.
        </p>
        <h3 className="mt-6 font-medium text-ink-100">Money</h3>
        <p className="mt-2">
          There is no charge in this build. Refunds: not set. Do not take
          payment until this sentence is replaced and a lawyer has reviewed
          these drafts.
        </p>
        <p className="mt-6">
          <Link href="/privacy" className="underline">
            Privacy draft
          </Link>
        </p>
      </main>
    </div>
  );
}
