"use client";

import Link from "next/link";
import { useState } from "react";

type PageId = "chat" | "team";

const LINKS: { href: string; id: PageId; label: string }[] = [
  { href: "/", id: "chat", label: "Chat" },
  { href: "/team", id: "team", label: "Team builder" },
];

function linkClass(active: boolean, mobile: boolean): string {
  const tone = active ? "bg-shell-800 text-ink-100" : "text-ink-500 hover:text-ink-100";
  if (mobile) return `flex min-h-11 items-center rounded-sm px-3 text-base ${tone}`;
  return `rounded-sm px-2 py-1 ${tone}`;
}

export function AppHeader({ activePage }: { activePage: PageId }) {
  const [open, setOpen] = useState(false);
  return (
    <header className={activePage === "chat" ? "chat-header" : "border-b border-shell-800 bg-shell-900"}>
      <div className="mx-auto flex max-w-[1600px] items-center gap-3 px-4 py-2 lg:flex-wrap lg:gap-x-6 lg:gap-y-3 lg:py-3">
        <div className="flex min-w-0 items-baseline gap-2">
          <span aria-hidden className="chat-brand-dot size-2 shrink-0 rounded-full bg-plasma-500" />
          <h1 className="truncate text-sm font-semibold tracking-wide text-ink-100">PokeAgent</h1>
        </div>

        <button
          type="button"
          className="ml-auto inline-flex size-11 items-center justify-center rounded-sm border border-shell-700 lg:hidden"
          aria-expanded={open}
          aria-controls="site-menu"
          onClick={() => setOpen((value) => !value)}
        >
          <span className="sr-only">{open ? "Close menu" : "Open menu"}</span>
          <span aria-hidden className="flex w-5 flex-col gap-1.5">
            <span className="block h-0.5 bg-current" />
            <span className="block h-0.5 bg-current" />
            <span className="block h-0.5 bg-current" />
          </span>
        </button>

        <nav aria-label="Main navigation" className="hidden items-center gap-1 text-xs lg:flex">
          {LINKS.map((link) => (
            <Link
              key={link.id}
              href={link.href}
              aria-current={activePage === link.id ? "page" : undefined}
              className={linkClass(activePage === link.id, false)}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto hidden items-center gap-2 text-xs lg:flex">
          <span className="text-ink-500">Model</span>
          <span className="rounded-sm border border-shell-700 bg-shell-800 px-2 py-1 font-mono text-ink-300">
            DeepSeek Flash
          </span>
        </div>
      </div>
      {open ? (
        <nav id="site-menu" aria-label="Mobile" className="flex flex-col px-2 pb-2 lg:hidden">
          {LINKS.map((link) => (
            <Link
              key={link.id}
              href={link.href}
              aria-current={activePage === link.id ? "page" : undefined}
              className={linkClass(activePage === link.id, true)}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <p className="px-3 py-2 text-xs text-ink-500">
            Model <span className="font-mono text-ink-300">DeepSeek Flash</span>
          </p>
        </nav>
      ) : null}
    </header>
  );
}
