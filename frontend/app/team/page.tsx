"use client";

import { useState } from "react";
import { AppHeader } from "@/components/AppHeader";
import { PokemonPicker } from "@/components/PokemonPicker";
import { TeamBuilder } from "@/components/TeamBuilder";
import { DEFENSIVE_GAPS, INITIAL_TEAM, OFFENSIVE_GAPS } from "@/lib/mock-data";
import type { Generation, Pokemon, Slot } from "@/lib/types";

export default function TeamPage() {
  const [generation, setGeneration] = useState<Generation>(4);
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
      <AppHeader activePage="team" generation={generation} onGenerationChange={setGeneration} />

      <main className="mx-auto grid max-w-[1600px] gap-4 p-4 lg:grid-cols-[minmax(18rem,30%)_1fr]">
        <TeamBuilder
          team={team}
          generation={generation}
          defensiveGaps={DEFENSIVE_GAPS}
          offensiveGaps={OFFENSIVE_GAPS}
          onOpenPicker={setPickerSlot}
          onRemove={(index) => replaceSlot(index, { kind: "empty" })}
        />

        <section className="h-fit rounded-md border border-shell-700 bg-shell-900 p-4">
          <h2 className="text-sm font-semibold text-ink-100">Team agent comes later</h2>
          <p className="mt-2 max-w-prose text-sm leading-relaxed text-ink-300">
            This team builder is a preview. Its slots are not sent to the chat agent.
          </p>
        </section>
      </main>

      <PokemonPicker
        slotIndex={pickerSlot}
        generation={generation}
        onGenerationChange={setGeneration}
        onSelect={handleSelect}
        onClose={() => setPickerSlot(null)}
      />
    </div>
  );
}
