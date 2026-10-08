import { describe, expect, it } from "vitest";

import { findActiveSegmentIndex, playbackDurationMs } from "./transcript";

// 0–1000, gap, 1500–3000, 3000–4000 (back-to-back)
const segments = [
  { start_ms: 0, end_ms: 1000 },
  { start_ms: 1500, end_ms: 3000 },
  { start_ms: 3000, end_ms: 4000 },
];

describe("findActiveSegmentIndex", () => {
  it.each([
    [0, 0, "exactly at the first start"],
    [999, 0, "inside the first segment"],
    [1000, 0, "exactly at the first end (gap starts) — previous stays active"],
    [1250, 0, "inside a silent gap — previous stays active"],
    [1500, 1, "exactly at a start after a gap"],
    [2999, 1, "just before a back-to-back boundary"],
    [3000, 2, "exactly at a back-to-back boundary — the next segment wins"],
    [4000, 2, "exactly at the last end"],
    [99_999, 2, "after the end of the recording"],
  ])("t=%i → %i (%s)", (ms, expected) => {
    expect(findActiveSegmentIndex(segments, ms)).toBe(expected);
  });

  it("returns -1 before the first segment starts", () => {
    expect(findActiveSegmentIndex([{ start_ms: 500, end_ms: 900 }], 499)).toBe(-1);
  });

  it("returns -1 for an empty transcript", () => {
    expect(findActiveSegmentIndex([], 1000)).toBe(-1);
  });

  it("picks the last of several segments starting at the same time", () => {
    const same = [
      { start_ms: 0, end_ms: 10 },
      { start_ms: 0, end_ms: 20 },
    ];
    expect(findActiveSegmentIndex(same, 0)).toBe(1);
  });

  it("agrees with a linear scan on a long transcript", () => {
    const long = Array.from({ length: 500 }, (_, i) => ({
      start_ms: i * 700,
      end_ms: i * 700 + 600,
    }));
    for (const ms of [0, 1, 699, 700, 701, 123_456, 349_300, 400_000]) {
      const linear = long.reduce((found, s, i) => (s.start_ms <= ms ? i : found), -1);
      expect(findActiveSegmentIndex(long, ms)).toBe(linear);
    }
  });
});

describe("playbackDurationMs", () => {
  it("uses whichever is longer: stated duration or transcript end", () => {
    expect(playbackDurationMs(10, segments)).toBe(10_000);
    expect(playbackDurationMs(2, segments)).toBe(4000);
    expect(playbackDurationMs(0, [])).toBe(0);
  });
});
