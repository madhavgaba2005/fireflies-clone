// Bonus B6 — dark mode. The theme is a class on <html>; every colour is a CSS variable
// (app/globals.css), so switching themes only swaps variable values.
export type Theme = "light" | "dark";

export const THEME_STORAGE_KEY = "lumen-theme";

/** Runs before first paint (inlined in <head>) so a dark-mode user never sees a light flash. */
export const NO_FLASH_SCRIPT = `(function(){try{var t=localStorage.getItem("${THEME_STORAGE_KEY}");if(t!=="light"&&t!=="dark"){t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.classList.toggle("dark",t==="dark")}catch(e){}})();`;

export function parseTheme(value: string | null | undefined): Theme | null {
  return value === "light" || value === "dark" ? value : null;
}

/** An explicit choice wins; otherwise follow the operating system (same rule as NO_FLASH_SCRIPT). */
export function resolveTheme(stored: string | null | undefined, prefersDark: boolean): Theme {
  return parseTheme(stored) ?? (prefersDark ? "dark" : "light");
}

const listeners = new Set<() => void>();

export function currentTheme(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

export function setTheme(theme: Theme): void {
  document.documentElement.classList.toggle("dark", theme === "dark");
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Storage can be unavailable (private mode); the theme still applies for this page view.
  }
  listeners.forEach((listener) => listener());
}

export function subscribeToTheme(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
