"use client";

import { Play } from "lucide-react";
import { memo } from "react";

import { Avatar } from "@/components/ui/Avatar";
import { cn, speakerColor } from "@/lib/colors";
import { formatTimestamp } from "@/lib/format";
import type { Fragment } from "@/lib/search";
import type { Segment } from "@/lib/types";

interface TranscriptLineProps {
  segment: Segment;
  active: boolean;
  fragments: Fragment[] | null; // null = no search highlights on this line
  showSpeaker: boolean; // consecutive lines by one speaker are grouped, like Fireflies
  onSelect: (segment: Segment) => void;
  register: (sequence: number, element: HTMLElement | null) => void;
}

/** Memoized: the player ticks ~60×/s, but a line only re-renders when its own props change. */
export const TranscriptLine = memo(function TranscriptLine({
  segment,
  active,
  fragments,
  showSpeaker,
  onSelect,
  register,
}: TranscriptLineProps) {
  const time = formatTimestamp(segment.start_ms);
  return (
    <li
      ref={(element) => register(segment.sequence, element)}
      data-testid="transcript-line"
      data-active={active || undefined}
      aria-current={active ? "true" : undefined}
      className={cn(
        "group relative flex gap-3 rounded-lg border-l-[3px] px-3 transition-colors",
        showSpeaker ? "mt-3 pt-2.5 pb-2" : "py-1.5",
        active ? "border-primary bg-primary-soft" : "border-transparent hover:bg-surface-muted",
      )}
    >
      <div className="w-9 shrink-0 pt-0.5">
        {showSpeaker ? (
          <Avatar id={segment.speaker.id} name={segment.speaker.name} />
        ) : (
          // Continuation lines keep their time in the gutter, so every line shows when it was said.
          <span
            aria-hidden
            onClick={() => onSelect(segment)}
            className="tabular block cursor-pointer pt-0.5 text-[11px] font-medium text-subtle group-hover:text-primary"
          >
            {time}
          </span>
        )}
      </div>
      <div className="min-w-0 flex-1">
        {showSpeaker && (
          <div className="mb-0.5 flex items-center gap-2">
            <span
              className="text-[13px] font-semibold"
              style={{ color: speakerColor(segment.speaker.id) }}
            >
              {segment.speaker.name}
            </span>
            <span
              aria-hidden
              onClick={() => onSelect(segment)}
              className="tabular inline-flex cursor-pointer items-center gap-1 text-[11.5px] font-medium text-subtle group-hover:text-primary"
            >
              <Play size={9} className="opacity-0 group-hover:opacity-100" fill="currentColor" />
              {time}
            </span>
          </div>
        )}
        <button
          type="button"
          onClick={() => onSelect(segment)}
          className="block w-full text-left text-[14px] leading-relaxed text-text"
          aria-label={`Play from ${time}: ${segment.text}`}
        >
          {fragments
            ? fragments.map((fragment, index) =>
                fragment.match ? (
                  <mark
                    key={index}
                    data-current-match={fragment.current || undefined}
                    className={cn(
                      "rounded px-0.5 text-text",
                      fragment.current ? "bg-mark-current" : "bg-mark",
                    )}
                  >
                    {fragment.text}
                  </mark>
                ) : (
                  <span key={index}>{fragment.text}</span>
                ),
              )
            : segment.text}
        </button>
      </div>
    </li>
  );
});
