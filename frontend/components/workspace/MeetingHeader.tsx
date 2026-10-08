"use client";

import {
  ArrowLeft,
  Download,
  CalendarDays,
  Clock,
  Link2,
  MoreHorizontal,
  Pencil,
  RefreshCw,
  Share2,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

import { AvatarStack } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { useComingSoon } from "@/components/ui/ComingSoon";
import { Menu, MenuItem, MenuSeparator } from "@/components/ui/Menu";
import { errorMessage } from "@/components/ui/States";
import { useRegenerateSummary } from "@/hooks/queries";
import { formatDate, formatDuration, formatTime } from "@/lib/format";
import type { MeetingDetail } from "@/lib/types";

export function MeetingHeader({
  meeting,
  onEdit,
  onDelete,
  onDownload,
}: {
  meeting: MeetingDetail;
  onEdit: () => void;
  onDelete: () => void;
  onDownload: () => void;
}) {
  const comingSoon = useComingSoon();
  const regenerate = useRegenerateSummary(meeting.id);
  const canRegenerate =
    meeting.transcript_revision > 0 &&
    meeting.processing_status !== "pending" &&
    meeting.processing_status !== "processing";

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast.success("Link copied");
    } catch {
      toast.error("Couldn't copy the link");
    }
  };

  return (
    <div className="flex shrink-0 flex-wrap items-start gap-3 border-b border-border bg-surface px-4 py-3 sm:px-6">
      <Link
        href="/meetings"
        aria-label="Back to meetings"
        className="mt-1 rounded-md p-1 text-muted hover:bg-surface-muted hover:text-text"
      >
        <ArrowLeft size={18} />
      </Link>
      <div className="min-w-0 flex-1">
        <h1 className="truncate text-[19px] font-semibold tracking-tight">{meeting.title}</h1>
        <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-[12.5px] text-muted">
          <span className="inline-flex items-center gap-1.5">
            <CalendarDays size={13} /> {formatDate(meeting.meeting_date)} ·{" "}
            {formatTime(meeting.meeting_date)}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Clock size={13} /> {formatDuration(meeting.duration_seconds)}
          </span>
          {meeting.participants.length > 0 && (
            <span className="inline-flex items-center gap-2">
              <AvatarStack people={meeting.participants} max={5} />
              <span>{meeting.participants.length} participants</span>
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-1.5">
        <Button
          size="sm"
          onClick={() =>
            comingSoon({
              name: "Share meeting",
              description: "Share notes, transcripts and soundbites with your team or by link.",
            })
          }
        >
          <Share2 size={14} /> Share
        </Button>
        <Button size="icon" variant="ghost" onClick={copyLink} aria-label="Copy link">
          <Link2 size={16} />
        </Button>
        <Menu
          trigger={
            <button
              type="button"
              aria-label="Meeting actions"
              className="rounded-lg p-2 text-muted hover:bg-surface-muted hover:text-text"
            >
              <MoreHorizontal size={18} />
            </button>
          }
        >
          <MenuItem icon={<Pencil size={15} />} onSelect={onEdit}>
            Edit details
          </MenuItem>
          {canRegenerate && (
            <MenuItem
              icon={<RefreshCw size={15} />}
              onSelect={() =>
                regenerate
                  .mutateAsync()
                  .then(() => toast.info("Regenerating notes…"))
                  .catch((error) =>
                    toast.error("Couldn't regenerate notes", { description: errorMessage(error) }),
                  )
              }
            >
              Regenerate notes
            </MenuItem>
          )}
          <MenuItem icon={<Download size={15} />} onSelect={onDownload}>
            Download
          </MenuItem>
          <MenuSeparator />
          <MenuItem icon={<Trash2 size={15} />} onSelect={onDelete} danger>
            Delete meeting
          </MenuItem>
        </Menu>
      </div>
    </div>
  );
}
