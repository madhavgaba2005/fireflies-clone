import { describe, expect, it } from "vitest";

import { NO_FLASH_SCRIPT, THEME_STORAGE_KEY, parseTheme, resolveTheme } from "./theme";

describe("theme", () => {
  it("accepts only known theme values", () => {
    expect(parseTheme("dark")).toBe("dark");
    expect(parseTheme("light")).toBe("light");
    expect(parseTheme("purple")).toBeNull();
    expect(parseTheme(null)).toBeNull();
  });

  it("prefers the stored choice, then the system preference", () => {
    expect(resolveTheme("light", true)).toBe("light");
    expect(resolveTheme("dark", false)).toBe("dark");
    expect(resolveTheme(null, true)).toBe("dark");
    expect(resolveTheme("garbage", false)).toBe("light");
  });

  it("the pre-paint script applies the stored theme to <html>", () => {
    const classes = new Set<string>();
    const fakeWindow = {
      localStorage: { getItem: (key: string) => (key === THEME_STORAGE_KEY ? "dark" : null) },
      matchMedia: () => ({ matches: false }),
      document: {
        documentElement: {
          classList: {
            toggle: (name: string, on: boolean) => (on ? classes.add(name) : classes.delete(name)),
          },
        },
      },
    };
    new Function("localStorage", "matchMedia", "document", NO_FLASH_SCRIPT)(
      fakeWindow.localStorage,
      fakeWindow.matchMedia,
      fakeWindow.document,
    );
    expect(classes.has("dark")).toBe(true);
  });
});
