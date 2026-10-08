"use client";

import { AlertTriangle, FileText, ListTree, Loader2, RefreshCw, Sparkles, Tag } from "lucide-react";
import Link from "next/link";
import { memo, type ReactNode } from "react";
import { toast } from "sonner";

import { ActionItemsSection } from "@/components/action-items/ActionItemsSection";
import { Button } from "@/components/ui/Button";
import { Skeleton, errorMessage } from "@/components/ui/States";
import { PanelExpandButton } from "@/components/ui/PanelExpandButton";
import { StatusChip } from "@/components/ui/StatusChip";
import { useRegenerateSummary } from "@/hooks/queries";
import { cn, speakerColor } from "@/lib/colors";
import { formatTimestamp } from "@/lib/format";
import type { MeetingDetail, Summary } from "@/lib/types";

function Section({
  icon,
  title,
  children,
  aside,
}: {
  icon: ReactNode;
  title: string;
  children: ReactNode;
  aside?: ReactNode;
}) {
  return (
    <section className="border-b border-border px-5 py-4 last:border-b-0">
      <div className="mb-2.5 flex items-center gap-2">
        <span className="text-primary">{icon}</span>
        <h3 className="text-[13.5px] font-semibold">{title}</h3>
        <div className="ml-auto">{aside}</div>
      </div>
      {children}
    </section>
  );
}

function GeneratingNotes() {
  return (
    <div className="px-5 py-6" role="status" aria-live="polite">
      <div className="mb-4 flex items-center gap-2 text-[13px] font-medium text-primary">
        <Loader2 size={15} className="animate-spin" /> Lumen is reading the transcript and writing
        your notes…
      </div>
      <div className="space-y-2.5">
        <Skeleton className="h-3 w-11/12" />
        <Skeleton className="h-3 w-10/12" />
        <Skeleton className="h-3 w-8/12" />
        <Skeleton className="mt-5 h-3 w-1/3" />
        <Skeleton className="h-3 w-9/12" />
      </div>
    </div>
  );
}

function FailedNotes({ meeting }: { meeting: MeetingDetail }) {
  const regenerate = useRegenerateSummary(meeting.id);
  return (
    <div role="alert" className="m-5 rounded-xl border border-danger/20 bg-danger-soft p-4">
      <div className="flex items-center gap-2 text-[13.5px] font-semibold text-danger">
        <AlertTriangle size={16} /> Notes couldn’t be generated
      </div>
      <p className="mt-1 text-[13px] text-muted">
        {meeting.processing_error ?? "The AI service reported an error."}
      </p>
      <Button
        size="sm"
        className="mt-3"
        disabled={regenerate.isPending}
        onClick={() =>
          regenerate
            .mutateAsync()
            .then(() => toast.info("Regenerating notes…"))
            .catch((error) => toast.error("Couldn’t retry", { description: errorMessage(error) }))
        }
      >
        <RefreshCw size={14} className={regenerate.isPending ? "animate-spin" : undefined} /> Retry
      </Button>
    </div>
  );
}

function SummarySections({
  summary,
  activeTopic,
  onSeek,
}: {
  summary: Summary;
  activeTopic: number;
  onSeek: (ms: number) => void;
}) {
  return (
    <>
      {summary.keywords.length > 0 && (
        <Section icon={<Tag size={15} />} title="Keywords">
          <div className="flex flex-wrap gap-1.5">
            {summary.keywords.map((keyword) => (
              <Link
                key={keyword}
                href={`/meetings?keyword=${encodeURIComponent(keyword)}`}
                className="rounded-full border border-border bg-surface px-2.5 py-1 text-[12px] text-muted transition hover:border-primary/40 hover:text-primary"
              >
                {keyword}
              </Link>
            ))}
          </div>
        </Section>
      )}
      <Section icon={<FileText size={15} />} title="Overview">
        <p className="text-[13.5px] leading-relaxed text-text" data-testid="overview">
          {summary.overview}
        </p>
      </Section>
      {summary.topics.length > 0 && (
        <Section icon={<ListTree size={15} />} title="Outline">
          <ol className="space-y-1" aria-label="Outline">
            {summary.topics.map((topic, index) => (
              <li key={topic.sequence}>
                <button
                  type="button"
                  disabled={topic.start_ms === null}
                  onClick={() => topic.start_ms !== null && onSeek(topic.start_ms)}
                  className={cn(
                    "flex w-full gap-3 rounded-lg px-2 py-2 text-left transition-colors",
                    index === activeTopic ? "bg-primary-soft" : "hover:bg-surface-muted",
                  )}
                >
                  {topic.start_ms !== null && (
                    <span className="tabular mt-0.5 shrink-0 text-[11.5px] font-semibold text-primary">
                      {formatTimestamp(topic.start_ms)}
                    </span>
                  )}
                  <span>
                    <span className="block text-[13.5px] font-semibold">{topic.title}</span>
                    <span className="mt-0.5 block text-[13px] leading-relaxed text-muted">
                      {topic.summary}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ol>
        </Section>
      )}
    </>
  );
}

function TalkTime({ meeting }: { meeting: MeetingDetail }) {
  if (meeting.speaker_stats.length === 0) return null;
  return (
    <Section icon={<Sparkles size={15} />} title="Talk time">
      <ul className="space-y-2" aria-label="Talk time by speaker">
        {meeting.speaker_stats.map((stat) => (
          <li key={stat.participant_id} className="flex items-center gap-3 text-[12.5px]">
            <span className="w-32 truncate">{stat.name}</span>
            <span className="h-2 flex-1 overflow-hidden rounded-full bg-surface-muted">
              <span
                className="block h-full rounded-full"
                style={{
                  width: `${stat.percentage}%`,
                  backgroundColor: speakerColor(stat.participant_id),
                }}
              />
            </span>
            <span className="tabular w-10 text-right text-muted">
              {Math.round(stat.percentage)}%
            </span>
          </li>
        ))}
      </ul>
    </Section>
  );
}

export const NotesPanel = memo(function NotesPanel({
  meeting,
  summary,
  summaryLoading,
  activeTopic,
  onSeek,
  expanded,
  onToggleExpand,
}: {
  meeting: MeetingDetail;
  summary: Summary | undefined;
  summaryLoading: boolean;
  activeTopic: number;
  onSeek: (ms: number) => void;
  expanded: boolean;
  onToggleExpand: () => void;
}) {
  const status = meeting.processing_status;
  return (
    <div className="h-full overflow-y-auto">
      <div className="flex h-14 items-center gap-2 border-b border-border px-5">
        <Sparkles size={16} className="text-primary" />
        <h2 className="text-[14px] font-semibold">AI meeting notes</h2>
        <span className="ml-auto">
          <StatusChip status={status} />
        </span>
        <PanelExpandButton panel="notes" expanded={expanded} onToggle={onToggleExpand} />
      </div>

      {status === "pending" || status === "processing" ? (
        <GeneratingNotes />
      ) : status === "failed" ? (
        <FailedNotes meeting={meeting} />
      ) : status === "not_requested" ? (
        <p className="px-5 py-5 text-[13px] text-muted">
          Notes are generated from a transcript. This meeting doesn’t have one yet — you can still
          track action items below.
        </p>
      ) : summaryLoading ? (
        <div className="space-y-2.5 px-5 py-6">
          <Skeleton className="h-3 w-10/12" />
          <Skeleton className="h-3 w-9/12" />
        </div>
      ) : summary ? (
        <SummarySections summary={summary} activeTopic={activeTopic} onSeek={onSeek} />
      ) : null}

      <ActionItemsSection meeting={meeting} onSeek={onSeek} />
      <TalkTime meeting={meeting} />
    </div>
  );
});
