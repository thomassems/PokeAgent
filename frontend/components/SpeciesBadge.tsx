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

// These type fills are dark enough that shell-950 initials disappear.
const LIGHT_INITIALS: ReadonlySet<TypeName> = new Set([
  "dark",
  "ghost",
  "dragon",
  "fighting",
  "poison",
]);

type SpeciesBadgeProps = {
  name: string;
  types?: readonly TypeName[];
  size?: "md" | "lg";
};

/** Type-coloured initials. Original marks only: no official artwork. */
export function SpeciesBadge({ name, types = [], size = "md" }: SpeciesBadgeProps) {
  const primary = types[0] ?? "normal";
  const initials = name
    .split(/[\s-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
  const dimension = size === "lg" ? "size-24 text-lg" : "size-16 text-sm";
  const ink = LIGHT_INITIALS.has(primary) ? "text-ink-100" : "text-shell-950";

  return (
    <span
      aria-hidden
      className={`inline-flex shrink-0 items-center justify-center rounded-md font-mono font-semibold ${dimension} ${TYPE_COLOR[primary]} ${ink}`}
    >
      {initials || "?"}
    </span>
  );
}
