"use client";

import { Plus, SearchX, Trash2, Video, X } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useOpenCreateMeeting } from "@/components/layout/CreateMeetingContext";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import { useMeetings } from "@/hooks/queries";
import { cn } from "@/lib/colors";
import {
  EMPTY_FILTERS,
  filtersToParams,
  hasActiveFilters,
  parseFilters,
  toMeetingQuery,
  type LibraryFilters,
} from "@/lib/filters";
import { groupByWeek } from "@/lib/format";
import type { MeetingListItem } from "@/lib/types";

import { BulkDeleteDialog } from "./BulkDeleteDialog";
import { DeleteMeetingDialog } from "./DeleteMeetingDialog";
import { EditMeetingModal } from "./EditMeetingModal";
import { MeetingFilters } from "./MeetingFilters";
import { MeetingRow } from "./MeetingRow";
import { TABLE_GRID, TABLE_PAD } from "./tableGrid";

function LoadingRows() {
  return (
    <div aria-label="Loading meetings">
      {Array.from({ length: 6 }, (_, i) => (
        <div
          key={i}
          className={cn(
            TABLE_GRID,
            TABLE_PAD,
            "min-h-[72px] border-b border-border md:min-h-[84px]",
          )}
        >
          <div className="flex items-center gap-3">
            <span className="hidden w-4 sm:block" />
            <Skeleton className="h-9 w-9 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-3.5 w-1/3" />
              <Skeleton className="h-3 w-1/5" />
            </div>
          </div>
          <Skeleton className="hidden h-3 w-20 md:block" />
          <Skeleton className="hidden h-3 w-16 md:block" />
          <Skeleton className="hidden h-3 w-12 md:block" />
          <span />
        </div>
      ))}
    </div>
  );
}

/** Header checkbox: checked when every visible meeting is selected, mixed when some are. */
function SelectAll({
  total,
  selected,
  onChange,
}: {
  total: number;
  selected: number;
  onChange: (all: boolean) => void;
}) {
  const box = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (box.current) box.current.indeterminate = selected > 0 && selected < total;
  }, [selected, total]);
  return (
    <input
      ref={box}
      type="checkbox"
      aria-label="Select all meetings"
      checked={total > 0 && selected === total}
      disabled={total === 0}
      onChange={(event) => onChange(event.target.checked)}
      className="hidden h-4 w-4 shrink-0 cursor-pointer accent-[var(--primary)] sm:block"
    />
  );
}

export function MeetingsLibrary() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const openCreate = useOpenCreateMeeting();
  const filters = useMemo(
    () => parseFilters(new URLSearchParams(searchParams.toString())),
    [searchParams],
  );
  const query = useMemo(() => toMeetingQuery(filters), [filters]);
  const { data, isPending, isError, error, refetch } = useMeetings(query);
  const [editing, setEditing] = useState<MeetingListItem | null>(null);
  const [deleting, setDeleting] = useState<MeetingListItem | null>(null);
  const [checked, setChecked] = useState<Set<number>>(() => new Set());
  const [bulkDeleting, setBulkDeleting] = useState(false);

  // Filters live in the URL: shareable links, and a refresh keeps them.
  const setFilters = useCallback(
    (next: LibraryFilters) => {
      const params = filtersToParams(next).toString();
      router.replace(params ? `${pathname}?${params}` : pathname, { scroll: false });
    },
    [router, pathname],
  );

  const items = useMemo(() => data?.items ?? [], [data]);
  const groups = useMemo(() => groupByWeek(items, (m) => m.meeting_date), [items]);
  // Selection only ever covers meetings that are currently listed (filters can hide some).
  const selectedMeetings = items.filter((m) => checked.has(m.id));
  const filtered = hasActiveFilters(filters);

  const toggle = (id: number, on: boolean) =>
    setChecked((current) => {
      const next = new Set(current);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });

  return (
    <div className="flex min-h-full flex-col bg-surface">
      <div className={cn(TABLE_PAD, "flex items-center gap-x-3 border-b border-border py-3")}>
        <div className="min-w-0 flex-1">
          <MeetingFilters filters={filters} onChange={setFilters} />
        </div>
        <p className="type-meta shrink-0 max-sm:hidden" aria-live="polite">
          {data
            ? `${data.total} ${data.total === 1 ? "meeting" : "meetings"}${filtered ? " match your filters" : ""}`
            : " "}
        </p>
      </div>

      {selectedMeetings.length > 0 && (
        <div
          className={cn(
            TABLE_PAD,
            "flex items-center gap-3 border-b border-border bg-primary-soft/60 py-2 text-[13px]",
          )}
          role="region"
          aria-label="Selection"
        >
          <span className="font-medium text-text">{selectedMeetings.length} selected</span>
          <Button size="sm" variant="danger" onClick={() => setBulkDeleting(true)}>
            <Trash2 size={14} /> Delete
          </Button>
          <button
            type="button"
            onClick={() => setChecked(new Set())}
            className="inline-flex items-center gap-1 text-meta hover:text-text"
          >
            <X size={14} /> Clear selection
          </button>
        </div>
      )}

      <div
        className={cn(
          TABLE_GRID,
          TABLE_PAD,
          "sticky top-0 z-20 h-11 border-b border-border bg-surface max-md:hidden",
        )}
      >
        <div className="flex items-center gap-3">
          <SelectAll
            total={items.length}
            selected={selectedMeetings.length}
            onChange={(all) => setChecked(all ? new Set(items.map((m) => m.id)) : new Set())}
          />
          <span className="type-col-heading">Meeting</span>
        </div>
        <span className="type-col-heading">Date</span>
        <span className="type-col-heading">Time</span>
        <span className="type-col-heading">Duration</span>
        <span />
      </div>

      {isPending ? (
        <LoadingRows />
      ) : isError ? (
        <ErrorState error={error} title="Couldn't load meetings" onRetry={() => refetch()} />
      ) : items.length === 0 ? (
        filtered ? (
          <EmptyState
            icon={SearchX}
            title="No meetings match your filters"
            description="Try a different search, date range or participant."
            action={
              <Button
                size="sm"
                onClick={() => setFilters({ ...EMPTY_FILTERS, sort: filters.sort })}
              >
                Clear filters
              </Button>
            }
          />
        ) : (
          <EmptyState
            icon={Video}
            title="No meetings yet"
            description="Upload or paste a transcript and Lumen will write the notes for you."
            action={
              <Button variant="primary" size="sm" onClick={() => openCreate("upload")}>
                <Plus size={15} /> New meeting
              </Button>
            }
          />
        )
      ) : (
        groups.map((group) => (
          <section key={group.label} aria-label={group.label}>
            <h2
              className={cn(TABLE_PAD, "flex items-end gap-3 border-b border-border pb-2.5 pt-3.5")}
            >
              {/* Same spacer as the row checkbox: the heading lines up with the avatars. */}
              <span aria-hidden className="hidden w-4 shrink-0 sm:block" />
              <span>
                <span className="type-group-heading">{group.label}</span>
                <span className="type-group-count">
                  {" "}
                  · {group.items.length} {group.items.length === 1 ? "meeting" : "meetings"}
                </span>
              </span>
            </h2>
            {group.items.map((meeting) => (
              <MeetingRow
                key={meeting.id}
                meeting={meeting}
                selected={checked.has(meeting.id)}
                selectionActive={selectedMeetings.length > 0}
                onSelect={(on) => toggle(meeting.id, on)}
                onEdit={() => setEditing(meeting)}
                onDelete={() => setDeleting(meeting)}
                onKeyword={(keyword) => setFilters({ ...filters, keyword })}
              />
            ))}
          </section>
        ))
      )}

      {editing && <EditMeetingModal meeting={editing} onClose={() => setEditing(null)} />}
      {deleting && <DeleteMeetingDialog meeting={deleting} onClose={() => setDeleting(null)} />}
      {bulkDeleting && (
        <BulkDeleteDialog
          meetings={selectedMeetings}
          onClose={() => setBulkDeleting(false)}
          onDone={(deletedIds) => {
            setBulkDeleting(false);
            setChecked((current) => new Set([...current].filter((id) => !deletedIds.includes(id))));
          }}
        />
      )}
    </div>
  );
}
