"use client";

import { useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { DevViewToggle } from "@/components/DevViewToggle";
import { PokemonPicker } from "@/components/PokemonPicker";
import { PromptPanel } from "@/components/PromptPanel";
import { ResultPanels } from "@/components/ResultPanels";
import { TeamBuilder } from "@/components/TeamBuilder";
import { DEFENSIVE_GAPS, INITIAL_TEAM, OFFENSIVE_GAPS } from "@/lib/mock-data";
import type { Generation, Pokemon, Slot, View } from "@/lib/types";

/**
 * Every piece of state in the shell lives here and travels down as props. At six
 * slots and one modal that is comfortable; a store earns its place when prop
 * drilling actually hurts, not before.
 */
export default function Home() {
  const [generation, setGeneration] = useState<Generation>(4);
  const [view, setView] = useState<View>("before");
  const [team, setTeam] = useState<readonly Slot[]>(INITIAL_TEAM);
  const [pickerSlot, setPickerSlot] = useState<number | null>(null);

  const replaceSlot = (index: number, slot: Slot) =>
    setTeam((current) => current.map((existing, i) => (i === index ? slot : existing)));

  const handleSelect = (pokemon: Pokemon) => {
    if (pickerSlot === null) return;
    replaceSlot(pickerSlot, { kind: "filled", pokemon, origin: "chosen" });
    setPickerSlot(null);
  };

  return (
    <div className="min-h-screen">
      <AppHeader generation={generation} onGenerationChange={setGeneration} />

      <main className="mx-auto grid max-w-[1600px] gap-4 p-4 lg:grid-cols-[minmax(18rem,30%)_1fr]">
        <TeamBuilder
          team={team}
          generation={generation}
          defensiveGaps={DEFENSIVE_GAPS}
          offensiveGaps={OFFENSIVE_GAPS}
          onOpenPicker={setPickerSlot}
          onRemove={(index) => replaceSlot(index, { kind: "empty" })}
        />

        <div className="min-w-0 space-y-4">
          <PromptPanel view={view} />
          {view === "after" && <ResultPanels />}
        </div>
      </main>

      <PokemonPicker
        slotIndex={pickerSlot}
        generation={generation}
        onGenerationChange={setGeneration}
        onSelect={handleSelect}
        onClose={() => setPickerSlot(null)}
      />

      <DevViewToggle view={view} onViewChange={setView} />
    </div>
  );
}
