"use client";

import { useEffect, useState, useSyncExternalStore } from "react";

import { type PlaybackClock, SimulatedClock } from "@/lib/playback";

/**
 * One clock per workspace. Components re-render from its snapshots via useSyncExternalStore.
 * Swapping SimulatedClock for a media-element clock here is the only change real audio needs.
 */
export function usePlaybackClock(durationMs: number): {
  clock: PlaybackClock;
  state: ReturnType<PlaybackClock["getSnapshot"]>;
} {
  const [clock] = useState<PlaybackClock>(() => new SimulatedClock(durationMs));
  useEffect(() => clock.setDuration(durationMs), [clock, durationMs]);
  useEffect(() => () => clock.destroy(), [clock]);
  const state = useSyncExternalStore(clock.subscribe, clock.getSnapshot, clock.getSnapshot);
  return { clock, state };
}
