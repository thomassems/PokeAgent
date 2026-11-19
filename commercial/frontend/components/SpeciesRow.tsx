"use client";

import { useEffect, useState } from "react";
import type { TypeName } from "@/lib/types";

const TYPE_COLOR: Record<TypeName, string> = {
  normal: "bg-type-normal text-shell-950",
  fire: "bg-type-fire text-shell-950",
  water: "bg-type-water text-shell-950",
  electric: "bg-type-electric text-shell-950",
  grass: "bg-type-grass text-shell-950",
  ice: "bg-type-ice text-shell-950",
  fighting: "bg-type-fighting text-ink-100",
  poison: "bg-type-poison text-ink-100",
  ground: "bg-type-ground text-shell-950",
  flying: "bg-type-flying text-shell-950",
  psychic: "bg-type-psychic text-shell-950",
  bug: "bg-type-bug text-shell-950",
  rock: "bg-type-rock text-shell-950",
  ghost: "bg-type-ghost text-ink-100",
  dragon: "bg-type-dragon text-ink-100",
  dark: "bg-type-dark text-ink-100",
  steel: "bg-type-steel text-shell-950",
  fairy: "bg-type-fairy text-shell-950",
};

export type SpeciesRowProps = {
  dex?: number;
  name: string;
  types?: readonly TypeName[];
  chips?: readonly string[];
};

let spriteFlag: Promise<boolean> | null = null;

function spriteFlagEnabled(): Promise<boolean> {
  if (!spriteFlag) {
    spriteFlag = fetch("/api/config")
      .then((response) => response.json())
      .then((body: { official_sprites?: boolean }) => Boolean(body.official_sprites))
      .catch(() => false);
  }
  return spriteFlag;
}

export function dexLabel(dex: number | undefined): string {
  if (!dex) return "#----";
  return `#${String(dex).padStart(4, "0")}`;
}

/** Compact text row. No official type symbols and no artwork. */
export function SpeciesRow({ dex, name, types = [], chips = [] }: SpeciesRowProps) {
  const [sprites, setSprites] = useState(false);
  useEffect(() => {
    void spriteFlagEnabled().then(setSprites);
  }, []);

  return (
    <div className="flex min-h-11 min-w-0 flex-1 items-start gap-3">
      <span className="w-14 shrink-0 pt-0.5 font-mono text-xs tabular-nums text-ink-400">
        {dexLabel(dex)}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-ink-100">{name}</p>
        <div className="mt-1 flex flex-wrap gap-1">
          {types.map((type) => (
            <span
              key={type}
              className={`rounded-sm px-1.5 py-0.5 text-[11px] font-medium capitalize ${TYPE_COLOR[type] ?? "bg-shell-700 text-ink-100"}`}
            >
              {type}
            </span>
          ))}
          {chips.map((chip) => (
            <span
              key={chip}
              className="rounded-sm border border-shell-600 px-1.5 py-0.5 text-[11px] text-ink-300"
            >
              {chip}
            </span>
          ))}
        </div>
        {sprites ? (
          <p className="mt-1 text-[11px] text-ink-500">No sprite file in this build.</p>
        ) : null}
      </div>
    </div>
  );
}
