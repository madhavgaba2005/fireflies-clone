"use client";

import { Plus, SearchX, Video } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useState } from "react";

import { useOpenCreateMeeting } from "@/components/layout/CreateMeetingContext";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import { useMeetings } from "@/hooks/queries";
import {
  EMPTY_FILTERS,
  filtersToParams,
  hasActiveFilters,
  parseFilters,
  toMeetingQuery,
  type LibraryFilters,
} from "@/lib/filters";
import { groupByDay } from "@/lib/format";
import type { MeetingListItem } from "@/lib/types";

import { DeleteMeetingDialog } from "./DeleteMeetingDialog";
import { EditMeetingModal } from "./EditMeetingModal";
import { MeetingFilters } from "./MeetingFilters";
import { MeetingRow } from "./MeetingRow";

function LoadingRows() {
  return (
    <div aria-label="Loading meetings" className="divide-y divide-border">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="flex items-center gap-4 px-5 py-4">
          <Skeleton className="h-10 w-10 rounded-xl" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3.5 w-1/3" />
            <Skeleton className="h-3 w-1/5" />
          </div>
          <Skeleton className="h-7 w-20 rounded-full" />
        </div>
      ))}
    </div>
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

  // Filters live in the URL: shareable links, and a refresh keeps them.
  const setFilters = useCallback(
    (next: LibraryFilters) => {
      const params = filtersToParams(next).toString();
      router.replace(params ? `${pathname}?${params}` : pathname, { scroll: false });
    },
    [router, pathname],
  );

  const groups = useMemo(() => groupByDay(data?.items ?? [], (m) => m.meeting_date), [data]);
  const filtered = hasActiveFilters(filters);

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-8">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-[22px] font-semibold tracking-tight">Meetings</h1>
          <p className="mt-0.5 text-[13px] text-muted" aria-live="polite">
            {data
              ? `${data.total} ${data.total === 1 ? "meeting" : "meetings"}${filtered ? " match your filters" : ""}`
              : " "}
          </p>
        </div>
      </div>

      <MeetingFilters filters={filters} onChange={setFilters} />

      <div className="mt-4 overflow-hidden rounded-2xl border border-border bg-surface">
        {isPending ? (
          <LoadingRows />
        ) : isError ? (
          <ErrorState error={error} title="Couldn't load meetings" onRetry={() => refetch()} />
        ) : data.items.length === 0 ? (
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
              <h2 className="sticky top-0 z-[1] border-b border-border bg-surface-muted/80 px-5 py-1.5 text-[11.5px] font-semibold uppercase tracking-wider text-muted backdrop-blur">
                {group.label}
              </h2>
              {group.items.map((meeting) => (
                <MeetingRow
                  key={meeting.id}
                  meeting={meeting}
                  onEdit={() => setEditing(meeting)}
                  onDelete={() => setDeleting(meeting)}
                  onKeyword={(keyword) => setFilters({ ...filters, keyword })}
                />
              ))}
            </section>
          ))
        )}
      </div>

      {editing && <EditMeetingModal meeting={editing} onClose={() => setEditing(null)} />}
      {deleting && <DeleteMeetingDialog meeting={deleting} onClose={() => setDeleting(null)} />}
    </div>
  );
}
