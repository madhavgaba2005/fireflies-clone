"use client";

import { useSyncExternalStore } from "react";

import {
  currentPreference,
  currentTheme,
  subscribeToTheme,
  type Theme,
  type ThemePreference,
} from "@/lib/theme";

/** The active theme; "light" during server rendering (the no-flash script fixes the first paint). */
export function useTheme(): Theme {
  return useSyncExternalStore(subscribeToTheme, currentTheme, () => "light");
}

/** What the user chose: system, light or dark. */
export function useThemePreference(): ThemePreference {
  return useSyncExternalStore(subscribeToTheme, currentPreference, () => "system");
}
