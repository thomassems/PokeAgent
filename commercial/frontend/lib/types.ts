export const TYPE_NAMES = [
  "normal",
  "fire",
  "water",
  "electric",
  "grass",
  "ice",
  "fighting",
  "poison",
  "ground",
  "flying",
  "psychic",
  "bug",
  "rock",
  "ghost",
  "dragon",
  "dark",
  "steel",
  "fairy",
] as const;

export type TypeName = (typeof TYPE_NAMES)[number];

export const GENERATIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9] as const;

export type Generation = (typeof GENERATIONS)[number];

/** Used when the team builder needs a chart and the user has not picked one. */
export const LATEST_GENERATION: Generation = GENERATIONS[GENERATIONS.length - 1];

export type StatKey = "hp" | "attack" | "defense" | "spAttack" | "spDefense" | "speed";

export type Stats = Record<StatKey, number>;

export type Pokemon = {
  id: string;
  name: string;
  types: [TypeName] | [TypeName, TypeName];
  stats: Stats;
  /**
   * The generation this *form* debuted, not the species. Alolan Marowak is a
   * Gen 1 species but a Gen 7 form, and the generation filter is asking which
   * games you could actually build with - so the form's debut is the useful
   * answer.
   */
  generation: Generation;
};

/** A Pokémon placed in a team slot. Drawn as a type badge, not official art. */
export type SlotPokemon = {
  /** National dex number from the PokeAPI name index. Not an image id. */
  id: string;
  name: string;
  types: readonly TypeName[];
};

/**
 * `origin` separates a slot the user picked from one an agent suggested.
 * Nothing computes a suggestion yet.
 */
export type Slot =
  | { kind: "empty" }
  | { kind: "filled"; pokemon: SlotPokemon; origin: "chosen" | "suggested" };

export type GapKind = "defensive" | "offensive";

export type View = "before" | "after";
