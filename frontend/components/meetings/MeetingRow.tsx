"use client";

import { CheckSquare, Clock, FileUp, MoreHorizontal, Pencil, Trash2, Video } from "lucide-react";
import Link from "next/link";

import { AvatarStack } from "@/components/ui/Avatar";
import { Menu, MenuItem, MenuSeparator } from "@/components/ui/Menu";
import { StatusChip } from "@/components/ui/StatusChip";
import { formatDuration, formatTime } from "@/lib/format";
import type { MeetingListItem } from "@/lib/types";

export function MeetingRow({
  meeting,
  onEdit,
  onDelete,
  onKeyword,
}: {
  meeting: MeetingListItem;
  onEdit: () => void;
  onDelete: () => void;
  onKeyword: (keyword: string) => void;
}) {
  const uploaded = meeting.source === "upload" || meeting.source === "paste";
  return (
    <div
      data-testid="meeting-row"
      className="group relative flex items-center gap-4 border-b border-border px-5 py-3.5 transition-colors last:border-b-0 hover:bg-surface-muted/60"
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-soft text-primary">
        {uploaded ? <FileUp size={18} /> : <Video size={18} />}
      </div>

      <div className="min-w-0 flex-1">
        <Link
          href={`/meetings/${meeting.id}`}
          className="block truncate text-[14px] font-semibold text-text after:absolute after:inset-0 hover:text-primary"
        >
          {meeting.title}
        </Link>
        <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12.5px] text-muted">
          <span className="tabular">{formatTime(meeting.meeting_date)}</span>
          <span className="inline-flex items-center gap-1">
            <Clock size={12} /> {formatDuration(meeting.duration_seconds)}
          </span>
          {meeting.action_item_count > 0 && (
            <span className="inline-flex items-center gap-1">
              <CheckSquare size={12} /> {meeting.open_action_item_count} open of{" "}
              {meeting.action_item_count}
            </span>
          )}
          <StatusChip status={meeting.processing_status} hideCompleted />
        </div>
      </div>

      <div className="relative z-10 hidden items-center gap-1.5 xl:flex">
        {meeting.keywords.slice(0, 2).map((keyword) => (
          <button
            key={keyword}
            type="button"
            onClick={() => onKeyword(keyword)}
            className="rounded-full border border-border bg-surface px-2 py-0.5 text-[11px] text-muted hover:border-primary/40 hover:text-primary"
          >
            {keyword}
          </button>
        ))}
      </div>

      <div className="relative z-10 hidden sm:block">
        <AvatarStack people={meeting.participants} />
      </div>

      <div className="relative z-10">
        <Menu
          trigger={
            <button
              type="button"
              aria-label={`Actions for ${meeting.title}`}
              className="rounded-md p-1.5 text-subtle hover:bg-surface hover:text-text"
            >
              <MoreHorizontal size={18} />
            </button>
          }
        >
          <MenuItem icon={<Pencil size={15} />} onSelect={onEdit}>
            Edit details
          </MenuItem>
          <MenuSeparator />
          <MenuItem icon={<Trash2 size={15} />} onSelect={onDelete} danger>
            Delete
          </MenuItem>
        </Menu>
      </div>
    </div>
  );
}
