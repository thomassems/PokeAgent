"use client";

import { useSyncExternalStore } from "react";

export const GO_ACCENTS = ["neutral", "blue", "red", "yellow"] as const;

export type GoAccent = (typeof GO_ACCENTS)[number];

const STORAGE_KEY = "trainermon.goAccent";
const listeners = new Set<() => void>();
let current: GoAccent = "neutral";
let loaded = false;

/** Missing or unknown storage stays on the neutral accent. */
export function parseStoredAccent(stored: string | null): GoAccent {
  return GO_ACCENTS.includes(stored as GoAccent) ? (stored as GoAccent) : "neutral";
}

function readStoredAccent(): GoAccent {
  if (loaded) return current;
  loaded = true;
  try {
    current = parseStoredAccent(window.localStorage.getItem(STORAGE_KEY));
  } catch {
    current = "neutral";
  }
  return current;
}

function serverAccent(): GoAccent {
  return "neutral";
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

/** Chat-only decoration. The team builder does not read this. */
export function useSharedAccent(): readonly [GoAccent, (accent: GoAccent) => void] {
  const accent = useSyncExternalStore(subscribe, readStoredAccent, serverAccent);

  const update = (next: GoAccent) => {
    current = next;
    loaded = true;
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // The chip still updates in this tab when storage is blocked.
    }
    emit();
  };

  return [accent, update];
}
