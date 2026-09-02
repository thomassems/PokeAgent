import type { Generation } from "@/lib/types";
import { GENERATIONS } from "@/lib/types";

type AppHeaderProps = {
  generation: Generation;
  onGenerationChange: (generation: Generation) => void;
};

export function AppHeader({ generation, onGenerationChange }: AppHeaderProps) {
  return (
    <header className="border-b border-shell-800 bg-shell-900">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <div className="flex items-baseline gap-2">
          <span aria-hidden className="size-2 rounded-full bg-plasma-500" />
          <h1 className="text-sm font-semibold tracking-wide text-ink-100">PokeAgent</h1>
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="generation" className="text-xs text-ink-500">
            Generation
          </label>
          <select
            id="generation"
            value={generation}
            onChange={(event) => onGenerationChange(Number(event.target.value) as Generation)}
            className="rounded-sm border border-shell-700 bg-shell-800 px-2 py-1 font-mono text-xs text-ink-100"
          >
            {GENERATIONS.map((value) => (
              <option key={value} value={value}>
                Gen {value}
              </option>
            ))}
          </select>
        </div>

        <div className="ml-auto flex items-center gap-2 text-xs">
          <span className="text-ink-500">Model</span>
          <span className="rounded-sm border border-shell-700 bg-shell-800 px-2 py-1 font-mono text-ink-300">
            deepseek-chat
          </span>
        </div>
      </div>
    </header>
  );
}
