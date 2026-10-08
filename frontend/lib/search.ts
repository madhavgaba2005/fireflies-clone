// In-transcript search. Plain substring matching (no RegExp), so user input like "(" or "$"
// can't break anything, and highlights are rendered as React elements — never as HTML.

export interface Match {
  segmentIndex: number;
  start: number;
  end: number;
}

export interface Fragment {
  text: string;
  match: boolean;
  current: boolean;
}

/** Every case-insensitive occurrence of `query`, in reading order. */
export function findMatches(texts: readonly string[], query: string): Match[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return [];
  const matches: Match[] = [];
  texts.forEach((text, segmentIndex) => {
    const haystack = text.toLowerCase();
    let from = 0;
    for (;;) {
      const start = haystack.indexOf(needle, from);
      if (start === -1) break;
      matches.push({ segmentIndex, start, end: start + needle.length });
      from = start + needle.length;
    }
  });
  return matches;
}

/** Splits one segment's text into plain and highlighted fragments. */
export function splitByMatches(
  text: string,
  ranges: readonly { start: number; end: number }[],
  currentStart: number | null = null,
): Fragment[] {
  const fragments: Fragment[] = [];
  let cursor = 0;
  for (const { start, end } of ranges) {
    if (start > cursor)
      fragments.push({ text: text.slice(cursor, start), match: false, current: false });
    fragments.push({ text: text.slice(start, end), match: true, current: start === currentStart });
    cursor = end;
  }
  if (cursor < text.length)
    fragments.push({ text: text.slice(cursor), match: false, current: false });
  return fragments;
}

/** Wraps around in both directions: next after the last is the first. */
export function stepMatch(current: number, total: number, direction: 1 | -1): number {
  if (total === 0) return -1;
  if (current < 0) return direction === 1 ? 0 : total - 1;
  return (current + direction + total) % total;
}
