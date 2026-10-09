import { describe, expect, it } from "vitest";

import {
  NO_FLASH_SCRIPT,
  THEME_STORAGE_KEY,
  parsePreference,
  parseTheme,
  resolveTheme,
} from "./theme";

describe("theme", () => {
  it("accepts only known theme values", () => {
    expect(parseTheme("dark")).toBe("dark");
    expect(parseTheme("light")).toBe("light");
    expect(parseTheme("purple")).toBeNull();
    expect(parseTheme(null)).toBeNull();
  });

  it("defaults to Light when nothing (or something unknown) is saved", () => {
    expect(parsePreference(null)).toBe("light");
    expect(parsePreference("garbage")).toBe("light");
    expect(parsePreference("dark")).toBe("dark");
    expect(parsePreference("system")).toBe("system");
  });

  it("resolves Light by default, Dark when chosen, and the OS only for System", () => {
    expect(resolveTheme(null, true)).toBe("light"); // new visitor on a dark OS still gets Light
    expect(resolveTheme("light", true)).toBe("light");
    expect(resolveTheme("dark", false)).toBe("dark");
    expect(resolveTheme("system", true)).toBe("dark");
    expect(resolveTheme("system", false)).toBe("light");
  });

  function runPrePaintScript(stored: string | null, osDark: boolean): Set<string> {
    const classes = new Set<string>();
    const fake = {
      localStorage: { getItem: (key: string) => (key === THEME_STORAGE_KEY ? stored : null) },
      matchMedia: () => ({ matches: osDark }),
      document: {
        documentElement: {
          classList: {
            toggle: (name: string, on: boolean) => (on ? classes.add(name) : classes.delete(name)),
          },
        },
      },
    };
    new Function("localStorage", "matchMedia", "document", NO_FLASH_SCRIPT)(
      fake.localStorage,
      fake.matchMedia,
      fake.document,
    );
    return classes;
  }

  it("the pre-paint script applies the same rules before React loads", () => {
    expect(runPrePaintScript("dark", false).has("dark")).toBe(true);
    expect(runPrePaintScript(null, true).has("dark")).toBe(false);
    expect(runPrePaintScript("system", true).has("dark")).toBe(true);
    expect(runPrePaintScript("light", true).has("dark")).toBe(false);
  });
});
