import type { Slot } from "@/lib/types";
import { TypeChip } from "./TypeChip";

/** Placeholder for a sprite: the first letter over a flat well. No images yet. */
function SpriteStandIn({ name }: { name: string }) {
  return (
    <span
      aria-hidden
      className="flex size-9 shrink-0 items-center justify-center rounded-sm border border-shell-700 bg-screen-950 font-mono text-sm text-ink-500"
    >
      {name.charAt(0)}
    </span>
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
            className="flex size-9 shrink-0 items-center justify-center rounded-sm border border-dashed border-shell-700 font-mono text-sm text-shell-600"
          >
            {slotNumber}
          </span>
          <span className="text-sm text-ink-500">
            Add to slot {slotNumber}
            <span className="mt-0.5 block text-xs text-shell-600">Filter by type or stat</span>
          </span>
        </button>
      </li>
    );
  }

  const isSuggested = slot.origin === "suggested";

  return (
    <li
      className={`flex items-center gap-3 rounded-md border p-2 ${
        isSuggested
          ? "border-plasma-600 border-dashed bg-plasma-600/10"
          : "border-shell-700 bg-shell-900"
      }`}
    >
      <SpriteStandIn name={slot.pokemon.name} />
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className="truncate text-sm font-medium text-ink-100">{slot.pokemon.name}</span>
          {isSuggested && (
            <span className="shrink-0 rounded-xs bg-plasma-600/25 px-1 py-px font-mono text-[10px] tracking-wide text-plasma-300 uppercase">
              Suggested
            </span>
          )}
        </div>
        <ul className="mt-1 flex flex-wrap gap-1">
          {slot.pokemon.types.map((type) => (
            <li key={type}>
              <TypeChip type={type} />
            </li>
          ))}
        </ul>
      </div>
      <button
        type="button"
        onClick={() => onRemove(index)}
        aria-label={`Remove ${slot.pokemon.name} from slot ${slotNumber}`}
        className="shrink-0 rounded-sm px-2 py-1 text-ink-500 transition-colors hover:bg-shell-800 hover:text-ink-100"
      >
        <span aria-hidden>✕</span>
      </button>
    </li>
  );
}
