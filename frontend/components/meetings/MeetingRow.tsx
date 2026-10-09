"use client";

import {
  CalendarDays,
  CheckSquare,
  Clock,
  Info,
  MoreHorizontal,
  Pencil,
  SquareArrowOutUpRight,
  Trash2,
  Video,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Popover } from "radix-ui";

import { Avatar } from "@/components/ui/Avatar";
import { Menu, MenuItem, MenuSeparator } from "@/components/ui/Menu";
import { StatusChip } from "@/components/ui/StatusChip";
import { cn } from "@/lib/colors";
import { formatDuration, formatShortDate, formatTime } from "@/lib/format";
import type { MeetingListItem } from "@/lib/types";

import { TABLE_GRID, TABLE_PAD } from "./tableGrid";

function participantSummary(meeting: MeetingListItem): string {
  const names = meeting.participants.map((p) => p.name);
  if (names.length === 0) return "No participants";
  const shown = names.slice(0, 2).join(", ");
  return names.length > 2 ? `${shown} +${names.length - 2}` : shown;
}

/** One avatar (the first participant), compact like Fireflies' owner avatar. */
function ParticipantIndicator({ meeting }: { meeting: MeetingListItem }) {
  const [first] = meeting.participants; // the "+N" for the others is in the names line
  return (
    <span
      role="img"
      aria-label={
        meeting.participants.length
          ? `Participants: ${meeting.participants.map((p) => p.name).join(", ")}`
          : "No participants"
      }
      className="relative shrink-0"
    >
      {first ? (
        <Avatar id={first.id} name={first.name} size="lg" />
      ) : (
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-soft text-primary">
          <Video size={16} />
        </span>
      )}
    </span>
  );
}

function DetailsPopover({
  meeting,
  onKeyword,
}: {
  meeting: MeetingListItem;
  onKeyword: (keyword: string) => void;
}) {
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label={`Details for ${meeting.title}`}
          className="rounded-md p-1.5 text-meta hover:bg-surface-muted hover:text-text"
        >
          <Info size={16} />
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="end"
          sideOffset={6}
          className="z-50 w-72 rounded-xl border border-border bg-surface p-3.5 text-[13px] shadow-lg focus:outline-none"
        >
          <p className="font-semibold leading-snug">{meeting.title}</p>
          <p className="type-meta mt-0.5">
            {formatShortDate(meeting.meeting_date)} · {formatTime(meeting.meeting_date)} ·{" "}
            {formatDuration(meeting.duration_seconds)}
          </p>
          <p className="type-col-heading mt-3">Participants</p>
          <ul className="mt-1.5 space-y-1.5">
            {meeting.participants.map((person) => (
              <li key={person.id} className="flex items-center gap-2">
                <Avatar id={person.id} name={person.name} size="xs" /> {person.name}
              </li>
            ))}
            {meeting.participants.length === 0 && <li className="type-meta">None</li>}
          </ul>
          {meeting.keywords.length > 0 && (
            <>
              <p className="type-col-heading mt-3">Tags</p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {meeting.keywords.map((keyword) => (
                  <Popover.Close asChild key={keyword}>
                    <button
                      type="button"
                      onClick={() => onKeyword(keyword)}
                      className="rounded-full border border-border px-2 py-0.5 text-[11.5px] text-muted hover:border-primary/40 hover:text-primary"
                    >
                      {keyword}
                    </button>
                  </Popover.Close>
                ))}
              </div>
            </>
          )}
          <p className="type-col-heading mt-3">Action items</p>
          <p className="mt-1">
            {meeting.action_item_count
              ? `${meeting.open_action_item_count} open of ${meeting.action_item_count}`
              : "None yet"}
          </p>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

export function MeetingRow({
  meeting,
  selected,
  selectionActive,
  onSelect,
  onEdit,
  onDelete,
  onKeyword,
}: {
  meeting: MeetingListItem;
  selected: boolean;
  selectionActive: boolean; // once anything is selected, every checkbox stays visible
  onSelect: (selected: boolean) => void;
  onEdit: () => void;
  onDelete: () => void;
  onKeyword: (keyword: string) => void;
}) {
  const router = useRouter();
  const date = formatShortDate(meeting.meeting_date);
  const time = formatTime(meeting.meeting_date);
  const duration = formatDuration(meeting.duration_seconds);
  return (
    <div
      data-testid="meeting-row"
      aria-selected={selected || undefined}
      className={cn(
        TABLE_GRID,
        TABLE_PAD,
        // Phones size to content; tablet and up use a fixed comfortable height (Fireflies-like density).
        "group relative min-h-[72px] border-b border-border py-3 transition-colors md:min-h-[84px]",
        "hover:bg-row-hover has-[a:focus-visible]:bg-row-hover",
        "has-[a:focus-visible]:outline-2 has-[a:focus-visible]:-outline-offset-2 has-[a:focus-visible]:outline-primary",
        selected && "bg-primary-soft/50",
      )}
    >
      <div className="flex min-w-0 items-center gap-3">
        <input
          type="checkbox"
          checked={selected}
          onChange={(event) => onSelect(event.target.checked)}
          aria-label={`Select ${meeting.title}`}
          className={cn(
            "relative z-10 hidden h-4 w-4 shrink-0 cursor-pointer accent-[var(--primary)] transition-opacity sm:block",
            selected || selectionActive
              ? "opacity-100"
              : "opacity-0 group-hover:opacity-100 focus-visible:opacity-100",
          )}
        />
        <ParticipantIndicator meeting={meeting} />
        <div className="min-w-0 flex-1">
          <Link
            href={`/meetings/${meeting.id}`}
            className="type-row-title block truncate outline-none after:absolute after:inset-0 hover:text-primary"
          >
            {meeting.title}
          </Link>
          <div className="type-meta mt-1 flex min-w-0 items-center gap-2">
            <span className="truncate">{participantSummary(meeting)}</span>
            {/* Tablet: the count yields its space to names (it is also in the details popover). */}
            {meeting.action_item_count > 0 && (
              <span
                className="hidden shrink-0 items-center gap-1 sm:inline-flex md:hidden xl:inline-flex"
                title={`${meeting.open_action_item_count} open of ${meeting.action_item_count} action items`}
              >
                <span aria-hidden className="text-border">
                  |
                </span>
                <CheckSquare size={12} /> {meeting.open_action_item_count} open of{" "}
                {meeting.action_item_count}
              </span>
            )}
            <StatusChip status={meeting.processing_status} hideCompleted />
            <span className="relative z-10 hidden shrink-0 items-center gap-1.5 xl:inline-flex">
              {meeting.keywords.slice(0, 2).map((keyword) => (
                <button
                  key={keyword}
                  type="button"
                  onClick={() => onKeyword(keyword)}
                  className="rounded-full border border-border bg-surface px-2 py-px text-[11px] text-muted hover:border-primary/40 hover:text-primary"
                >
                  {keyword}
                </button>
              ))}
            </span>
          </div>
          {/* Phones: the date, time and duration columns collapse into one line. */}
          <p className="type-meta tabular mt-0.5 md:hidden">
            {date} · {time} · {duration}
          </p>
        </div>
      </div>

      <div className="type-meta hidden items-center gap-2 md:flex">
        <CalendarDays size={15} className="shrink-0" />
        <span className="truncate">{date}</span>
      </div>
      <div className="type-meta tabular hidden items-center gap-2 md:flex">
        <Clock size={15} className="shrink-0" />
        <span className="truncate">{time}</span>
      </div>
      <div className="type-meta tabular hidden md:block">{duration}</div>

      <div className="relative z-10 flex items-center justify-end gap-0.5">
        <Menu
          trigger={
            <button
              type="button"
              aria-label={`Actions for ${meeting.title}`}
              className="rounded-md p-1.5 text-primary hover:bg-surface-muted"
            >
              <MoreHorizontal size={18} />
            </button>
          }
        >
          <MenuItem
            icon={<SquareArrowOutUpRight size={15} />}
            onSelect={() => router.push(`/meetings/${meeting.id}`)}
          >
            Open
          </MenuItem>
          <MenuItem icon={<Pencil size={15} />} onSelect={onEdit}>
            Edit details
          </MenuItem>
          <MenuSeparator />
          <MenuItem icon={<Trash2 size={15} />} onSelect={onDelete} danger>
            Delete
          </MenuItem>
        </Menu>
        <span className="hidden md:inline-flex">
          <DetailsPopover meeting={meeting} onKeyword={onKeyword} />
        </span>
      </div>
    </div>
  );
}
