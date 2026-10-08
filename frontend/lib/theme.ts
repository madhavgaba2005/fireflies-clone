// Bonus B6 — dark mode. The theme is a class on <html>; every colour is a CSS variable
// (app/globals.css), so switching themes only swaps variable values.
// The user picks a *preference* (system / light / dark); "system" follows the OS setting live.

export type Theme = "light" | "dark";
export type ThemePreference = "system" | Theme;

export const THEME_STORAGE_KEY = "lumen-theme";

/** Runs before first paint (inlined in <head>) so a dark-mode user never sees a light flash. */
export const NO_FLASH_SCRIPT = `(function(){try{var t=localStorage.getItem("${THEME_STORAGE_KEY}");if(t!=="light"&&t!=="dark"){t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.classList.toggle("dark",t==="dark")}catch(e){}})();`;

export function parseTheme(value: string | null | undefined): Theme | null {
  return value === "light" || value === "dark" ? value : null;
}

export function parsePreference(value: string | null | undefined): ThemePreference {
  return parseTheme(value) ?? "system";
}

/** An explicit choice wins; otherwise follow the operating system (same rule as NO_FLASH_SCRIPT). */
export function resolveTheme(stored: string | null | undefined, prefersDark: boolean): Theme {
  return parseTheme(stored) ?? (prefersDark ? "dark" : "light");
}

const DARK_QUERY = "(prefers-color-scheme: dark)";
const listeners = new Set<() => void>();

function readStored(): string | null {
  try {
    return localStorage.getItem(THEME_STORAGE_KEY);
  } catch {
    return null; // storage unavailable (private mode): behave as "system"
  }
}

function apply(): void {
  const theme = resolveTheme(readStored(), matchMedia(DARK_QUERY).matches);
  document.documentElement.classList.toggle("dark", theme === "dark");
  listeners.forEach((listener) => listener());
}

export function currentTheme(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

export function currentPreference(): ThemePreference {
  return parsePreference(readStored());
}

export function setThemePreference(preference: ThemePreference): void {
  try {
    if (preference === "system") localStorage.removeItem(THEME_STORAGE_KEY);
    else localStorage.setItem(THEME_STORAGE_KEY, preference);
  } catch {
    // Storage unavailable: the theme still applies for this page view.
    document.documentElement.classList.toggle(
      "dark",
      preference === "dark" || (preference === "system" && matchMedia(DARK_QUERY).matches),
    );
    listeners.forEach((listener) => listener());
    return;
  }
  apply();
}

export function subscribeToTheme(listener: () => void): () => void {
  listeners.add(listener);
  // While anyone is listening, follow OS theme changes (only matters for the "system" preference).
  const media = matchMedia(DARK_QUERY);
  media.addEventListener("change", apply);
  return () => {
    listeners.delete(listener);
    media.removeEventListener("change", apply);
  };
}
