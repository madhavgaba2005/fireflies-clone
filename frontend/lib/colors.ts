// Each person keeps the same colour everywhere (avatar, transcript name, speaker timeline),
// derived from their id so it's stable across pages and reloads.

const SPEAKER_COLORS = [
  "#7c3aed", // violet
  "#0891b2", // cyan
  "#db2777", // pink
  "#ea580c", // orange
  "#16a34a", // green
  "#2563eb", // blue
  "#ca8a04", // amber
  "#9333ea", // purple
] as const;

export function speakerColor(id: number): string {
  return SPEAKER_COLORS[Math.abs(id) % SPEAKER_COLORS.length];
}

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}
