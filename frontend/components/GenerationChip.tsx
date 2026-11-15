"use client";

import { useEffect, useId, useRef, useState } from "react";
import { GENERATIONS, type Generation } from "@/lib/types";

type GenerationChipProps = {
  generation: Generation | null;
  onChange: (generation: Generation | null) => void;
  tone: "light" | "dark";
  placement: "up" | "down";
};

export function GenerationChip({ generation, onChange, tone, placement }: GenerationChipProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const listId = useId();
  const label = generation === null ? "Generation: Any" : `Generation: ${generation}`;

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

  const choose = (value: Generation | null) => {
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
          aria-label="Generation"
          className={`generation-menu generation-menu-${placement}`}
        >
          <li>
            <button
              type="button"
              role="option"
              aria-selected={generation === null}
              onClick={() => choose(null)}
            >
              Any
            </button>
          </li>
          {GENERATIONS.map((value) => (
            <li key={value}>
              <button
                type="button"
                role="option"
                aria-selected={generation === value}
                onClick={() => choose(value)}
              >
                Gen {value}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
