"use client";

import Link from "next/link";
import { useAppName } from "@/lib/app-name";

type AppHeaderProps = {
  activePage: "chat" | "team" | "account" | "lists" | "trades" | "explorer";
};

export function AppHeader({ activePage }: AppHeaderProps) {
  const appName = useAppName();
  return (
    <header className={activePage === "chat" ? "chat-header" : "border-b border-shell-800 bg-shell-900"}>
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <div className="flex items-baseline gap-2">
          <span aria-hidden className="size-2 rounded-full bg-plasma-500" />
          <h1 className="text-sm font-semibold tracking-wide text-ink-100">{appName}</h1>
        </div>

        <nav aria-label="Main navigation" className="flex items-center gap-1 text-xs">
          <Link
            href="/"
            aria-current={activePage === "chat" ? "page" : undefined}
            className={`rounded-sm px-2 py-1 ${activePage === "chat" ? "bg-shell-800 text-ink-100" : "text-ink-500 hover:text-ink-100"}`}
          >
            Assistant
          </Link>
          <Link
            href="/account"
            aria-current={activePage === "account" ? "page" : undefined}
            className={`rounded-sm px-2 py-1 ${activePage === "account" ? "bg-shell-800 text-ink-100" : "text-ink-500 hover:text-ink-100"}`}
          >
            Account
          </Link>
          <Link
            href="/lists"
            aria-current={activePage === "lists" ? "page" : undefined}
            className={`rounded-sm px-2 py-1 ${activePage === "lists" ? "bg-shell-800 text-ink-100" : "text-ink-500 hover:text-ink-100"}`}
          >
            Lists
          </Link>
          <Link
            href="/trades"
            aria-current={activePage === "trades" ? "page" : undefined}
            className={`rounded-sm px-2 py-1 ${activePage === "trades" ? "bg-shell-800 text-ink-100" : "text-ink-500 hover:text-ink-100"}`}
          >
            Trades
          </Link>
          <Link
            href="/team"
            aria-current={activePage === "team" ? "page" : undefined}
            className={`rounded-sm px-2 py-1 ${activePage === "team" ? "bg-shell-800 text-ink-100" : "text-ink-500 hover:text-ink-100"}`}
          >
            Team builder
          </Link>
        </nav>

        <div className="ml-auto flex items-center gap-2 text-xs">
          <span className="text-ink-500">Model</span>
          <span className="rounded-sm border border-shell-700 bg-shell-800 px-2 py-1 font-mono text-ink-300">
            DeepSeek Flash
          </span>
        </div>
      </div>
    </header>
  );
}
