"use client";

import { useSyncExternalStore } from "react";
import { GENERATIONS, type Generation } from "./types";

const STORAGE_KEY = "trainermon.generation";
const listeners = new Set<() => void>();
let current: Generation | null = null;
let loaded = false;

function readStoredGeneration(): Generation | null {
  if (loaded) return current;
  loaded = true;
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    const value = Number(stored);
    current =
      stored && GENERATIONS.includes(value as Generation) ? (value as Generation) : null;
  } catch {
    current = null;
  }
  return current;
}

function serverGeneration(): Generation | null {
  return null;
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
 * The chat page and the team builder share one selection. Nothing is selected
 * until the user picks a generation, and that choice survives navigation.
 */
export function useSharedGeneration(): readonly [
  Generation | null,
  (generation: Generation | null) => void,
] {
  const generation = useSyncExternalStore(subscribe, readStoredGeneration, serverGeneration);

  const update = (next: Generation | null) => {
    current = next;
    loaded = true;
    try {
      if (next === null) window.localStorage.removeItem(STORAGE_KEY);
      else window.localStorage.setItem(STORAGE_KEY, String(next));
    } catch {
      // The chip still updates in this tab when storage is blocked.
    }
    emit();
  };

  return [generation, update];
}
