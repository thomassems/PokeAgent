import type { Generation, Slot, TypeName } from "@/lib/types";
import { typesForGeneration } from "@/lib/mock-data";
import { CoverageSummary } from "./CoverageSummary";
import { GenerationChip } from "./GenerationChip";
import { TeamSlot } from "./TeamSlot";
import { TypeChip } from "./TypeChip";

type TeamBuilderProps = {
  team: readonly Slot[];
  generation: Generation | null;
  onGenerationChange: (generation: Generation | null) => void;
  defensiveGaps: readonly TypeName[];
  offensiveGaps: readonly TypeName[];
  onOpenPicker: (index: number) => void;
  onRemove: (index: number) => void;
};

export function TeamBuilder({
  team,
  generation,
  onGenerationChange,
  defensiveGaps,
  offensiveGaps,
  onOpenPicker,
  onRemove,
}: TeamBuilderProps) {
  const filled = team.filter((slot) => slot.kind === "filled").length;
  const availableTypes = typesForGeneration(generation);

  return (
    <div className="space-y-4">
      <section>
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-xs font-semibold tracking-widest text-ink-500 uppercase">Team</h2>
          <div className="flex items-center gap-2">
            <GenerationChip
              generation={generation}
              onChange={onGenerationChange}
              tone="dark"
              placement="down"
            />
            <span className="font-mono text-xs text-ink-500">{filled} / 6</span>
          </div>
        </div>
        <ul className="space-y-2">
          {team.map((slot, index) => (
            <TeamSlot
              // Slots are positional: index is the identity here, not a fallback.
              key={index}
              slot={slot}
              index={index}
              onOpenPicker={onOpenPicker}
              onRemove={onRemove}
            />
          ))}
        </ul>
      </section>

      <CoverageSummary defensiveGaps={defensiveGaps} offensiveGaps={offensiveGaps} />

      {/* Fairy arrives in Gen 6. With no generation selected this uses the latest chart. */}
      <section className="rounded-md border border-shell-700 bg-shell-900 p-3">
        <div className="mb-2 flex items-baseline justify-between">
          <h2 className="text-xs font-semibold tracking-widest text-ink-500 uppercase">
            {generation === null ? "Types" : `Types in gen ${generation}`}
          </h2>
          <span className="font-mono text-xs text-ink-500">{availableTypes.length}</span>
        </div>
        <ul className="flex flex-wrap gap-1.5">
          {availableTypes.map((type) => (
            <li key={type}>
              <TypeChip type={type} />
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
