"use client";

import { useEffect, useId, useRef, useState } from "react";
import {
  loadPokemonDetails,
  loadPokemonNames,
  searchPokemonNames,
  type PokemonName,
} from "@/lib/pokeapi";
import type { SlotPokemon } from "@/lib/types";

type PokemonPickerProps = {
  slotIndex: number | null;
  onSelect: (pokemon: SlotPokemon) => void;
  onClose: () => void;
};

export function PokemonPicker({ slotIndex, onSelect, onClose }: PokemonPickerProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const isOpen = slotIndex !== null;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (isOpen && !dialog.open) dialog.showModal();
    if (!isOpen && dialog.open) dialog.close();
    if (isOpen) dialog.querySelector<HTMLInputElement>("#pokemon-search")?.focus();
  }, [isOpen]);

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose();
      }}
      aria-labelledby="picker-title"
      className="m-auto w-[min(28rem,calc(100vw-2rem))] rounded-md border border-shell-700 bg-shell-900 p-0 text-ink-100 backdrop:bg-shell-950/70"
    >
      <div className="flex items-center justify-between border-b border-shell-800 px-4 py-3">
        <h2 id="picker-title" className="text-sm font-semibold">
          {slotIndex === null ? "Choose a Pokémon" : `Choose for slot ${slotIndex + 1}`}
        </h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close picker"
          className="rounded-sm px-2 py-1 text-ink-500 transition-colors hover:bg-shell-800 hover:text-ink-100"
        >
          <span aria-hidden>✕</span>
        </button>
      </div>
      {slotIndex !== null && (
        <PokemonSearch key={slotIndex} onSelect={onSelect} />
      )}
    </dialog>
  );
}

function PokemonSearch({ onSelect }: { onSelect: (pokemon: SlotPokemon) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();
  const [query, setQuery] = useState("");
  const [names, setNames] = useState<readonly PokemonName[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [activeIndex, setActiveIndex] = useState(0);
  const [adding, setAdding] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const alive = useRef(true);

  const suggestions = names ? searchPokemonNames(names, query) : [];
  const highlighted =
    suggestions.length === 0 ? 0 : Math.min(activeIndex, suggestions.length - 1);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    loadPokemonNames()
      .then((loaded) => {
        if (!cancelled) {
          setNames(loaded);
          setLoadError(null);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setLoadError(error instanceof Error ? error.message : "Could not load Pokémon names.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [loadAttempt]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const choose = async (entry: PokemonName) => {
    if (adding) return;
    setAdding(entry.name);
    setActionError(null);
    try {
      const details = await loadPokemonDetails(entry);
      if (!alive.current) return;
      onSelect({
        id: String(details.id),
        name: details.name,
        types: details.types,
      });
    } catch (error) {
      if (!alive.current) return;
      setActionError(error instanceof Error ? error.message : `Could not load ${entry.name}.`);
      setAdding(null);
    }
  };

  const status = (() => {
    if (adding) return `Adding ${adding}…`;
    if (actionError) return actionError;
    if (loadError) return loadError;
    if (!names) return "Loading Pokémon names…";
    if (query.trim().length >= 2 && suggestions.length === 0) {
      return `No Pokémon named "${query.trim()}".`;
    }
    return null;
  })();

  return (
    <div className="px-4 py-3">
      <label htmlFor="pokemon-search" className="sr-only">
        Search Pokémon by name
      </label>
      <input
        ref={inputRef}
        id="pokemon-search"
        role="combobox"
        aria-expanded={suggestions.length > 0}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={
          suggestions[highlighted] ? `${listId}-${suggestions[highlighted].id}` : undefined
        }
        value={query}
        disabled={adding !== null}
        autoComplete="off"
        spellCheck={false}
        placeholder="Search by name"
        onChange={(event) => {
          setQuery(event.target.value);
          setActiveIndex(0);
          setActionError(null);
        }}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setActiveIndex((index) => Math.min(index + 1, Math.max(suggestions.length - 1, 0)));
          } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setActiveIndex((index) => Math.max(index - 1, 0));
          } else if (event.key === "Enter" && suggestions[highlighted]) {
            event.preventDefault();
            void choose(suggestions[highlighted]);
          }
        }}
        className="w-full rounded-sm border border-shell-700 bg-shell-800 px-3 py-2 text-sm text-ink-100 placeholder:text-ink-500 disabled:opacity-60"
      />

      {status && (
        <p className="mt-3 flex items-center justify-between gap-3 text-sm text-ink-500" role="status">
          <span>{status}</span>
          {loadError && (
            <button
              type="button"
              onClick={() => setLoadAttempt((attempt) => attempt + 1)}
              className="shrink-0 rounded-sm px-2 py-1 text-ink-100 hover:bg-shell-800"
            >
              Try again
            </button>
          )}
        </p>
      )}

      {suggestions.length > 0 && (
        <ul id={listId} role="listbox" aria-label="Matching Pokémon" className="mt-2 space-y-1">
          {suggestions.map((entry, index) => (
            <li key={entry.id}>
              <button
                id={`${listId}-${entry.id}`}
                type="button"
                role="option"
                aria-selected={index === highlighted}
                disabled={adding !== null}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => void choose(entry)}
                className={`flex w-full items-center justify-between rounded-sm px-2 py-1.5 text-left text-sm ${
                  index === highlighted ? "bg-shell-800" : "hover:bg-shell-800"
                }`}
              >
                <span>{entry.name}</span>
                <span className="font-mono text-xs text-ink-500">#{entry.id}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
