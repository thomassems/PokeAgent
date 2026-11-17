"use client";

import { useSyncExternalStore } from "react";

export const GAMES = ["main", "go"] as const;

export type Game = (typeof GAMES)[number];

const STORAGE_KEY = "pokeagent.game";
const listeners = new Set<() => void>();
let current: Game = "main";
let loaded = false;

/** Missing or unknown storage stays on the main series. */
export function parseStoredGame(stored: string | null): Game {
  return stored === "go" ? "go" : "main";
}

function readStoredGame(): Game {
  if (loaded) return current;
  loaded = true;
  try {
    current = parseStoredGame(window.localStorage.getItem(STORAGE_KEY));
  } catch {
    current = "main";
  }
  return current;
}

function serverGame(): Game {
  return "main";
}

function emit() {
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

/**
 * The chat page remembers which game is selected. The team builder does not
 * read this: it stays on the main series.
 */
export function useSharedGame(): readonly [Game, (game: Game) => void] {
  const game = useSyncExternalStore(subscribe, readStoredGame, serverGame);

  const update = (next: Game) => {
    current = next;
    loaded = true;
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // The chip still updates in this tab when storage is blocked.
    }
    emit();
  };

  return [game, update];
}
