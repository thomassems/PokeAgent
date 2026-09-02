import type { TypeName } from "@/lib/types";

const TYPE_COLOR: Record<TypeName, string> = {
  normal: "bg-type-normal",
  fire: "bg-type-fire",
  water: "bg-type-water",
  electric: "bg-type-electric",
  grass: "bg-type-grass",
  ice: "bg-type-ice",
  fighting: "bg-type-fighting",
  poison: "bg-type-poison",
  ground: "bg-type-ground",
  flying: "bg-type-flying",
  psychic: "bg-type-psychic",
  bug: "bg-type-bug",
  rock: "bg-type-rock",
  ghost: "bg-type-ghost",
  dragon: "bg-type-dragon",
  dark: "bg-type-dark",
  steel: "bg-type-steel",
  fairy: "bg-type-fairy",
};

type TypeChipProps = {
  type: TypeName;
  /**
   * A shape drawn before the label. Gap chips use it so the defensive and
   * offensive groups stay distinguishable without relying on hue.
   */
  marker?: string;
};

export function TypeChip({ type, marker }: TypeChipProps) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-sm border border-shell-700 bg-shell-800 py-0.5 pr-2 pl-1.5 text-xs text-ink-100">
      {marker ? (
        <span aria-hidden className="text-ink-500">
          {marker}
        </span>
      ) : (
        <span aria-hidden className={`size-2 rounded-full ${TYPE_COLOR[type]}`} />
      )}
      <span className="capitalize">{type}</span>
    </span>
  );
}
