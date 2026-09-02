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

/**
 * `origin` is the only thing separating a slot the user picked from one the
 * agent suggested. Nothing computes it yet; it is hardcoded in the mock team.
 */
export type Slot =
  | { kind: "empty" }
  | { kind: "filled"; pokemon: Pokemon; origin: "chosen" | "suggested" };

export type GapKind = "defensive" | "offensive";

export type View = "before" | "after";
