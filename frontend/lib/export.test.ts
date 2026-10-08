import { describe, expect, it } from "vitest";

import { exportFileName, notesToText, slugify, transcriptToText } from "./export";
import type { ActionItem, MeetingDetail, Segment, Summary } from "./types";

const meeting = {
  id: 1,
  title: "Weekly Product Sync",
  meeting_date: "2026-10-08T10:00:00Z",
  duration_seconds: 278,
  participants: [
    { id: 1, name: "Priya Sharma", email: null },
    { id: 2, name: "Arjun Mehta", email: null },
  ],
} as MeetingDetail;

const segments = [
  {
    id: 1,
    sequence: 0,
    start_ms: 0,
    end_ms: 5000,
    speaker: { id: 1, name: "Priya Sharma" },
    text: "Morning.",
  },
  {
    id: 2,
    sequence: 1,
    start_ms: 75_000,
    end_ms: 80_000,
    speaker: { id: 2, name: "Arjun Mehta" },
    text: "Release is ready.",
  },
] as Segment[];

const summary: Summary = {
  meeting_id: 1,
  overview: "We reviewed the release.",
  provider: "seed",
  transcript_revision: 1,
  generated_at: "2026-10-08T10:10:00Z",
  topics: [{ sequence: 0, title: "Release", summary: "Ready to ship.", start_ms: 75_000 }],
  keywords: ["Release", "QA"],
};

const items = [
  {
    id: 1,
    title: "Ship 2.4",
    completed: true,
    assignee: { id: 2, name: "Arjun Mehta", email: null },
    due_date: "2026-10-20",
  },
  { id: 2, title: "Write changelog", completed: false, assignee: null, due_date: null },
] as ActionItem[];

describe("file names", () => {
  it("slugifies titles safely", () => {
    expect(slugify("Discovery Call — Brightline Logistics!")).toBe(
      "discovery-call-brightline-logistics",
    );
    expect(slugify("***")).toBe("meeting");
    expect(exportFileName("Weekly Product Sync", "notes", "md")).toBe(
      "weekly-product-sync-notes.md",
    );
  });
});

describe("transcriptToText", () => {
  it("includes timestamps and speakers by default-style options", () => {
    const text = transcriptToText(meeting, segments, { timestamps: true, speakers: true }, "txt");
    const lines = text.trim().split("\n");
    expect(lines[0]).toBe("Weekly Product Sync");
    expect(lines[1]).toContain("Priya Sharma, Arjun Mehta");
    expect(lines).toContain("[00:00] Priya Sharma: Morning.");
    expect(lines).toContain("[01:15] Arjun Mehta: Release is ready.");
  });

  it("respects the timestamp and speaker toggles", () => {
    const text = transcriptToText(meeting, segments, { timestamps: false, speakers: false }, "txt");
    expect(text).toContain("\nMorning.\nRelease is ready.\n");
    expect(text).not.toMatch(/\[\d\d:\d\d\]/);
  });

  it("renders Markdown with a title heading and bold speakers", () => {
    const md = transcriptToText(meeting, segments, { timestamps: true, speakers: true }, "md");
    expect(md.startsWith("# Weekly Product Sync\n")).toBe(true);
    expect(md).toContain("[01:15] **Arjun Mehta:** Release is ready.");
  });
});

describe("notesToText", () => {
  it("writes keywords, overview, outline and action items in Markdown", () => {
    const md = notesToText(meeting, summary, items, "md");
    expect(md).toContain("## Keywords\nRelease, QA");
    expect(md).toContain("## Overview\nWe reviewed the release.");
    expect(md).toContain("- **[01:15] Release** — Ready to ship.");
    expect(md).toContain("- [x] Ship 2.4 — Arjun Mehta (due 2026-10-20)");
    expect(md).toContain("- [ ] Write changelog");
  });

  it("writes plain text sections and handles missing notes and items", () => {
    const text = notesToText(meeting, undefined, [], "txt");
    expect(text).toContain("(No AI notes for this meeting yet.)");
    expect(text).toContain("ACTION ITEMS\nNone.");
  });
});
