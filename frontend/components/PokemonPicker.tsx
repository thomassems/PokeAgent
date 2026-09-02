"use client";

import { useEffect, useRef, useState } from "react";
import { POKEMON, typesForGeneration } from "@/lib/mock-data";
import type { Generation, Pokemon, StatKey, TypeName } from "@/lib/types";
import { GENERATIONS } from "@/lib/types";
import { TypeChip } from "./TypeChip";

const STAT_OPTIONS: readonly { key: StatKey; label: string }[] = [
  { key: "speed", label: "Speed" },
  { key: "attack", label: "Attack" },
  { key: "defense", label: "Defense" },
  { key: "spAttack", label: "Sp. Attack" },
  { key: "spDefense", label: "Sp. Defense" },
  { key: "hp", label: "HP" },
];

const selectClass =
  "rounded-sm border border-shell-700 bg-shell-800 px-2 py-1 text-xs text-ink-100";

type PokemonPickerProps = {
  slotIndex: number | null;
  generation: Generation;
  onGenerationChange: (generation: Generation) => void;
  onSelect: (pokemon: Pokemon) => void;
  onClose: () => void;
};

export function PokemonPicker({
  slotIndex,
  generation,
  onGenerationChange,
  onSelect,
  onClose,
}: PokemonPickerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [typeFilter, setTypeFilter] = useState<TypeName | "all">("all");
  const [sortStat, setSortStat] = useState<StatKey>("speed");

  const isOpen = slotIndex !== null;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    // showModal() throws if the dialog is already open, so both directions are guarded.
    if (isOpen && !dialog.open) dialog.showModal();
    if (!isOpen && dialog.open) dialog.close();
  }, [isOpen]);

  // A Pokemon is pickable in a generation if it had debuted by then.
  const candidates = POKEMON.filter(
    (pokemon) =>
      pokemon.generation <= generation &&
      (typeFilter === "all" || pokemon.types.includes(typeFilter)),
  ).toSorted((a, b) => b.stats[sortStat] - a.stats[sortStat]);

  return (
    <dialog
      ref={dialogRef}
      // Fires for Escape as well as close(); the browser also restores focus to
      // whatever was focused before showModal(), so the slot button gets it back.
      onClose={onClose}
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose();
      }}
      aria-labelledby="picker-title"
      className="m-auto w-[min(32rem,calc(100vw-2rem))] rounded-md border border-shell-700 bg-shell-900 p-0 text-ink-100 backdrop:bg-shell-950/70"
    >
      <div className="flex items-center justify-between border-b border-shell-800 px-4 py-3">
        <h2 id="picker-title" className="text-sm font-semibold">
          Choose for slot {(slotIndex ?? 0) + 1}
        </h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close picker"
          className="rounded-sm px-2 py-1 text-ink-500 transition-colors hover:bg-shell-800 hover:text-ink-100"
        >
          <span aria-hidden>✕</span>
        </button>
      </div>

      <div className="flex flex-wrap gap-3 border-b border-shell-800 px-4 py-3">
        <div className="flex items-center gap-1.5">
          <label htmlFor="picker-type" className="text-xs text-ink-500">
            Type
          </label>
          <select
            id="picker-type"
            value={typeFilter}
            onChange={(event) => setTypeFilter(event.target.value as TypeName | "all")}
            className={`${selectClass} capitalize`}
          >
            <option value="all">All</option>
            {typesForGeneration(generation).map((type) => (
              <option key={type} value={type} className="capitalize">
                {type}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1.5">
          <label htmlFor="picker-gen" className="text-xs text-ink-500">
            Gen
          </label>
          {/* Bound to app-level state, so changing it here also moves the header. */}
          <select
            id="picker-gen"
            value={generation}
            onChange={(event) => onGenerationChange(Number(event.target.value) as Generation)}
            className={selectClass}
          >
            {GENERATIONS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1.5">
          <label htmlFor="picker-sort" className="text-xs text-ink-500">
            Sort
          </label>
          <select
            id="picker-sort"
            value={sortStat}
            onChange={(event) => setSortStat(event.target.value as StatKey)}
            className={selectClass}
          >
            {STAT_OPTIONS.map(({ key, label }) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="max-h-[50vh] overflow-y-auto p-2">
        {candidates.length === 0 ? (
          <p className="p-4 text-center text-sm text-ink-500">
            Nothing matches those filters in generation {generation}.
          </p>
        ) : (
          <ul className="space-y-1">
            {candidates.map((pokemon) => (
              <li key={pokemon.id}>
                <button
                  type="button"
                  onClick={() => onSelect(pokemon)}
                  className="flex w-full items-center gap-3 rounded-sm px-2 py-1.5 text-left transition-colors hover:bg-shell-800"
                >
                  <span className="min-w-0 flex-1 truncate text-sm">{pokemon.name}</span>
                  <span className="flex shrink-0 gap-1">
                    {pokemon.types.map((type) => (
                      <TypeChip key={type} type={type} />
                    ))}
                  </span>
                  <span className="w-16 shrink-0 text-right font-mono text-xs text-ink-500">
                    gen {pokemon.generation}
                  </span>
                  <span className="w-8 shrink-0 text-right font-mono text-xs text-plasma-300">
                    {pokemon.stats[sortStat]}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </dialog>
  );
}
