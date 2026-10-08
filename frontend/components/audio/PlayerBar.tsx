"use client";

import { Info, Pause, Play, RotateCcw, RotateCw } from "lucide-react";
import { memo, useMemo } from "react";

import { Menu, MenuItem } from "@/components/ui/Menu";
import { speakerColor } from "@/lib/colors";
import { formatTimestamp } from "@/lib/format";
import { PLAYBACK_RATES, type PlaybackClock, type PlaybackState } from "@/lib/playback";
import type { Segment } from "@/lib/types";

export const SKIP_MS = 15_000;

/** Coloured blocks under the seek bar: who spoke when (a recognisable Fireflies cue). */
const SpeakerTimeline = memo(function SpeakerTimeline({
  segments,
  durationMs,
}: {
  segments: Segment[];
  durationMs: number;
}) {
  if (!durationMs) return null;
  return (
    <div
      className="pointer-events-none absolute inset-x-0 top-1/2 h-1.5 -translate-y-1/2 overflow-hidden rounded-full bg-surface-muted"
      aria-hidden
    >
      {segments.map((segment) => (
        <span
          key={segment.id}
          className="absolute top-0 h-full opacity-40"
          style={{
            left: `${(segment.start_ms / durationMs) * 100}%`,
            width: `${Math.max(0.3, ((segment.end_ms - segment.start_ms) / durationMs) * 100)}%`,
            backgroundColor: speakerColor(segment.speaker.id),
          }}
        />
      ))}
    </div>
  );
});

export function PlayerBar({
  state,
  clock,
  segments,
}: {
  state: PlaybackState;
  clock: PlaybackClock;
  segments: Segment[];
}) {
  const progress = state.durationMs ? (state.currentMs / state.durationMs) * 100 : 0;
  const speakers = useMemo(
    () => [...new Map(segments.map((s) => [s.speaker.id, s.speaker])).values()],
    [segments],
  );

  return (
    <div
      className="flex shrink-0 items-center gap-3 border-t border-border bg-surface px-4 py-2.5 sm:gap-4"
      data-testid="player"
    >
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => clock.seek(state.currentMs - SKIP_MS)}
          aria-label="Back 15 seconds"
          className="rounded-full p-2 text-muted hover:bg-surface-muted hover:text-text"
        >
          <RotateCcw size={17} />
        </button>
        <button
          type="button"
          onClick={clock.toggle}
          disabled={!state.durationMs}
          aria-label={state.playing ? "Pause" : "Play"}
          className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white shadow-sm transition hover:bg-primary-hover disabled:opacity-40"
        >
          {state.playing ? (
            <Pause size={18} fill="currentColor" />
          ) : (
            <Play size={18} fill="currentColor" className="ml-0.5" />
          )}
        </button>
        <button
          type="button"
          onClick={() => clock.seek(state.currentMs + SKIP_MS)}
          aria-label="Forward 15 seconds"
          className="rounded-full p-2 text-muted hover:bg-surface-muted hover:text-text"
        >
          <RotateCw size={17} />
        </button>
      </div>

      <span
        className="tabular w-[92px] shrink-0 text-[12.5px] text-muted"
        data-testid="player-time"
      >
        <span className="font-semibold text-text">{formatTimestamp(state.currentMs)}</span> /{" "}
        {formatTimestamp(state.durationMs)}
      </span>

      <div className="relative flex h-6 min-w-0 flex-1 items-center">
        <SpeakerTimeline segments={segments} durationMs={state.durationMs} />
        <div
          className="pointer-events-none absolute left-0 top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-primary"
          style={{ width: `${progress}%` }}
          aria-hidden
        />
        <input
          type="range"
          aria-label="Seek"
          min={0}
          max={state.durationMs || 0}
          step={100}
          value={Math.round(state.currentMs)}
          onChange={(event) => clock.seek(Number(event.target.value))}
          className="seek relative h-6 w-full cursor-pointer appearance-none bg-transparent [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:shadow"
        />
      </div>

      <div className="hidden items-center md:flex" aria-label="Speakers">
        {speakers.slice(0, 5).map((speaker) => (
          <span
            key={speaker.id}
            className="flex items-center gap-1 px-1 text-[11px] text-muted"
            title={speaker.name}
          >
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: speakerColor(speaker.id) }}
            />
            {speaker.name.split(" ")[0]}
          </span>
        ))}
      </div>

      <Menu
        trigger={
          <button
            type="button"
            aria-label="Playback speed"
            className="tabular rounded-md px-2 py-1 text-[12.5px] font-semibold text-muted hover:bg-surface-muted"
          >
            {state.rate}×
          </button>
        }
      >
        {PLAYBACK_RATES.map((rate) => (
          <MenuItem key={rate} onSelect={() => clock.setRate(rate)}>
            <span className={rate === state.rate ? "font-semibold text-primary" : undefined}>
              {rate}×
            </span>
          </MenuItem>
        ))}
      </Menu>

      <span
        className="hidden text-subtle lg:inline"
        title="No recording is attached to this meeting, so playback is simulated. Transcript sync works exactly as it would with real audio."
      >
        <Info size={15} aria-label="Simulated playback" />
      </span>
    </div>
  );
}
