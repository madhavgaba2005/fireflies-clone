import { describe, expect, it } from "vitest";

import { speakerColor } from "./colors";
import {
  dateRange,
  EMPTY_FILTERS,
  filtersToParams,
  hasActiveFilters,
  isoDay,
  parseFilters,
  toMeetingQuery,
} from "./filters";
import { dayLabel, formatDuration, formatTimestamp, groupByDay, initials } from "./format";
import { meetingSearchParams } from "./endpoints";

describe("formatTimestamp", () => {
  it.each([
    [0, "00:00"],
    [999, "00:00"],
    [75_000, "01:15"],
    [3_599_999, "59:59"],
    [3_725_000, "1:02:05"],
    [-5, "00:00"],
  ])("%i ms → %s", (ms, expected) => {
    expect(formatTimestamp(ms)).toBe(expected);
  });
});

describe("formatDuration", () => {
  it.each([
    [0, "—"],
    [20, "1 min"],
    [278, "5 min"],
    [3600, "1 hr"],
    [3900, "1 hr 5 min"],
  ])("%i s → %s", (seconds, expected) => {
    expect(formatDuration(seconds)).toBe(expected);
  });
});

describe("day grouping", () => {
  const now = new Date(2026, 9, 9, 12, 0);

  it("labels today and yesterday by local calendar day", () => {
    expect(dayLabel(new Date(2026, 9, 9, 0, 5).toISOString(), now)).toBe("Today");
    expect(dayLabel(new Date(2026, 9, 8, 23, 59).toISOString(), now)).toBe("Yesterday");
    expect(dayLabel(new Date(2026, 9, 5, 10).toISOString(), now)).not.toMatch(/Today|Yesterday/);
  });

  it("groups consecutive items of the same day, keeping order", () => {
    const items = [
      new Date(2026, 9, 9, 11).toISOString(),
      new Date(2026, 9, 9, 9).toISOString(),
      new Date(2026, 9, 8, 15).toISOString(),
    ];
    const groups = groupByDay(items, (d) => d, now);
    expect(groups.map((g) => [g.label, g.items.length])).toEqual([
      ["Today", 2],
      ["Yesterday", 1],
    ]);
  });
});

describe("initials and colours", () => {
  it("uses first and last name initials", () => {
    expect(initials("Priya Sharma")).toBe("PS");
    expect(initials("Mary Jane Watson")).toBe("MW");
    expect(initials("kim")).toBe("K");
    expect(initials("  ")).toBe("?");
  });

  it("gives each person a stable colour", () => {
    expect(speakerColor(3)).toBe(speakerColor(3));
    expect(speakerColor(1)).not.toBe(speakerColor(2));
  });
});

describe("library filters", () => {
  const now = new Date(2026, 9, 9, 12, 0);

  it("round-trips through the URL", () => {
    const filters = {
      ...EMPTY_FILTERS,
      q: "sync",
      participantIds: [2, 5],
      date: "custom" as const,
      from: "2026-10-01",
      to: "2026-10-05",
      sort: "oldest" as const,
      keyword: "Activation",
    };
    expect(parseFilters(filtersToParams(filters))).toEqual(filters);
  });

  it("ignores junk in the URL", () => {
    const parsed = parseFilters(new URLSearchParams("participant=abc&participant=-1&date=forever"));
    expect(parsed).toEqual(EMPTY_FILTERS);
  });

  it("turns presets into inclusive day ranges", () => {
    expect(dateRange({ ...EMPTY_FILTERS, date: "today" }, now)).toEqual({
      from: "2026-10-09",
      to: "2026-10-09",
    });
    expect(dateRange({ ...EMPTY_FILTERS, date: "7d" }, now)).toEqual({
      from: "2026-10-03",
      to: "2026-10-09",
    });
    expect(dateRange({ ...EMPTY_FILTERS, date: "30d" }, now).from).toBe("2026-09-10");
    expect(dateRange(EMPTY_FILTERS, now)).toEqual({});
    expect(isoDay(new Date(2026, 0, 5))).toBe("2026-01-05");
  });

  it("builds the API query", () => {
    const query = toMeetingQuery(
      { ...EMPTY_FILTERS, q: " x ", participantIds: [3], sort: "oldest" },
      now,
    );
    const params = meetingSearchParams(query);
    expect(params.get("q")).toBe("x");
    expect(params.getAll("participant_id")).toEqual(["3"]);
    expect(params.get("sort")).toBe("meeting_date");
    expect(params.has("date_from")).toBe(false);
  });

  it("knows when any filter is active", () => {
    expect(hasActiveFilters(EMPTY_FILTERS)).toBe(false);
    expect(hasActiveFilters({ ...EMPTY_FILTERS, sort: "oldest" })).toBe(false);
    expect(hasActiveFilters({ ...EMPTY_FILTERS, participantIds: [1] })).toBe(true);
  });
});
