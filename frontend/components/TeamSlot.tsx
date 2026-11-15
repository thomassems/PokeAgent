"use client";

import { useState } from "react";
import type { Slot } from "@/lib/types";
import { TypeChip } from "./TypeChip";

/**
 * Official PokeAPI sprites are already pixel art. A plain img at the file's
 * native 96px keeps that grid on an integer scale. next/image would resample
 * it, which softens the pixels.
 */
function PixelSprite({ src, name }: { src: string; name: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <span
        aria-hidden
        className="flex size-24 items-center justify-center font-mono text-lg text-ink-500"
      >
        {name.charAt(0)}
      </span>
    );
  }
  return (
    // The sprite file is already 96px pixel art. next/image would resample it.
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt=""
      width={96}
      height={96}
      className="pixel-sprite"
      onError={() => setFailed(true)}
    />
  );
}

type TeamSlotProps = {
  slot: Slot;
  index: number;
  onOpenPicker: (index: number) => void;
  onRemove: (index: number) => void;
};

export function TeamSlot({ slot, index, onOpenPicker, onRemove }: TeamSlotProps) {
  const slotNumber = index + 1;

  if (slot.kind === "empty") {
    return (
      <li>
        <button
          type="button"
          onClick={() => onOpenPicker(index)}
          className="flex w-full items-center gap-3 rounded-md border border-dashed border-shell-700 bg-shell-900/40 p-2 text-left transition-colors hover:border-plasma-600 hover:bg-shell-900"
        >
          <span
            aria-hidden
            className="flex size-24 shrink-0 items-center justify-center rounded-sm border border-dashed border-shell-700 font-mono text-sm text-shell-600"
          >
            {slotNumber}
          </span>
          <span className="text-sm text-ink-500">
            Add to slot {slotNumber}
            <span className="mt-0.5 block text-xs text-shell-600">Search by name</span>
          </span>
        </button>
      </li>
    );
  }

  const isSuggested = slot.origin === "suggested";

  return (
    <li
      className={`flex items-center gap-2 rounded-md border p-2 ${
        isSuggested
          ? "border-plasma-600 border-dashed bg-plasma-600/10"
          : "border-shell-700 bg-shell-900"
      }`}
    >
      <button
        type="button"
        onClick={() => onOpenPicker(index)}
        aria-label={`Replace ${slot.pokemon.name}`}
        className="flex min-w-0 flex-1 items-center gap-3 text-left"
      >
        <span className="flex size-24 shrink-0 items-center justify-center overflow-hidden rounded-sm border border-shell-700 bg-screen-950">
          <PixelSprite key={slot.pokemon.spriteUrl} src={slot.pokemon.spriteUrl} name={slot.pokemon.name} />
        </span>
        <span className="min-w-0">
          <span className="flex items-baseline gap-2">
            <span className="truncate text-sm font-medium text-ink-100">{slot.pokemon.name}</span>
            {isSuggested && (
              <span className="shrink-0 rounded-xs bg-plasma-600/25 px-1 py-px font-mono text-[10px] tracking-wide text-plasma-300 uppercase">
                Suggested
              </span>
            )}
          </span>
          {slot.pokemon.types.length > 0 && (
            <ul className="mt-1 flex flex-wrap gap-1">
              {slot.pokemon.types.map((type) => (
                <li key={type}>
                  <TypeChip type={type} />
                </li>
              ))}
            </ul>
          )}
        </span>
      </button>
      <button
        type="button"
        onClick={() => onRemove(index)}
        aria-label={`Remove ${slot.pokemon.name} from slot ${slotNumber}`}
        className="shrink-0 self-start rounded-sm px-2 py-1 text-ink-500 transition-colors hover:bg-shell-800 hover:text-ink-100"
      >
        <span aria-hidden>✕</span>
      </button>
    </li>
  );
}
