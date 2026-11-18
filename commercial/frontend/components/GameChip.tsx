"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { Game } from "@/lib/game";

type GameChipProps = {
  game: Game;
  onChange: (game: Game) => void;
  tone: "light" | "dark";
  placement: "up" | "down";
};

const OPTIONS: readonly { value: Game; label: string }[] = [
  { value: "main", label: "Main series" },
  { value: "go", label: "Pokémon GO" },
];

/**
 * Same menu chrome as the generation chip. The class names are shared on
 * purpose: the two chips sit next to each other and should look like one control.
 */
export function GameChip({ game, onChange, tone, placement }: GameChipProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const listId = useId();
  const label = OPTIONS.find((option) => option.value === game)?.label ?? "Main series";

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const choose = (value: Game) => {
    onChange(value);
    setOpen(false);
  };

  return (
    <div ref={rootRef} className={`generation-chip generation-chip-${tone}`}>
      <button
        type="button"
        className="generation-chip-button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        onClick={() => setOpen((current) => !current)}
      >
        {label}
      </button>
      {open && (
        <ul
          id={listId}
          role="listbox"
          aria-label="Game"
          className={`generation-menu generation-menu-${placement}`}
        >
          {OPTIONS.map((option) => (
            <li key={option.value}>
              <button
                type="button"
                role="option"
                aria-selected={game === option.value}
                onClick={() => choose(option.value)}
              >
                {option.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
