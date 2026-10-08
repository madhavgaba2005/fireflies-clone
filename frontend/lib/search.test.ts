import { describe, expect, it } from "vitest";

import { findMatches, splitByMatches, stepMatch } from "./search";

const texts = ["The budget is tight.", "No match here", "Budget, budget, BUDGET!"];

describe("findMatches", () => {
  it("finds every case-insensitive occurrence in reading order", () => {
    expect(findMatches(texts, "budget")).toEqual([
      { segmentIndex: 0, start: 4, end: 10 },
      { segmentIndex: 2, start: 0, end: 6 },
      { segmentIndex: 2, start: 8, end: 14 },
      { segmentIndex: 2, start: 16, end: 22 },
    ]);
  });

  it("returns nothing for an empty or whitespace query", () => {
    expect(findMatches(texts, "")).toEqual([]);
    expect(findMatches(texts, "   ")).toEqual([]);
  });

  it("returns nothing when there is no match", () => {
    expect(findMatches(texts, "roadmap")).toEqual([]);
  });

  it("treats regex characters literally", () => {
    expect(findMatches(["cost (est.) $5.00", "a.b"], "(est.)")).toEqual([
      { segmentIndex: 0, start: 5, end: 11 },
    ]);
    expect(findMatches(["a.b", "axb"], ".")).toHaveLength(1);
  });

  it("does not report overlapping matches twice", () => {
    expect(findMatches(["aaaa"], "aa")).toHaveLength(2);
  });

  it("trims the query", () => {
    expect(findMatches(texts, "  tight ")).toHaveLength(1);
  });
});

describe("splitByMatches", () => {
  it("keeps all text and marks matches and the current match", () => {
    const fragments = splitByMatches(
      texts[2],
      [
        { start: 0, end: 6 },
        { start: 8, end: 14 },
      ],
      8,
    );
    expect(fragments).toEqual([
      { text: "Budget", match: true, current: false },
      { text: ", ", match: false, current: false },
      { text: "budget", match: true, current: true },
      { text: ", BUDGET!", match: false, current: false },
    ]);
    expect(fragments.map((f) => f.text).join("")).toBe(texts[2]);
  });

  it("returns the whole text when there are no ranges", () => {
    expect(splitByMatches("hello", [])).toEqual([{ text: "hello", match: false, current: false }]);
  });

  it("handles a match covering the whole text", () => {
    expect(splitByMatches("hi", [{ start: 0, end: 2 }])).toEqual([
      { text: "hi", match: true, current: false },
    ]);
  });
});

describe("stepMatch", () => {
  it("wraps around in both directions", () => {
    expect(stepMatch(2, 3, 1)).toBe(0);
    expect(stepMatch(0, 3, -1)).toBe(2);
    expect(stepMatch(1, 3, 1)).toBe(2);
  });

  it("starts from the first (next) or last (previous) match", () => {
    expect(stepMatch(-1, 3, 1)).toBe(0);
    expect(stepMatch(-1, 3, -1)).toBe(2);
  });

  it("returns -1 when there are no matches", () => {
    expect(stepMatch(0, 0, 1)).toBe(-1);
  });
});
