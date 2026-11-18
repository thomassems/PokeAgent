"use client";

import { createContext, useContext, type ReactNode } from "react";

const DEFAULT_APP_NAME = "Trainermon";

const AppNameContext = createContext(DEFAULT_APP_NAME);

export function AppNameProvider({
  name,
  children,
}: {
  name: string;
  children: ReactNode;
}) {
  return <AppNameContext.Provider value={name}>{children}</AppNameContext.Provider>;
}

export function useAppName(): string {
  return useContext(AppNameContext);
}
