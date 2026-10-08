"use client";

import { Download } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { cn } from "@/lib/colors";
import {
  exportFileName,
  notesToText,
  transcriptToText,
  type ExportContent,
  type ExportFormat,
} from "@/lib/export";
import type { ActionItem, MeetingDetail, Segment, Summary } from "@/lib/types";

function Choice<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}) {
  return (
    <fieldset>
      <legend className="mb-1.5 text-[13px] font-medium">{label}</legend>
      <div className="grid grid-cols-2 gap-1 rounded-xl bg-surface-muted p-1">
        {options.map((option) => (
          <label
            key={option.value}
            className={cn(
              "cursor-pointer rounded-lg py-2 text-center text-[13px] font-medium transition",
              value === option.value ? "bg-surface text-text shadow-sm" : "text-muted",
            )}
          >
            <input
              type="radio"
              className="sr-only"
              name={label}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function download(fileName: string, text: string, format: ExportFormat) {
  const type = format === "md" ? "text/markdown" : "text/plain";
  const url = URL.createObjectURL(new Blob([text], { type: `${type};charset=utf-8` }));
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
}

/** Bonus B2: Fireflies-style Download dialog, generated client-side from data already loaded. */
export function ExportDialog({
  meeting,
  segments,
  summary,
  actionItems,
  onClose,
}: {
  meeting: MeetingDetail;
  segments: Segment[];
  summary: Summary | undefined;
  actionItems: ActionItem[];
  onClose: () => void;
}) {
  const [content, setContent] = useState<ExportContent>(segments.length ? "transcript" : "notes");
  const [format, setFormat] = useState<ExportFormat>("txt");
  const [timestamps, setTimestamps] = useState(true);
  const [speakers, setSpeakers] = useState(true);

  const save = () => {
    const text =
      content === "transcript"
        ? transcriptToText(meeting, segments, { timestamps, speakers }, format)
        : notesToText(meeting, summary, actionItems, format);
    const fileName = exportFileName(meeting.title, content, format);
    download(fileName, text, format);
    toast.success("Download started", { description: fileName });
    onClose();
  };

  return (
    <Modal
      open
      onOpenChange={(open) => !open && onClose()}
      title="Download"
      description="Export this meeting as a text or Markdown file."
      size="sm"
      footer={
        <>
          <Button size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" size="sm" onClick={save}>
            <Download size={14} /> Download
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <Choice
          label="Content"
          value={content}
          onChange={setContent}
          options={[
            { value: "transcript", label: "Transcript" },
            { value: "notes", label: "AI notes" },
          ]}
        />
        <Choice
          label="Format"
          value={format}
          onChange={setFormat}
          options={[
            { value: "txt", label: "Text (.txt)" },
            { value: "md", label: "Markdown (.md)" },
          ]}
        />
        {content === "transcript" && (
          <div className="flex flex-col gap-2 text-[13px]">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={timestamps}
                onChange={(e) => setTimestamps(e.target.checked)}
                className="accent-[var(--primary)]"
              />
              Include timestamps
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={speakers}
                onChange={(e) => setSpeakers(e.target.checked)}
                className="accent-[var(--primary)]"
              />
              Include speaker names
            </label>
          </div>
        )}
      </div>
    </Modal>
  );
}
