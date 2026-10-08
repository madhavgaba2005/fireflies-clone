"use client";

import { useQueryClient } from "@tanstack/react-query";
import { FileQuestion } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { PlayerBar } from "@/components/audio/PlayerBar";
import { DeleteMeetingDialog } from "@/components/meetings/DeleteMeetingDialog";
import { EditMeetingModal } from "@/components/meetings/EditMeetingModal";
import { NotesPanel } from "@/components/summary/NotesPanel";
import {
  TranscriptPanel,
  type TranscriptPanelHandle,
} from "@/components/transcript/TranscriptPanel";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/States";
import {
  isProcessing,
  keys,
  useActionItems,
  useMeeting,
  useSummary,
  useTranscript,
} from "@/hooks/queries";
import { usePlaybackClock } from "@/hooks/usePlaybackClock";
import { ApiError } from "@/lib/api";
import { cn } from "@/lib/colors";
import { findActiveSegmentIndex, playbackDurationMs } from "@/lib/transcript";
import type { ProcessingStatus, Segment } from "@/lib/types";

import { ExportDialog } from "./ExportDialog";
import { MeetingHeader } from "./MeetingHeader";

const NO_SEGMENTS: Segment[] = [];
const ARROW_SEEK_MS = 5000;

function WorkspaceSkeleton() {
  return (
    <div className="flex h-full flex-col" aria-label="Loading meeting">
      <div className="border-b border-border bg-surface px-6 py-4">
        <Skeleton className="h-5 w-72" />
        <Skeleton className="mt-2 h-3 w-96" />
      </div>
      <div className="grid flex-1 gap-0 lg:grid-cols-[minmax(340px,42%)_1fr]">
        <div className="space-y-3 border-r border-border bg-surface p-5">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-3 w-full" />
          ))}
        </div>
        <div className="space-y-4 p-5">
          {Array.from({ length: 8 }, (_, i) => (
            <Skeleton key={i} className="h-4 w-11/12" />
          ))}
        </div>
      </div>
    </div>
  );
}

export function MeetingWorkspace({ id }: { id: number }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const meetingQuery = useMeeting(id);
  const transcriptQuery = useTranscript(id);
  const meeting = meetingQuery.data;
  const summaryQuery = useSummary(id, meeting?.processing_status === "completed");
  const transcript = useRef<TranscriptPanelHandle>(null);
  const [mobileTab, setMobileTab] = useState<"notes" | "transcript">("transcript");
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const actionItemsQuery = useActionItems(id); // shared cache with the notes panel

  const segments = transcriptQuery.data?.segments ?? NO_SEGMENTS;
  const durationMs = playbackDurationMs(meeting?.duration_seconds ?? 0, segments);
  const { clock, state } = usePlaybackClock(durationMs);

  // Player → transcript: which line is active right now (binary search, see lib/transcript.ts).
  const activeIndex = useMemo(
    () => findActiveSegmentIndex(segments, state.currentMs),
    [segments, state.currentMs],
  );
  const topics = summaryQuery.data?.topics;
  const topicTimes = useMemo(
    () => (topics ?? []).map((t) => ({ start_ms: t.start_ms ?? 0, end_ms: t.start_ms ?? 0 })),
    [topics],
  );
  const activeTopic = useMemo(
    () => findActiveSegmentIndex(topicTimes, state.currentMs),
    [topicTimes, state.currentMs],
  );

  // Transcript → player: clicking a line (or a chapter / action item) seeks and plays.
  const seekAndPlay = useCallback(
    (ms: number) => {
      clock.seek(ms);
      clock.play();
    },
    [clock],
  );

  // Deep link: /meetings/3?t=125000 starts at 2:05 (used by global search results).
  const startAt = Number(searchParams.get("t"));
  const appliedDeepLink = useRef(false);
  useEffect(() => {
    if (appliedDeepLink.current || !durationMs || !startAt) return;
    appliedDeepLink.current = true;
    clock.seek(startAt);
  }, [clock, durationMs, startAt]);

  // Eventual consistency made visible: tell the user when the AI notes arrive.
  const previousStatus = useRef<ProcessingStatus | undefined>(undefined);
  const status = meeting?.processing_status;
  useEffect(() => {
    const before = previousStatus.current;
    previousStatus.current = status;
    if (!before || !isProcessing({ processing_status: before }) || !status) return;
    if (status === "completed") {
      toast.success("Your meeting notes are ready");
      queryClient.invalidateQueries({ queryKey: keys.summary(id) });
      queryClient.invalidateQueries({ queryKey: keys.actionItems(id) });
      queryClient.invalidateQueries({ queryKey: keys.meetings() });
    } else if (status === "failed") {
      toast.error("Notes couldn't be generated", {
        description: "You can retry from the notes panel.",
      });
    }
  }, [status, id, queryClient]);

  useEffect(() => {
    if (meeting) document.title = `${meeting.title} · Lumen`;
  }, [meeting]);

  // Keyboard: Space play/pause, ←/→ seek 5 s, "/" find in transcript (ignored while typing).
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (target.closest("input, textarea, select, [contenteditable], [role=dialog], [role=menu]"))
        return;
      if (event.key === " " && !target.closest("button")) {
        event.preventDefault();
        clock.toggle();
      } else if (event.key === "ArrowRight") {
        clock.seek(clock.getSnapshot().currentMs + ARROW_SEEK_MS);
      } else if (event.key === "ArrowLeft") {
        clock.seek(clock.getSnapshot().currentMs - ARROW_SEEK_MS);
      } else if (event.key === "/") {
        event.preventDefault();
        setMobileTab("transcript");
        transcript.current?.focusSearch();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [clock]);

  if (meetingQuery.isPending) return <WorkspaceSkeleton />;

  if (meetingQuery.isError) {
    const notFound = meetingQuery.error instanceof ApiError && meetingQuery.error.status === 404;
    return notFound ? (
      <EmptyState
        icon={FileQuestion}
        title="Meeting not found"
        description="It may have been deleted, or the link is wrong."
        action={
          <Link href="/meetings" className="text-[13px] font-semibold text-primary hover:underline">
            Back to meetings
          </Link>
        }
        className="h-full"
      />
    ) : (
      <ErrorState
        error={meetingQuery.error}
        title="Couldn't load this meeting"
        onRetry={() => meetingQuery.refetch()}
        className="h-full justify-center"
      />
    );
  }

  const loaded = meetingQuery.data; // narrowed: not pending, not error

  const transcriptArea = transcriptQuery.isError ? (
    <ErrorState
      error={transcriptQuery.error}
      title="Couldn't load the transcript"
      onRetry={() => transcriptQuery.refetch()}
    />
  ) : transcriptQuery.isPending ? (
    <div className="space-y-4 p-5">
      {Array.from({ length: 8 }, (_, i) => (
        <Skeleton key={i} className="h-4 w-11/12" />
      ))}
    </div>
  ) : (
    <TranscriptPanel
      ref={transcript}
      segments={segments}
      initialQuery={searchParams.get("find") ?? ""}
      initialMatchFromMs={startAt || 0}
      activeIndex={activeIndex}
      playing={state.playing}
      onSeek={seekAndPlay}
    />
  );

  return (
    <div className="flex h-full flex-col">
      <MeetingHeader
        meeting={loaded}
        onDownload={() => setDownloading(true)}
        onEdit={() => setEditing(true)}
        onDelete={() => setDeleting(true)}
      />

      <div
        role="tablist"
        aria-label="Workspace panels"
        className="flex border-b border-border bg-surface lg:hidden"
      >
        {(["notes", "transcript"] as const).map((tab) => (
          <button
            key={tab}
            role="tab"
            type="button"
            aria-selected={mobileTab === tab}
            onClick={() => setMobileTab(tab)}
            className={cn(
              "flex-1 border-b-2 py-2.5 text-[13px] font-medium capitalize",
              mobileTab === tab ? "border-primary text-primary" : "border-transparent text-muted",
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="grid min-h-0 flex-1 lg:grid-cols-[minmax(340px,42%)_1fr]">
        <div
          className={cn(
            "min-h-0 border-r border-border bg-surface",
            mobileTab === "notes" ? "block" : "hidden lg:block",
          )}
        >
          <NotesPanel
            meeting={loaded}
            summary={summaryQuery.data}
            summaryLoading={summaryQuery.isPending && summaryQuery.fetchStatus !== "idle"}
            activeTopic={activeTopic}
            onSeek={seekAndPlay}
          />
        </div>
        <div
          className={cn("min-h-0 bg-bg", mobileTab === "transcript" ? "block" : "hidden lg:block")}
        >
          {transcriptArea}
        </div>
      </div>

      <PlayerBar state={state} clock={clock} segments={segments} />

      {downloading && (
        <ExportDialog
          meeting={loaded}
          segments={segments}
          summary={summaryQuery.data}
          actionItems={actionItemsQuery.data ?? []}
          onClose={() => setDownloading(false)}
        />
      )}
      {editing && <EditMeetingModal meeting={loaded} onClose={() => setEditing(false)} />}
      {deleting && (
        <DeleteMeetingDialog
          meeting={loaded}
          onClose={() => setDeleting(false)}
          onDeleted={() => router.push("/meetings")}
        />
      )}
    </div>
  );
}
