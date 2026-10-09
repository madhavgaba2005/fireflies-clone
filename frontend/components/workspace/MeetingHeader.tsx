"use client";

import {
  ArrowLeft,
  CalendarDays,
  ChevronRight,
  Clock,
  Download,
  Link2,
  Menu as MenuIcon,
  MoreHorizontal,
  Pencil,
  RefreshCw,
  Share2,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { toast } from "sonner";

import { useOpenNavDrawer } from "@/components/layout/ShellContext";
import { NotificationsButton, UserMenu } from "@/components/layout/UserControls";
import { AvatarStack } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { useComingSoon } from "@/components/ui/ComingSoon";
import { Menu, MenuItem, MenuSeparator } from "@/components/ui/Menu";
import { errorMessage } from "@/components/ui/States";
import { useRegenerateSummary } from "@/hooks/queries";
import { formatDate, formatDuration, formatTime } from "@/lib/format";
import type { MeetingDetail } from "@/lib/types";

/**
 * Compact single-line toolbar for meeting pages (Fireflies' meeting view): breadcrumb on the left,
 * meeting actions + notifications + account on the right. Rendered in every state (loading,
 * not found) so navigation is always available.
 */
export function MeetingToolbar({ title, actions }: { title?: string; actions?: ReactNode }) {
  const openDrawer = useOpenNavDrawer();
  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b border-border bg-surface px-3 sm:px-4">
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={openDrawer}
        aria-label="Open navigation"
      >
        <MenuIcon size={18} />
      </Button>
      <Link
        href="/meetings"
        aria-label="Back to meetings"
        className="rounded-md p-1.5 text-meta hover:bg-surface-muted hover:text-text"
      >
        <ArrowLeft size={17} />
      </Link>
      <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-1 text-[13.5px]">
        <Link href="/meetings" className="shrink-0 text-meta hover:text-text max-sm:hidden">
          All meetings
        </Link>
        {title && (
          <>
            <ChevronRight size={14} className="shrink-0 text-subtle max-sm:hidden" />
            <span aria-current="page" className="truncate font-medium text-text">
              {title}
            </span>
          </>
        )}
      </nav>
      <div className="ml-auto flex shrink-0 items-center gap-1">
        {actions}
        <div className="hidden items-center gap-1 sm:flex">
          <NotificationsButton />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}

/** Share (primary), copy link and the ⋯ menu for one meeting. */
export function MeetingActions({
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
    <>
      <Button
        variant="primary"
        size="sm"
        aria-label="Share"
        onClick={() =>
          comingSoon({
            name: "Share meeting",
            description: "Share notes, transcripts and soundbites with your team or by link.",
          })
        }
      >
        <Share2 size={14} /> <span className="hidden sm:inline">Share</span>
      </Button>
      <Button size="icon" variant="ghost" onClick={copyLink} aria-label="Copy link">
        <Link2 size={16} />
      </Button>
      <Menu
        trigger={
          <button
            type="button"
            aria-label="Meeting actions"
            className="rounded-lg p-2 text-meta hover:bg-surface-muted hover:text-text"
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
    </>
  );
}

/** Title and metadata at the top of the notes column (compact, like Fireflies). */
export function MeetingTitle({ meeting }: { meeting: MeetingDetail }) {
  return (
    <div className="pb-5">
      <h1 className="text-[21px] font-semibold leading-tight tracking-tight">{meeting.title}</h1>
      <div className="type-meta mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5">
        {meeting.participants.length > 0 && (
          <span className="inline-flex items-center gap-2">
            <AvatarStack people={meeting.participants} max={5} />
            <span className="whitespace-nowrap">{meeting.participants.length} participants</span>
          </span>
        )}
        <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
          <CalendarDays size={13} /> {formatDate(meeting.meeting_date)} ·{" "}
          {formatTime(meeting.meeting_date)}
        </span>
        <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
          <Clock size={13} /> {formatDuration(meeting.duration_seconds)}
        </span>
      </div>
    </div>
  );
}
