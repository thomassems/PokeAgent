import { TYPE_NAMES, type TypeName } from "./types";

const INDEX_URL = "https://pokeapi.co/api/v2/pokemon?limit=2000";
const INDEX_STORAGE_KEY = "trainermon.pokemon-index.v1";

export type PokemonName = {
  id: number;
  slug: string;
  name: string;
};

export type PokemonDetails = {
  id: number;
  name: string;
  types: TypeName[];
};

type IndexResponse = {
  results: { name: string; url: string }[];
};

type PokemonResponse = {
  types: { slot: number; type: { name: string } }[];
};

let memory: PokemonName[] | null = null;
let inflight: Promise<PokemonName[]> | null = null;

function displayName(slug: string): string {
  return slug
    .split("-")
    .map((part) => (part ? part.charAt(0).toUpperCase() + part.slice(1) : part))
    .join(" ");
}

function isTypeName(value: string): value is TypeName {
  return (TYPE_NAMES as readonly string[]).includes(value);
}

function isStoredIndex(value: unknown): value is PokemonName[] {
  return (
    Array.isArray(value) &&
    value.length > 0 &&
    value.every(
      (entry) =>
        typeof entry === "object" &&
        entry !== null &&
        typeof (entry as PokemonName).id === "number" &&
        typeof (entry as PokemonName).slug === "string" &&
        typeof (entry as PokemonName).name === "string",
    )
  );
}

function readStoredIndex(): PokemonName[] | null {
  try {
    const raw = window.localStorage.getItem(INDEX_STORAGE_KEY);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    return isStoredIndex(parsed) ? parsed : null;
  } catch {
    // A bad cache should not block the network fetch that replaces it.
    return null;
  }
}

async function fetchIndex(): Promise<PokemonName[]> {
  const response = await fetch(INDEX_URL);
  if (!response.ok) throw new Error("Could not load Pokémon names.");
  const body = (await response.json()) as IndexResponse;
  return body.results.flatMap((entry) => {
    const id = Number(entry.url.split("/").filter(Boolean).pop());
    if (!Number.isInteger(id)) return [];
    return [{ id, slug: entry.name, name: displayName(entry.name) }];
  });
}

/** The full name list, kept in memory and in localStorage after the first fetch. */
export function loadPokemonNames(): Promise<PokemonName[]> {
  if (memory) return Promise.resolve(memory);
  if (!inflight) {
    const stored = readStoredIndex();
    if (stored) {
      memory = stored;
      return Promise.resolve(stored);
    }
    inflight = fetchIndex().then(
      (names) => {
        memory = names;
        try {
          window.localStorage.setItem(INDEX_STORAGE_KEY, JSON.stringify(names));
        } catch {
          // The memory cache still serves this page if storage is full.
        }
        return names;
      },
      (error: unknown) => {
        inflight = null;
        throw error;
      },
    );
  }
  return inflight;
}

/** Prefix matches first, then substring matches. Empty until two characters. */
export function searchPokemonNames(
  names: readonly PokemonName[],
  query: string,
): PokemonName[] {
  const needle = query.trim().toLowerCase();
  if (needle.length < 2) return [];
  const prefixes: PokemonName[] = [];
  const contains: PokemonName[] = [];
  for (const entry of names) {
    const slug = entry.slug;
    const label = entry.name.toLowerCase();
    if (slug.startsWith(needle) || label.startsWith(needle)) prefixes.push(entry);
    else if (slug.includes(needle) || label.includes(needle)) contains.push(entry);
  }
  return [...prefixes, ...contains].slice(0, 8);
}

export async function loadPokemonDetails(entry: PokemonName): Promise<PokemonDetails> {
  const response = await fetch(`https://pokeapi.co/api/v2/pokemon/${entry.id}`);
  if (response.status === 404) throw new Error(`${entry.name} was not found.`);
  if (!response.ok) throw new Error(`Could not load ${entry.name}.`);
  const body = (await response.json()) as PokemonResponse;
  const types = body.types
    .slice()
    .sort((a, b) => a.slot - b.slot)
    .map((row) => row.type.name)
    .filter(isTypeName);
  return {
    id: entry.id,
    name: entry.name,
    types,
  };
}
