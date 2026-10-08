"use client";

import { FileText, Loader2, Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useGlobalSearch } from "@/hooks/queries";
import { formatDate, formatTimestamp } from "@/lib/format";
import { findMatches, splitByMatches } from "@/lib/search";

const DEBOUNCE_MS = 250;

function Highlighted({ text, query }: { text: string; query: string }) {
  const ranges = findMatches([text], query);
  return (
    <>
      {splitByMatches(text, ranges).map((fragment, index) =>
        fragment.match ? (
          <mark key={index} className="rounded bg-mark px-0.5 text-text">
            {fragment.text}
          </mark>
        ) : (
          <span key={index}>{fragment.text}</span>
        ),
      )}
    </>
  );
}

/**
 * Bonus: search every meeting's title and transcript from the top bar. Results link straight to
 * the moment in the recording (`?t=`) with the transcript search pre-filled (`?find=`).
 * Enter still opens the library filtered by title.
 */
export function GlobalSearch() {
  const router = useRouter();
  const container = useRef<HTMLDivElement>(null);
  const [text, setText] = useState("");
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const { data, isFetching, isError } = useGlobalSearch(query);

  useEffect(() => {
    const timer = setTimeout(() => setQuery(text.trim()), DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [text]);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    setOpen(false);
    const q = text.trim();
    router.push(q ? `/meetings?q=${encodeURIComponent(q)}` : "/meetings");
  };

  const finish = () => {
    setOpen(false);
    setText("");
  };

  const showPanel = open && query.length >= 2;
  const find = encodeURIComponent(query);

  return (
    <div ref={container} className="relative max-w-md flex-1">
      <form onSubmit={submit} role="search">
        <Search
          size={15}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-subtle"
        />
        <input
          value={text}
          onChange={(event) => {
            setText(event.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={(event) => event.key === "Escape" && setOpen(false)}
          placeholder="Search meetings and transcripts"
          role="combobox"
          aria-label="Search meetings"
          aria-autocomplete="list"
          aria-expanded={showPanel}
          aria-controls="global-search-results"
          className="h-9 w-full rounded-lg border border-border bg-surface-muted pl-9 pr-8 text-[13px] outline-none transition focus:border-primary focus:bg-surface focus:ring-2 focus:ring-primary-ring"
        />
        {isFetching && (
          <Loader2
            size={14}
            className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-subtle"
          />
        )}
      </form>

      {showPanel && (
        <div
          id="global-search-results"
          role="region"
          aria-label="Search results"
          className="absolute left-0 right-0 top-11 z-40 max-h-[70vh] overflow-y-auto rounded-xl border border-border bg-surface p-1.5 shadow-xl sm:right-auto sm:w-[560px]"
        >
          {isError ? (
            <p className="px-3 py-4 text-[13px] text-danger">Search is unavailable right now.</p>
          ) : !data ? (
            <p className="px-3 py-4 text-[13px] text-muted">Searching…</p>
          ) : data.results.length === 0 ? (
            <p className="px-3 py-4 text-[13px] text-muted">
              Nothing matches “{data.query}” in any title or transcript.
            </p>
          ) : (
            <>
              <p className="px-3 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wider text-subtle">
                {data.total_hits} transcript {data.total_hits === 1 ? "match" : "matches"} in{" "}
                {data.results.length} {data.results.length === 1 ? "meeting" : "meetings"}
                {data.truncated && " (showing the first 50)"}
              </p>
              {data.results.map((result) => (
                <div key={result.meeting_id} className="rounded-lg px-1.5 py-1">
                  <Link
                    href={`/meetings/${result.meeting_id}?find=${find}`}
                    onClick={finish}
                    className="flex items-center gap-2 rounded-md px-1.5 py-1.5 hover:bg-surface-muted"
                  >
                    <FileText size={14} className="shrink-0 text-primary" />
                    <span className="truncate text-[13px] font-semibold">
                      <Highlighted text={result.title} query={data.query} />
                    </span>
                    <span className="ml-auto shrink-0 text-[11px] text-subtle">
                      {formatDate(result.meeting_date)}
                    </span>
                  </Link>
                  {result.hits.slice(0, 3).map((hit) => (
                    <Link
                      key={hit.segment_id}
                      href={`/meetings/${result.meeting_id}?t=${hit.start_ms}&find=${find}`}
                      onClick={finish}
                      className="ml-6 flex gap-2 rounded-md px-1.5 py-1 text-[12.5px] text-muted hover:bg-surface-muted"
                      data-testid="search-hit"
                    >
                      <span className="tabular shrink-0 font-medium text-primary">
                        {formatTimestamp(hit.start_ms)}
                      </span>
                      <span className="min-w-0">
                        <span className="font-medium text-text">{hit.speaker}:</span>{" "}
                        <Highlighted text={hit.snippet} query={data.query} />
                      </span>
                    </Link>
                  ))}
                  {result.hits.length > 3 && (
                    <p className="ml-8 px-1.5 text-[11.5px] text-subtle">
                      +{result.hits.length - 3} more in this meeting
                    </p>
                  )}
                </div>
              ))}
            </>
          )}
          <p className="border-t border-border px-3 pb-1 pt-2 text-[11.5px] text-subtle">
            Press Enter to filter the library by title
          </p>
        </div>
      )}
    </div>
  );
}
