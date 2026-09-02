import type { View } from "@/lib/types";

/**
 * Temporary. Exists only so both layouts are inspectable before any agent can
 * drive the transition. Delete this file and its one call site in page.tsx.
 */
const VIEWS: readonly { value: View; label: string }[] = [
  { value: "before", label: "Before prompt" },
  { value: "after", label: "After prompt" },
];

export function DevViewToggle({
  view,
  onViewChange,
}: {
  view: View;
  onViewChange: (view: View) => void;
}) {
  return (
    <div className="fixed right-4 bottom-4 z-10 flex items-center gap-1 rounded-md border border-shell-700 bg-shell-800/95 p-1 shadow-lg">
      <span className="px-2 font-mono text-[10px] tracking-widest text-shell-600 uppercase">
        Dev
      </span>
      {VIEWS.map(({ value, label }) => (
        <button
          key={value}
          type="button"
          onClick={() => onViewChange(value)}
          aria-pressed={view === value}
          className={`rounded-sm px-2 py-1 text-xs transition-colors ${
            view === value
              ? "bg-plasma-600 text-ink-100"
              : "text-ink-500 hover:bg-shell-700 hover:text-ink-100"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
