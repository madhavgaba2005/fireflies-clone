// Player → transcript synchronization: which segment is active at time `ms`?

export interface Timed {
  start_ms: number;
  end_ms: number;
}

/**
 * Index of the segment that is active at `ms`, or -1 before the first segment.
 *
 * Rules (each one unit-tested):
 * - a segment is active from its start (inclusive) until the next segment starts;
 *   at exactly `next.start_ms` the next segment wins — no flicker, no double highlight
 * - in a silent gap between segments, the previous segment stays active
 * - after the last segment ends, the last segment stays active
 *
 * Binary search over start times: O(log n) per playback tick. Segments must be sorted by
 * `start_ms`, which the API guarantees (ordered by sequence, non-decreasing times).
 */
export function findActiveSegmentIndex(segments: readonly Timed[], ms: number): number {
  let low = 0;
  let high = segments.length - 1;
  let found = -1;
  while (low <= high) {
    const mid = (low + high) >>> 1;
    if (segments[mid].start_ms <= ms) {
      found = mid;
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }
  return found;
}

/** Length of the recording: the larger of the stated duration and the transcript's end. */
export function playbackDurationMs(durationSeconds: number, segments: readonly Timed[]): number {
  const transcriptEnd = segments.length ? segments[segments.length - 1].end_ms : 0;
  return Math.max(durationSeconds * 1000, transcriptEnd);
}
