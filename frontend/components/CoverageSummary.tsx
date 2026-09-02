import type { GapKind, TypeName } from "@/lib/types";
import { TypeChip } from "./TypeChip";

const GROUPS: Record<GapKind, { title: string; hint: string; marker: string }> = {
  defensive: {
    title: "Defensive gaps",
    hint: "nothing on the team resists these",
    marker: "○",
  },
  offensive: {
    title: "Offensive gaps",
    hint: "nothing on the team hits these 2×",
    marker: "△",
  },
};

function GapGroup({ kind, types }: { kind: GapKind; types: readonly TypeName[] }) {
  const { title, hint, marker } = GROUPS[kind];

  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-xs font-semibold tracking-wide text-ink-300 uppercase">{title}</h3>
        <span className="font-mono text-xs text-plasma-300">{types.length}</span>
      </div>
      <p className="mt-0.5 text-xs text-ink-500">{hint}</p>
      {types.length === 0 ? (
        <p className="mt-2 text-xs text-ink-500">None.</p>
      ) : (
        <ul className="mt-2 flex flex-wrap gap-1.5">
          {types.map((type) => (
            <li key={type}>
              <TypeChip type={type} marker={marker} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

type CoverageSummaryProps = {
  defensiveGaps: readonly TypeName[];
  offensiveGaps: readonly TypeName[];
};

export function CoverageSummary({ defensiveGaps, offensiveGaps }: CoverageSummaryProps) {
  return (
    <section className="rounded-md border border-shell-700 bg-shell-900 p-3">
      <h2 className="mb-3 text-xs font-semibold tracking-widest text-ink-500 uppercase">
        Coverage
      </h2>
      <div className="space-y-4">
        <GapGroup kind="defensive" types={defensiveGaps} />
        <GapGroup kind="offensive" types={offensiveGaps} />
      </div>
    </section>
  );
}
