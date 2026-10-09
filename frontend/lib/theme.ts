// Bonus B6 — dark mode. The theme is a class on <html>; every colour is a CSS variable
// (app/globals.css), so switching themes only swaps variable values.
// The user picks a *preference* (system / light / dark); "system" follows the OS setting live.
// With no saved preference the app is LIGHT (the default for new visitors), regardless of the OS.

export type Theme = "light" | "dark";
export type ThemePreference = "system" | Theme;

export const THEME_STORAGE_KEY = "lumen-theme";

/** Runs before first paint (inlined in <head>) so a dark-mode user never sees a light flash. */
export const NO_FLASH_SCRIPT = `(function(){try{var t=localStorage.getItem("${THEME_STORAGE_KEY}");var d=t==="dark"||(t==="system"&&matchMedia("(prefers-color-scheme: dark)").matches);document.documentElement.classList.toggle("dark",d)}catch(e){}})();`;

export function parseTheme(value: string | null | undefined): Theme | null {
  return value === "light" || value === "dark" ? value : null;
}

/** Saved preference; anything missing or unknown means the default, Light. */
export function parsePreference(value: string | null | undefined): ThemePreference {
  return value === "system" ? "system" : (parseTheme(value) ?? "light");
}

/** Light unless the user chose Dark, or chose System on a dark OS (same rule as NO_FLASH_SCRIPT). */
export function resolveTheme(stored: string | null | undefined, prefersDark: boolean): Theme {
  const preference = parsePreference(stored);
  if (preference === "system") return prefersDark ? "dark" : "light";
  return preference;
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
    localStorage.setItem(THEME_STORAGE_KEY, preference); // "system" is stored too: no key = Light
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
