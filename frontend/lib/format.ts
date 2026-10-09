// Display formatting. Pure functions — unit tested in format.test.ts.

/** 75_000 → "01:15"; 3_725_000 → "1:02:05". */
export function formatTimestamp(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const mm = String(minutes).padStart(2, "0");
  const ss = String(seconds).padStart(2, "0");
  return hours > 0 ? `${hours}:${mm}:${ss}` : `${mm}:${ss}`;
}

/** 278 → "5 min"; 45 → "1 min"; 3900 → "1 hr 5 min"; 0 → "—". */
export function formatDuration(seconds: number): string {
  if (seconds <= 0) return "—";
  const minutes = Math.max(1, Math.round(seconds / 60));
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours} hr ${rest} min` : `${hours} hr`;
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** Library group heading: "Today", "Yesterday" or "Mon, Oct 5". */
const shortDay = (date: Date) =>
  date.toLocaleDateString(undefined, { month: "short", day: "numeric" });

/** Library date column, e.g. "Wed, Oct 7". */
export function formatShortDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

/** Sunday that starts the local calendar week containing `date`. */
function startOfWeek(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() - date.getDay());
}

/** Fireflies-style week heading: "Oct 4 – Today" for this week, "Sep 27 – Oct 3, 2026" before. */
export function weekLabel(iso: string, now: Date = new Date()): string {
  const start = startOfWeek(new Date(iso));
  if (start.getTime() === startOfWeek(now).getTime()) return `${shortDay(start)} – Today`;
  const end = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 6);
  return `${shortDay(start)} – ${shortDay(end)}, ${end.getFullYear()}`;
}

/** Groups items (already sorted) by calendar week, keeping order. */
export function groupByWeek<T>(
  items: T[],
  getDate: (item: T) => string,
  now: Date = new Date(),
): { label: string; items: T[] }[] {
  const groups: { label: string; items: T[] }[] = [];
  for (const item of items) {
    const label = weekLabel(getDate(item), now);
    const last = groups.at(-1);
    if (last && last.label === label) last.items.push(item);
    else groups.push({ label, items: [item] });
  }
  return groups;
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  const first = parts[0][0];
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase();
}

/** Value for <input type="datetime-local"> from an ISO string (local time). */
export function toDateTimeLocal(iso: string | Date): string {
  const date = typeof iso === "string" ? new Date(iso) : iso;
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

/** "2026-10-08T14:30" (local) → ISO string with timezone, as the API requires. */
export function fromDateTimeLocal(value: string): string {
  return new Date(value).toISOString();
}
