import type { Generation, Pokemon, Slot, TypeName } from "./types";
import { TYPE_NAMES } from "./types";

/**
 * Placeholder dex for the layout shell. Base stats are real values so the stat
 * sort produces a believable ordering, but this file is scaffolding - the baked
 * dex under backend/data/ replaces it wholesale.
 */
type PokemonRow = readonly [
  id: string,
  name: string,
  types: readonly [TypeName] | readonly [TypeName, TypeName],
  generation: Generation,
  stats: readonly [number, number, number, number, number, number],
];

const ROWS = [
  ["charizard", "Charizard", ["fire", "flying"], 1, [78, 84, 78, 109, 85, 100]],
  ["gengar", "Gengar", ["ghost", "poison"], 1, [60, 65, 60, 130, 75, 110]],
  ["snorlax", "Snorlax", ["normal"], 1, [160, 110, 65, 65, 110, 30]],
  ["gyarados", "Gyarados", ["water", "flying"], 1, [95, 125, 79, 60, 100, 81]],
  ["alakazam", "Alakazam", ["psychic"], 1, [55, 50, 45, 135, 95, 120]],
  ["machamp", "Machamp", ["fighting"], 1, [90, 130, 80, 65, 85, 55]],
  ["tyranitar", "Tyranitar", ["rock", "dark"], 2, [100, 134, 110, 95, 100, 61]],
  ["scizor", "Scizor", ["bug", "steel"], 2, [70, 130, 100, 55, 80, 65]],
  ["umbreon", "Umbreon", ["dark"], 2, [95, 65, 110, 60, 130, 65]],
  ["heracross", "Heracross", ["bug", "fighting"], 2, [80, 125, 75, 40, 95, 85]],
  ["metagross", "Metagross", ["steel", "psychic"], 3, [80, 135, 130, 95, 90, 70]],
  ["salamence", "Salamence", ["dragon", "flying"], 3, [95, 135, 80, 110, 80, 100]],
  ["blaziken", "Blaziken", ["fire", "fighting"], 3, [80, 120, 70, 110, 70, 80]],
  ["milotic", "Milotic", ["water"], 3, [95, 60, 79, 100, 125, 81]],
  ["flygon", "Flygon", ["ground", "dragon"], 3, [80, 100, 80, 80, 80, 100]],
  ["infernape", "Infernape", ["fire", "fighting"], 4, [76, 104, 71, 104, 71, 108]],
  ["empoleon", "Empoleon", ["water", "steel"], 4, [84, 86, 88, 111, 101, 60]],
  ["torterra", "Torterra", ["grass", "ground"], 4, [95, 109, 105, 75, 85, 56]],
  ["garchomp", "Garchomp", ["dragon", "ground"], 4, [108, 130, 95, 80, 85, 102]],
  ["lucario", "Lucario", ["fighting", "steel"], 4, [70, 110, 70, 115, 70, 90]],
  ["staraptor", "Staraptor", ["normal", "flying"], 4, [85, 120, 70, 50, 60, 100]],
  ["roserade", "Roserade", ["grass", "poison"], 4, [60, 70, 65, 125, 105, 90]],
  ["luxray", "Luxray", ["electric"], 4, [80, 120, 79, 95, 79, 70]],
  ["weavile", "Weavile", ["dark", "ice"], 4, [70, 120, 65, 45, 85, 125]],
  ["gliscor", "Gliscor", ["ground", "flying"], 4, [75, 95, 125, 45, 75, 95]],
  ["rotom", "Rotom", ["electric", "ghost"], 4, [50, 50, 77, 95, 77, 91]],
  ["magnezone", "Magnezone", ["electric", "steel"], 4, [70, 70, 115, 130, 90, 60]],
  ["hydreigon", "Hydreigon", ["dark", "dragon"], 5, [92, 105, 90, 125, 90, 98]],
  ["volcarona", "Volcarona", ["bug", "fire"], 5, [85, 60, 65, 135, 105, 100]],
  ["aegislash", "Aegislash", ["steel", "ghost"], 6, [60, 50, 140, 50, 140, 60]],
  ["sylveon", "Sylveon", ["fairy"], 6, [95, 65, 65, 110, 130, 60]],
  ["talonflame", "Talonflame", ["fire", "flying"], 6, [78, 81, 71, 74, 69, 126]],
  ["marowak-alola", "Marowak (Alolan)", ["fire", "ghost"], 7, [60, 80, 110, 50, 80, 45]],
  ["mimikyu", "Mimikyu", ["ghost", "fairy"], 7, [55, 90, 80, 50, 105, 96]],
  ["toxapex", "Toxapex", ["poison", "water"], 7, [50, 63, 152, 53, 142, 35]],
] as const satisfies readonly PokemonRow[];

export const POKEMON: readonly Pokemon[] = ROWS.map(([id, name, types, generation, s]) => ({
  id,
  name,
  // The rows are `as const` for literal type inference, which makes the tuples
  // readonly; Pokemon owns a mutable copy.
  types: [...types] as Pokemon["types"],
  generation,
  stats: { hp: s[0], attack: s[1], defense: s[2], spAttack: s[3], spDefense: s[4], speed: s[5] },
}));

/**
 * Dark and Steel arrived in Gen 2, Fairy in Gen 6. Hardcoded so the generation
 * control has a visible effect - pick an early generation and chips disappear.
 */
export function typesForGeneration(generation: Generation): readonly TypeName[] {
  return TYPE_NAMES.filter((type) => {
    if (type === "fairy") return generation >= 6;
    if (type === "dark" || type === "steel") return generation >= 2;
    return true;
  });
}

const byId = (id: string): Pokemon => {
  const found = POKEMON.find((pokemon) => pokemon.id === id);
  if (!found) throw new Error(`Unknown placeholder pokemon: ${id}`);
  return found;
};

/** One chosen and one suggested slot, so the two states are visible side by side. */
export const INITIAL_TEAM: readonly Slot[] = [
  { kind: "filled", pokemon: byId("infernape"), origin: "chosen" },
  { kind: "filled", pokemon: byId("rotom"), origin: "suggested" },
  { kind: "empty" },
  { kind: "empty" },
  { kind: "empty" },
  { kind: "empty" },
];

export const DEFENSIVE_GAPS: readonly TypeName[] = ["ice", "dragon", "fighting", "rock"];

export const OFFENSIVE_GAPS: readonly TypeName[] = ["steel", "ghost"];

export const CUSTOM_LOOP_LINES: readonly string[] = [
  "Parsing request: balanced team, Sinnoh-legal, no legendaries.",
  "Team has 2 of 6 slots filled. Working the remaining 4.",
  "Calling find_candidates(types=[ice, dragon], sort=speed)",
  "  → 14 candidates returned",
  "Calling type_effectiveness(team=[infernape, rotom])",
  "  → defensive gaps: ice, dragon, fighting, rock",
  "  → offensive gaps: steel, ghost",
  "Weavile covers ice and dragon offensively but adds a fighting weakness.",
  "Calling find_candidates(resists=[fighting], sort=defense)",
  "  → 9 candidates returned",
  "Gliscor resists fighting and covers the ground gap.",
  "Re-checking defensive gaps with the provisional team.",
  "  → defensive gaps: rock",
  "Two slots remain. Proposing Empoleon for the rock gap.",
];

export const LANGCHAIN_LINES: readonly string[] = [
  "Invoking agent with 3 bound tools.",
  "Tool call: find_candidates",
  "Tool call: type_effectiveness",
  "Observation: 4 defensive gaps, 2 offensive gaps.",
  "Proposing Weavile, Gliscor, Empoleon, Bronzong.",
  "Finished in 6 steps.",
];
