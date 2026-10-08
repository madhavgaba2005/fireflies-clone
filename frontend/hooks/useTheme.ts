"use client";

import { useSyncExternalStore } from "react";

import { currentTheme, subscribeToTheme, type Theme } from "@/lib/theme";

/** The active theme; "light" during server rendering (the no-flash script fixes the first paint). */
export function useTheme(): Theme {
  return useSyncExternalStore(subscribeToTheme, currentTheme, () => "light");
}
