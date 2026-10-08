"use client";

import { ChevronDown, ChevronUp, LocateFixed, MessageSquareText, Search, X } from "lucide-react";
import {
  forwardRef,
  memo,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

import { EmptyState } from "@/components/ui/States";
import { findMatches, splitByMatches, stepMatch } from "@/lib/search";
import type { Segment } from "@/lib/types";

import { TranscriptLine } from "./TranscriptLine";

/** After the user scrolls by hand, playback stops pulling the view along for a few seconds. */
export const MANUAL_SCROLL_GRACE_MS = 4000;

export interface TranscriptPanelHandle {
  focusSearch(): void;
}

interface TranscriptPanelProps {
  segments: Segment[];
  initialQuery?: string; // e.g. from a global-search result (?find=)
  initialMatchFromMs?: number; // start at the first match at/after this moment (?t=)
  activeIndex: number;
  playing: boolean;
  onSeek: (ms: number) => void;
}

export const TranscriptPanel = memo(
  forwardRef<TranscriptPanelHandle, TranscriptPanelProps>(function TranscriptPanel(
    { segments, initialQuery = "", initialMatchFromMs = 0, activeIndex, playing, onSeek },
    ref,
  ) {
    const lines = useRef(new Map<number, HTMLElement>());
    const scroller = useRef<HTMLDivElement>(null);
    const searchInput = useRef<HTMLInputElement>(null);
    const lastManualScroll = useRef(0);
    const [query, setQuery] = useState(initialQuery);
    const [awayFromActive, setAwayFromActive] = useState(false);

    useImperativeHandle(ref, () => ({ focusSearch: () => searchInput.current?.focus() }), []);

    const register = useCallback((sequence: number, element: HTMLElement | null) => {
      if (element) lines.current.set(sequence, element);
      else lines.current.delete(sequence);
    }, []);

    const scrollToLine = useCallback(
      (index: number, smooth = true) => {
        const segment = segments[index];
        const element = segment && lines.current.get(segment.sequence);
        element?.scrollIntoView({ block: "center", behavior: smooth ? "smooth" : "auto" });
      },
      [segments],
    );

    // --- search ---------------------------------------------------------------------------------
    const texts = useMemo(() => segments.map((s) => s.text), [segments]);
    const matches = useMemo(() => findMatches(texts, query), [texts, query]);
    const [current, setCurrent] = useState(() => {
      if (!matches.length) return -1;
      const index = matches.findIndex(
        (m) => segments[m.segmentIndex].start_ms >= initialMatchFromMs,
      );
      return index === -1 ? 0 : index;
    });
    const rangesBySegment = useMemo(() => {
      const map = new Map<number, { start: number; end: number }[]>();
      for (const match of matches) {
        const list = map.get(match.segmentIndex) ?? [];
        list.push(match);
        map.set(match.segmentIndex, list);
      }
      return map;
    }, [matches]);

    // A new query starts at its first match (state adjusted during render, not in an effect).
    const [matchesFor, setMatchesFor] = useState(matches);
    if (matchesFor !== matches) {
      setMatchesFor(matches);
      setCurrent(matches.length ? 0 : -1);
    }

    const currentMatch = current >= 0 ? matches[current] : undefined;
    useEffect(() => {
      if (!currentMatch) return;
      lastManualScroll.current = Date.now(); // reading search results: don't yank the view back
      scrollToLine(currentMatch.segmentIndex);
    }, [currentMatch, scrollToLine]);

    const step = (direction: 1 | -1) =>
      setCurrent((index) => stepMatch(index, matches.length, direction));

    const onSearchKey = (event: KeyboardEvent<HTMLInputElement>) => {
      if (event.key === "Enter") {
        event.preventDefault();
        step(event.shiftKey ? -1 : 1);
      } else if (event.key === "Escape") {
        setQuery("");
      }
    };

    // --- follow playback ------------------------------------------------------------------------
    // Whenever the active line changes (playback, seek bar, chapter click) bring it into view —
    // unless the user scrolled by hand a moment ago; then offer a "Back to current" button.
    useEffect(() => {
      if (activeIndex < 0) return;
      if (Date.now() - lastManualScroll.current < MANUAL_SCROLL_GRACE_MS) {
        setAwayFromActive(true);
        return;
      }
      setAwayFromActive(false);
      scrollToLine(activeIndex);
    }, [activeIndex, scrollToLine]);

    const markManualScroll = () => {
      lastManualScroll.current = Date.now();
    };

    const select = useCallback((segment: Segment) => onSeek(segment.start_ms), [onSeek]);

    if (segments.length === 0) {
      return (
        <EmptyState
          icon={MessageSquareText}
          title="No transcript"
          description="This meeting was added without a transcript. Notes and action items can still be tracked."
        />
      );
    }

    return (
      <div className="flex h-full min-h-0 flex-col">
        <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
          <h2 className="text-[14px] font-semibold">Transcript</h2>
          <div className="relative ml-auto w-full max-w-72">
            <Search
              size={14}
              className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-subtle"
            />
            <input
              ref={searchInput}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={onSearchKey}
              placeholder="Find in transcript"
              aria-label="Find in transcript"
              className="h-8 w-full rounded-lg border border-border bg-surface-muted pl-8 pr-24 text-[13px] outline-none focus:border-primary focus:bg-surface focus:ring-2 focus:ring-primary-ring"
            />
            {query.trim() && (
              <div className="absolute right-1 top-1/2 flex -translate-y-1/2 items-center">
                <span
                  className="tabular px-1 text-[11.5px] text-muted"
                  data-testid="match-count"
                  aria-live="polite"
                >
                  {matches.length ? `${current + 1} / ${matches.length}` : "0 / 0"}
                </span>
                <button
                  type="button"
                  aria-label="Previous match"
                  onClick={() => step(-1)}
                  disabled={!matches.length}
                  className="rounded p-0.5 text-muted hover:text-text disabled:opacity-40"
                >
                  <ChevronUp size={14} />
                </button>
                <button
                  type="button"
                  aria-label="Next match"
                  onClick={() => step(1)}
                  disabled={!matches.length}
                  className="rounded p-0.5 text-muted hover:text-text disabled:opacity-40"
                >
                  <ChevronDown size={14} />
                </button>
                <button
                  type="button"
                  aria-label="Clear search"
                  onClick={() => setQuery("")}
                  className="rounded p-0.5 text-muted hover:text-text"
                >
                  <X size={14} />
                </button>
              </div>
            )}
          </div>
        </div>

        {query.trim() && matches.length === 0 && (
          <p
            className="border-b border-border bg-surface-muted px-4 py-2 text-[12.5px] text-muted"
            role="status"
          >
            No matches for “{query.trim()}”
          </p>
        )}

        <div className="relative min-h-0 flex-1">
          <div
            ref={scroller}
            className="h-full overflow-y-auto px-2 pb-6 sm:px-3"
            onWheel={markManualScroll}
            onTouchMove={markManualScroll}
            onKeyDown={markManualScroll}
          >
            <ol aria-label="Transcript lines">
              {segments.map((segment, index) => {
                const ranges = rangesBySegment.get(index);
                return (
                  <TranscriptLine
                    key={segment.id}
                    segment={segment}
                    active={index === activeIndex}
                    showSpeaker={
                      index === 0 || segments[index - 1].speaker.id !== segment.speaker.id
                    }
                    fragments={
                      ranges
                        ? splitByMatches(
                            segment.text,
                            ranges,
                            currentMatch?.segmentIndex === index ? currentMatch.start : null,
                          )
                        : null
                    }
                    onSelect={select}
                    register={register}
                  />
                );
              })}
            </ol>
          </div>
          {playing && awayFromActive && (
            <button
              type="button"
              onClick={() => {
                lastManualScroll.current = 0;
                setAwayFromActive(false);
                scrollToLine(activeIndex);
              }}
              className="absolute bottom-4 left-1/2 inline-flex -translate-x-1/2 items-center gap-1.5 rounded-full bg-text px-3 py-1.5 text-[12px] font-medium text-white shadow-lg"
            >
              <LocateFixed size={13} /> Back to current
            </button>
          )}
        </div>
      </div>
    );
  }),
);
