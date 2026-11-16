"use client";

import type { GoAccent } from "@/lib/go-accent";

type AccentChipProps = {
  accent: GoAccent;
  onChange: (accent: GoAccent) => void;
};

const OPTIONS: readonly { value: GoAccent; label: string }[] = [
  { value: "neutral", label: "Neutral" },
  { value: "blue", label: "Blue" },
  { value: "red", label: "Red" },
  { value: "yellow", label: "Yellow" },
];

/**
 * A labelled colour choice. The swatch is decoration beside the word, so the
 * selection is still clear without colour.
 */
export function AccentChip({ accent, onChange }: AccentChipProps) {
  return (
    <div className="accent-chip" role="radiogroup" aria-label="Accent colour">
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={accent === option.value}
          className={accent === option.value ? "is-selected" : undefined}
          onClick={() => onChange(option.value)}
        >
          <span className={`accent-swatch accent-swatch-${option.value}`} aria-hidden="true" />
          {option.label}
        </button>
      ))}
    </div>
  );
}
