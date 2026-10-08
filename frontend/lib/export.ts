// Bonus B2 — export a transcript or the notes as TXT or Markdown. Pure functions (unit tested);
// the dialog only turns their output into a file download.
import { formatDate, formatDuration, formatTimestamp } from "./format";
import type { ActionItem, MeetingDetail, Segment, Summary } from "./types";

export type ExportContent = "transcript" | "notes";
export type ExportFormat = "txt" | "md";

export interface TranscriptOptions {
  timestamps: boolean;
  speakers: boolean;
}

export function slugify(title: string): string {
  return (
    title
      .toLowerCase()
      .normalize("NFKD")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 60) || "meeting"
  );
}

export function exportFileName(
  title: string,
  content: ExportContent,
  format: ExportFormat,
): string {
  return `${slugify(title)}-${content}.${format}`;
}

function header(meeting: MeetingDetail, format: ExportFormat): string[] {
  const meta = [
    formatDate(meeting.meeting_date),
    formatDuration(meeting.duration_seconds),
    meeting.participants.map((p) => p.name).join(", "),
  ]
    .filter(Boolean)
    .join(" · ");
  return format === "md" ? [`# ${meeting.title}`, "", `_${meta}_`, ""] : [meeting.title, meta, ""];
}

export function transcriptToText(
  meeting: MeetingDetail,
  segments: Segment[],
  options: TranscriptOptions,
  format: ExportFormat,
): string {
  const lines = header(meeting, format);
  for (const segment of segments) {
    const time = options.timestamps ? `[${formatTimestamp(segment.start_ms)}] ` : "";
    const speaker = options.speakers
      ? format === "md"
        ? `**${segment.speaker.name}:** `
        : `${segment.speaker.name}: `
      : "";
    lines.push(`${time}${speaker}${segment.text}`);
    if (format === "md") lines.push("");
  }
  return lines.join("\n").trimEnd() + "\n";
}

export function notesToText(
  meeting: MeetingDetail,
  summary: Summary | undefined,
  actionItems: ActionItem[],
  format: ExportFormat,
): string {
  const md = format === "md";
  const heading = (title: string) => (md ? `## ${title}` : title.toUpperCase());
  const lines = header(meeting, format);

  if (summary) {
    if (summary.keywords.length) lines.push(heading("Keywords"), summary.keywords.join(", "), "");
    lines.push(heading("Overview"), summary.overview, "");
    if (summary.topics.length) {
      lines.push(heading("Outline"));
      for (const topic of summary.topics) {
        const time = topic.start_ms !== null ? `[${formatTimestamp(topic.start_ms)}] ` : "";
        lines.push(
          md
            ? `- **${time}${topic.title}** — ${topic.summary}`
            : `- ${time}${topic.title}: ${topic.summary}`,
        );
      }
      lines.push("");
    }
  } else {
    lines.push("(No AI notes for this meeting yet.)", "");
  }

  lines.push(heading("Action items"));
  if (actionItems.length === 0) lines.push("None.");
  for (const item of actionItems) {
    const box = md ? (item.completed ? "- [x] " : "- [ ] ") : item.completed ? "[done] " : "[ ] ";
    const who = item.assignee ? ` — ${item.assignee.name}` : "";
    const due = item.due_date ? ` (due ${item.due_date})` : "";
    lines.push(`${box}${item.title}${who}${due}`);
  }
  return lines.join("\n").trimEnd() + "\n";
}
