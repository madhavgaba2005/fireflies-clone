// Library filter state lives in the URL (shareable, survives refresh). This module converts
// between URL search params and the API query.
import type { MeetingQuery } from "./types";

export type DatePreset = "any" | "today" | "7d" | "30d" | "custom";

export const DATE_PRESETS: { value: DatePreset; label: string }[] = [
  { value: "any", label: "Any time" },
  { value: "today", label: "Today" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "custom", label: "Custom range" },
];

export interface LibraryFilters {
  q: string;
  participantIds: number[];
  date: DatePreset;
  from: string; // YYYY-MM-DD, custom range only
  to: string;
  sort: "newest" | "oldest";
  keyword: string;
}

export const EMPTY_FILTERS: LibraryFilters = {
  q: "",
  participantIds: [],
  date: "any",
  from: "",
  to: "",
  sort: "newest",
  keyword: "",
};

/** "YYYY-MM-DD" for a local calendar day. */
export function isoDay(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function daysAgo(now: Date, days: number): Date {
  return new Date(now.getFullYear(), now.getMonth(), now.getDate() - days);
}

export function dateRange(
  filters: LibraryFilters,
  now: Date = new Date(),
): { from?: string; to?: string } {
  switch (filters.date) {
    case "today":
      return { from: isoDay(now), to: isoDay(now) };
    case "7d":
      return { from: isoDay(daysAgo(now, 6)), to: isoDay(now) };
    case "30d":
      return { from: isoDay(daysAgo(now, 29)), to: isoDay(now) };
    case "custom":
      return { from: filters.from || undefined, to: filters.to || undefined };
    default:
      return {};
  }
}

export function parseFilters(params: URLSearchParams): LibraryFilters {
  const date = params.get("date") as DatePreset | null;
  return {
    q: params.get("q") ?? "",
    participantIds: params
      .getAll("participant")
      .map(Number)
      .filter((id) => Number.isInteger(id) && id > 0),
    date: date && DATE_PRESETS.some((p) => p.value === date) ? date : "any",
    from: params.get("from") ?? "",
    to: params.get("to") ?? "",
    sort: params.get("sort") === "oldest" ? "oldest" : "newest",
    keyword: params.get("keyword") ?? "",
  };
}

export function filtersToParams(filters: LibraryFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.q.trim()) params.set("q", filters.q.trim());
  for (const id of filters.participantIds) params.append("participant", String(id));
  if (filters.date !== "any") params.set("date", filters.date);
  if (filters.date === "custom" && filters.from) params.set("from", filters.from);
  if (filters.date === "custom" && filters.to) params.set("to", filters.to);
  if (filters.sort === "oldest") params.set("sort", "oldest");
  if (filters.keyword) params.set("keyword", filters.keyword);
  return params;
}

export function toMeetingQuery(filters: LibraryFilters, now: Date = new Date()): MeetingQuery {
  const { from, to } = dateRange(filters, now);
  return {
    q: filters.q,
    participantIds: filters.participantIds,
    dateFrom: from,
    dateTo: to,
    keyword: filters.keyword || undefined,
    sort: filters.sort === "oldest" ? "meeting_date" : "-meeting_date",
  };
}

export function hasActiveFilters(filters: LibraryFilters): boolean {
  return (
    filters.q.trim() !== "" ||
    filters.participantIds.length > 0 ||
    filters.date !== "any" ||
    filters.keyword !== ""
  );
}
