import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";

export default function PrivacyDraftPage() {
  return (
    <div className="flex min-h-screen flex-col bg-shell-950 text-ink-100">
      <AppHeader activePage="account" />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 text-sm leading-6 text-ink-300">
        <p className="text-xs font-semibold tracking-wide text-plasma-400 uppercase">
          Draft, pending lawyer review
        </p>
        <h2 className="mt-2 text-lg font-semibold text-ink-100">Privacy draft</h2>
        <p className="mt-3">
          This is not a finished privacy policy and not legal advice. Do not
          treat it as one until a lawyer has reviewed it. Trainermon does not
          charge money yet.
        </p>
        <h3 className="mt-6 font-medium text-ink-100">Who it is for</h3>
        <p className="mt-2">
          Accounts are for people aged 13 and over. We ask you to confirm that
          at sign-up and we store that you confirmed it. We do not ask for a
          birth date. If you are under 13, do not create an account.
        </p>
        <h3 className="mt-6 font-medium text-ink-100">What we store</h3>
        <p className="mt-2">
          Email, a password hash, trainer name, trainer level, team, an
          optional city, an optional friend code, and the want and have rows
          you type. We also store the timezone your browser already reports,
          so a later raid hour can use it. We do not ask you to pick a
          timezone, we do not read a Pokémon GO account, and we do not collect
          GPS. City is whatever you type later, and it can stay blank.
        </p>
        <h3 className="mt-6 font-medium text-ink-100">Who else sees it</h3>
        <p className="mt-2">
          Other trainers can see your trainer name, city, and the Pokémon that
          overlap their lists. They do not see your email or your friend code.
          Friend codes stay on your own account unless a later feature, which
          is not built, shows an opted-in code inside a raid lobby.
        </p>
        <h3 className="mt-6 font-medium text-ink-100">Children</h3>
        <p className="mt-2">
          The US COPPA rule, as amended, is in force from 22 April 2026. The
          simplest way to meet it is not to offer the service to anyone under
          13, which is the rule this draft uses. We do not knowingly keep
          information from under 13, and we do not profile children.
        </p>
        <p className="mt-2">
          In Canada, the Office of the Privacy Commissioner published a
          Children&apos;s Privacy Code on 20 October 2026. It expects parental
          consent for children under 13, privacy by default, and no profiling
          of children. This draft does not add a parental-consent flow. It
          refuses under-13 accounts instead. A lawyer still has to confirm
          that this is enough.
        </p>
        <h3 className="mt-6 font-medium text-ink-100">Other companies</h3>
        <p className="mt-2">
          The app is hosted for us. The assistant, when it is used, sends the
          question to the configured model provider. Curation drafts do the
          same with text an admin pastes. Billing is not turned on. When it
          is, the payment company would be named here. We do not sell personal
          information.
        </p>
        <p className="mt-6">
          <Link href="/terms" className="underline">
            Terms draft
          </Link>
        </p>
      </main>
    </div>
  );
}
